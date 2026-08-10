### Before start:
1. Set power-manager to Intel_pstate:
   `vim /etc/default/grub`
   Add 'intel_pstate=passive' to 'GRUB_CMDLINE_LINUX_DEFAULT'.
2. Set scaling mode to performance
    1. `echo "active" | sudo tee /sys/devices/system/cpu/intel_pstate/status`
    2. `echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
3. (Optional) Fix the maximum frequency of each core.
    1. `MAX_FREQ=$(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq)`

	2. `echo $MAX_FREQ | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq`

	3. `echo $MAX_FREQ | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq`
---
### Sender:
1. Calibrate the transmission window size in code: `p_loop_calibration` and `e_loop_calibration`, or at the running phase.
2. Start the sender: 
   * `./sender [xxx]` [xxx] is the file contains the binary bits.
---
### Receiver:
* `./receiver [xxx]` [xxx] is the sampling time window, e.g., 0.01 means sample every 0.01 ms.
* Attention: better to set the sampling rate to be 100x of the sender frequency, e.g.: sender frequency 1000 Hz (1ms), then set the sampling rate to 100000 Hz (0.01 ms)