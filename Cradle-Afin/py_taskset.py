#!/usr/bin/env python3
import sys
import subprocess
import time
import rdtsc
from math import ceil

if len(sys.argv) != 3:
    print("Usage: python3 taskset.py [program_args(dot after x ms)] [bandwidth(bps)]")  # 1000 bandwidth means, 
    sys.exit(1)

program = "./receiver"
program_args = sys.argv[1]

bandwidth = float(sys.argv[2])
sleep_interval = 1 / bandwidth
print(f"Sleep interval: {sleep_interval}")

CORE1 = 14
CORE2 = 16

print(f"Run the program.. {program} {program_args}")
process = subprocess.Popen(
    ["taskset", "-c", str(CORE1), program, program_args],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

if process.poll() is not None:  
    print(f"Error, {program} failed to start.")
    sys.exit(1)

PID = process.pid
print(f"PID: {PID}")

send_seq = [0,1,1,1,0,1,1,1,0,0] # 0 p 1 e

time.sleep(0.3)
tsc_value_st = rdtsc.rdtsc()
for i in send_seq:
    if(i == 0):
        subprocess.run(["taskset", "-pc", str(CORE1), str(PID)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["taskset", "-pc", str(CORE2), str(PID)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(sleep_interval)

tsc_value_ed = rdtsc.rdtsc()
print("Time stamp start and end:")
print(tsc_value_st, tsc_value_ed)

'''
MAX_SWITCHES = 500
switch_count = 0
time.sleep(0.3)


tsc_value_st = rdtsc.rdtsc()
while switch_count < MAX_SWITCHES:
    # try:
    #     if process.poll() is not None:
    #         print("Process terminated unexpectedly.")
    #         break
    subprocess.run(["taskset", "-pc", str(CORE2), str(PID)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(sleep_interval)

    subprocess.run(["taskset", "-pc", str(CORE1), str(PID)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(sleep_interval)

    switch_count += 1
    # except KeyboardInterrupt:
    #     print("Interrupted by user.")
    #     break


tsc_value_ed = rdtsc.rdtsc()
print("Time stamp start and end")
print(tsc_value_st, tsc_value_ed)
print(f"Switched {switch_count} times.")
'''