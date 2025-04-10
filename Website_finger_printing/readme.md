## Before start:
1. Compile the receiver by gcc. `gcc -o receiver receiver.c`
2. Run the `worker.py` to perform the experiment.
3. Run `make_dataset.py` to make dataset.
4. In gru_classification, run `torchrun --nproc_per_node=[xxxxx ] ddp.py` to train the model and see the results.