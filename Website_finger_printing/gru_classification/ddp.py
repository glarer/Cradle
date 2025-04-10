import os
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributed as dist
from torch.utils.data import DataLoader, TensorDataset, random_split
from torch.utils.data.distributed import DistributedSampler
import numpy as np
from sklearn.preprocessing import StandardScaler
from Website_finger_printing.gru_classification.gru_model import GRUClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
import logging
import json

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s', 
                    handlers=[
                        logging.FileHandler("output.log"),
                        logging.StreamHandler()
                    ])

def main():
    dist.init_process_group(backend='nccl')
    local_rank = int(os.environ['LOCAL_RANK'])
    torch.cuda.set_device(local_rank)
    device = torch.device('cuda', local_rank)

    WEBSITE_NUM = 96
    ACCESS_NUM = 100

    data_path = '../data/dataset_%dc_%dr/data.npy' % (WEBSITE_NUM, ACCESS_NUM)
    label_path = '../data/dataset_%dc_%dr/label.npy' % (WEBSITE_NUM, ACCESS_NUM)
    id_to_name_path = '../data/dataset_%dc_%dr/label_dict.json' % (WEBSITE_NUM, ACCESS_NUM)
    
    with open(id_to_name_path, 'r') as f:
        id_to_name = json.load(f)

    values_view = id_to_name.values()
    target_names = list(values_view)

    X = np.load(data_path)
    y = np.load(label_path)

    num_classes = len(np.unique(y))
    print("class num:", num_classes)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_tensor = torch.from_numpy(X).float()
    y_tensor = torch.from_numpy(y).long()
    dataset = TensorDataset(X_tensor, y_tensor)

    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(dataset, [train_size, test_size])

    train_sampler = DistributedSampler(train_dataset)
    test_sampler = DistributedSampler(test_dataset)

    batch_size = 176
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False, sampler=train_sampler)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, sampler=test_sampler)

    input_size = 1
    embedding_dim = 16      # 16
    hidden_size = 256       # 384
    num_layers = 2
    num_classes = 96

    model = GRUClassifier(input_size, hidden_size, num_layers, num_classes)

    model = model.to(device)

    model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank], output_device=local_rank)


    criterion = nn.CrossEntropyLoss().to(device)
    optimizer1 = optim.Adam(model.parameters(), lr=0.001)
    # optimizer2 = optim.SGD(model.parameters(), lr=0.0002)
    optimizer2 = optim.SGD(model.parameters(), lr=0.0004, momentum=0.9, weight_decay=1e-4)
    optimizer = optimizer1

    num_epochs = 500
    for epoch in range(num_epochs):
        model.train()
        train_sampler.set_epoch(epoch)
        running_loss = 0.0
        correct_top1 = 0
        correct_top3 = 0
        total = 0

        all_preds_top1 = []
        all_preds_top3 = []
        all_labels = []

        for i, (inputs, labels) in enumerate(train_loader):
            inputs = inputs.unsqueeze(-1).to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item()

            _, predicted_top1 = torch.max(outputs, 1)  # Top-1
            _, predicted_top3 = torch.topk(outputs, 3, dim=1)  # Top-3

            total += labels.size(0)
            correct_top1 += (predicted_top1 == labels).sum().item()

            correct_top3 += sum([1 if labels[i].item() in predicted_top3[i] else 0 for i in range(labels.size(0))])

            all_preds_top1.extend(predicted_top1.cpu().numpy())
            all_preds_top3.extend([predicted_top3[i].cpu().numpy() for i in range(labels.size(0))])
            all_labels.extend(labels.cpu().numpy())

        total_correct_top1 = torch.tensor(correct_top1).to(device)
        total_correct_top3 = torch.tensor(correct_top3).to(device)
        total_samples = torch.tensor(total).to(device)
        dist.all_reduce(total_correct_top1, op=dist.ReduceOp.SUM)
        dist.all_reduce(total_correct_top3, op=dist.ReduceOp.SUM)
        dist.all_reduce(total_samples, op=dist.ReduceOp.SUM)

        acc_top1 = 100 * total_correct_top1.item() / total_samples.item()
        acc_top3 = 100 * total_correct_top3.item() / total_samples.item()

        f1_top1 = f1_score(all_labels, all_preds_top1, average='macro')
        precision_top1 = precision_score(all_labels, all_preds_top1, average='macro',zero_division=0)
        recall_top1 = recall_score(all_labels, all_preds_top1, average='macro',zero_division=0)

        # Top - 3
        all_preds_top3_flat = []
        for i in range(len(all_preds_top3)):
            if all_labels[i] in all_preds_top3[i]:
                all_preds_top3_flat.append(all_labels[i])
            else:
                all_preds_top3_flat.append(all_preds_top3[i][0])

        f1_top3 = f1_score(all_labels, all_preds_top3_flat, average='macro')
        precision_top3 = precision_score(all_labels, all_preds_top3_flat, average='macro', zero_division=0)
        recall_top3 = recall_score(all_labels, all_preds_top3_flat, average='macro',zero_division=0)

        if local_rank == 0:
            logging.info(f'== Epoch [{epoch+1}/{num_epochs}], Loss: {running_loss:.4f} ==')
            logging.info(f'Top-1 Accuracy: **{acc_top1:.2f}%**, Top-3 Accuracy: {acc_top3:.2f}%')
            logging.info(f'Top-1 F1 Score: {f1_top1:.4f}, Precision: {precision_top1:.4f}, Recall: {recall_top1:.4f}')
            logging.info(f'Top-3 F1 Score: {f1_top3:.4f}, Precision: {precision_top3:.4f}, Recall: {recall_top3:.4f}')

        if dist.get_rank() == 0 and acc_top1 > 55:
            torch.save(model.state_dict(), 'models/model_{:.7f}.pth'.format(acc_top1))
    
    model.eval()
    with torch.no_grad():
        test_sampler.set_epoch(0)
        correct_top1 = 0
        correct_top3 = 0
        total = 0

        all_preds_top1 = []
        all_preds_top3 = []
        all_labels = []

        for inputs, labels in test_loader:
            inputs = inputs.unsqueeze(-1).to(device)
            labels = labels.to(device)

            outputs = model(inputs)

            _, predicted_top1 = torch.max(outputs, 1)  # Top-1
            _, predicted_top3 = torch.topk(outputs, 3, dim=1)  # Top-3

            total += labels.size(0)
            correct_top1 += (predicted_top1 == labels).sum().item()

            correct_top3 += sum([1 if labels[i].item() in predicted_top3[i] else 0 for i in range(labels.size(0))])

            all_preds_top1.extend(predicted_top1.cpu().numpy())
            all_preds_top3.extend([predicted_top3[i].cpu().numpy() for i in range(labels.size(0))])
            all_labels.extend(labels.cpu().numpy())

        total_correct_top1 = torch.tensor(correct_top1).to(device)
        total_correct_top3 = torch.tensor(correct_top3).to(device)
        total_samples = torch.tensor(total).to(device)
        dist.all_reduce(total_correct_top1, op=dist.ReduceOp.SUM)
        dist.all_reduce(total_correct_top3, op=dist.ReduceOp.SUM)
        dist.all_reduce(total_samples, op=dist.ReduceOp.SUM)

        acc_top1 = 100 * total_correct_top1.item() / total_samples.item()
        acc_top3 = 100 * total_correct_top3.item() / total_samples.item()

        f1_top1 = f1_score(all_labels, all_preds_top1, average='macro')
        precision_top1 = precision_score(all_labels, all_preds_top1, average='macro', zero_division=0)
        recall_top1 = recall_score(all_labels, all_preds_top1, average='macro',zero_division=0)

        all_preds_top3_flat = []
        for i in range(len(all_preds_top3)):
            if all_labels[i] in all_preds_top3[i]:
                all_preds_top3_flat.append(all_labels[i])
            else:
                all_preds_top3_flat.append(all_preds_top3[i][0])

        f1_top3 = f1_score(all_labels, all_preds_top3_flat, average='macro')
        precision_top3 = precision_score(all_labels, all_preds_top3_flat, average='macro', zero_division=0)
        recall_top3 = recall_score(all_labels, all_preds_top3_flat, average='macro',zero_division=0)

        
        if local_rank == 0:
            logging.info('\nValidation: \n')
            logging.info(f'Test Accuracy (Top-1): {acc_top1:.2f}%')
            logging.info(f'Test Accuracy (Top-3): {acc_top3:.2f}%')
            logging.info(f'Test F1 Score (Top-1): {f1_top1:.4f}, Precision (Top-1): {precision_top1:.4f}, Recall (Top-1): {recall_top1:.4f}')
            logging.info(f'Test F1 Score (Top-3): {f1_top3:.4f}, Precision (Top-3): {precision_top3:.4f}, Recall (Top-3): {recall_top3:.4f}')
            logging.info(classification_report(all_labels, all_preds_top1, target_names=target_names, digits=4))

    dist.destroy_process_group()


# distributed training
# torchrun --nproc_per_node=[xxx] ddp.py
if __name__ == '__main__':
    main()