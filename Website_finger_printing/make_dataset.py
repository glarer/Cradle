import os
import numpy as np
import json

websites = []

def read_data(file_path):
    dict_data = {}
    data = []
    label = np.array([])
    for i in range(len(websites)):
        print(f"Read data from {websites[i]}") 
        file_name = file_path + websites[i] + "/"
        iters_num = os.listdir(file_name)
        if len(iters_num) < 100:
            print(f"Website {websites[i]} not enough data.")
            continue
        dict_data[i] = websites[i]
        for j in range(0, 100):
            iter_file_name = file_name + str(j) + ".txt"
            if not os.path.exists(iter_file_name):
                print(f"File {iter_file_name} not exists")
                continue
            with open(iter_file_name, 'rb') as f:
                iter_data = np.fromfile(f, dtype=np.uint64)

            for k in range(len(iter_data) - 1, 0, -1):
                iter_data[k] = iter_data[k] - iter_data[k - 1]
            iter_data = np.append(iter_data[1:], iter_data[-1])
            
            total_len = len(iter_data)
            sqz_len = int(total_len/2)
            ## Squeeze the data to 1/2
            iter_data = iter_data.reshape(sqz_len, 2)
            average_arr = np.mean(iter_data, axis=1)
            average_arr = average_arr.astype(np.uint64)
            average_arr = average_arr.reshape(sqz_len)

            data.append(average_arr)
            label = np.append(label, i)
        print(f"{websites[i]} done.")

    data = np.array(data)
    np.save('dataset_96c_100r/data.npy', data)
    np.save('dataset_96c_100r/label.npy', label)
    with open('dataset_96c_100r/label_dict.json', 'w') as file:
        json.dump(dict_data, file)
    print(f"Data shape: {data.shape}")
    print(f"Label length: {label.shape}")

if __name__ == '__main__':
    try:
        with open("websites.txt", "r") as f:
            for lines in f:
                websites.append(lines.strip())
    except FileNotFoundError:
        print("Read error")
    print(websites)
    
    # for i in range(len(websites)):
    #     dict_data[websites[i]] = i
    # print(dict_data)
    # with open('label_dict.json', 'w') as file:
    #     json.dump(dict_data, file)

    # with open('label_dict.json', 'r') as fd:
    #     label_dict = json.load(fd)
    # print(label_dict)
    
    read_data("logs/")