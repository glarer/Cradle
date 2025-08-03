target: receiver_c sender

receiver_c: receiver.c
	gcc -o receiver receiver.c

sender: sender.c
	gcc -o sender sender.c -lm -lpthread

.PHONY: clean
clean:
	rm -f receiver sender