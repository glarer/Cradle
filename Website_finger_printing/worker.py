import subprocess
from multiprocessing import Process
import os
import time

def run_program_a(args):
    try:
        print(f"Run the receiver, args: {args[1:]}")
        result = subprocess.run(
            args,
            check=True,
            text=True,
            stdout=None,
            stderr=None
        )
        # print(f"Receiver outputs:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Run receiver error: \n{e.stderr}")

def run_program_b(args):
    try:
        print(f"Run the chrome, args: {args[1:]}")
        result = subprocess.run(
            args,
            check=True,
            text=True,
            stdout=None,
            stderr=None
        )
        # print(f"Chrome outputs:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Chrome error:\n{e.stderr}")

if __name__ == "__main__":
    websites = []
    try:
        with open("websites.txt", "r") as f:
            for lines in f:
                websites.append(lines.strip())
    except FileNotFoundError:
        print("Read error")

    print(websites)
    print(len(websites))
    
    for i in range(len(websites)):
        print("Here we at " + websites[i])
        os.system("mkdir logs/"+ websites[i])
        for j in range(0, 100):
            program_a = [
                "taskset",
                "-c", "14,16",
                "./receiver",
                "0.05",
                websites[i],
                str(j)
            ]

            program_b = [
                "google-chrome",
                "--headless",
                "--new-window",
                "--incognito",
                "--disable-application-cache",
                "--disable-dbus",
                "--disable-gpu",
                "--no-sandbox",
                "--timeout=1000",
                "--virtual-time-budget=1000",
                websites[i]
            ]

            p1 = Process(target=run_program_a, args=(program_a,))
            p2 = Process(target=run_program_b, args=(program_b,))

            p1.start()
            time.sleep(0.2)
            p2.start()

            p2.join()
            p1.join()
            p1.terminate()
            p2.terminate()
        time.sleep(0.7)
        print(websites[i] + " is done\n\n")