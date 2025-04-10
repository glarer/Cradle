import torch
import torch.nn as nn

class GRUClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(GRUClassifier, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.fc_input = nn.Linear(input_size, hidden_size)

        self.gru = nn.GRU(hidden_size, hidden_size, num_layers, batch_first=True)

        self.attention = nn.Linear(hidden_size, 1)  

        self.fc1 = nn.Linear(hidden_size, 256)      #       256 -> 192 -> 100
        self.fc2 = nn.Linear(256, 192)  
        self.fc3 = nn.Linear(192, num_classes)

        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.fc_input(x)

        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.gru(x, h0)  # out: (batch_size, seq_length, hidden_size)

        attn_weights = torch.tanh(self.attention(out))  # (batch_size, seq_length, 1)
        attn_weights = torch.softmax(attn_weights, dim=1) 
        
        context = torch.sum(attn_weights * out, dim=1)  # (batch_size, hidden_size)

        out = self.fc1(context)  # (batch_size, 256)
        out = self.relu(out)    
        out = self.fc2(out)       # (batch_size, 192)
        out = self.relu(out) 
        out = self.fc3(out)       # (batch_size, num_classes)
        
        return out
