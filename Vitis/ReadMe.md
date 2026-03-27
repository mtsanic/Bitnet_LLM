# Vitis Bare-Metal Verification

This folder contains the bare-metal C application deployed to the ARM Cortex-A9 processor to feed data to the physical FPGA fabric and benchmark its performance.

## Hardware-in-the-Loop Methodology
Because the Zynq environment lacks a file system, the 100 Python test cases are baked directly into the application memory via a generated `test_data.h` header. The software executes the following loop:
1. Converts floating-point inputs to 16-bit fixed-point.
2. Packs two 16-bit inputs into a 32-bit word and writes to the AXI address (`0x080`).
3. Triggers the IP start bit (`0x000`).
4. Polls the done bit.
5. Reads the 32-bit outputs (`0x100`), un-scales them back to floats, and calculates the absolute error.

## Bypassing SDT Timer Issues
To ensure pinpoint latency measurement and avoid known initialization bugs in the Vitis 2024.1 System Device Tree (SDT) timer libraries, the application directly commands the Zynq Global Timer registers:
* `0xF8F00208`: Global Timer Control (forces the timer on).
* `0xF8F00200`: Lower 32-bit counter (read exactly before and after IP execution).

## Execution
Connect the physical board via UART (115200 baud) and JTAG. Bypassing the auto-generated `ps7_init` script in the launch configuration may be required depending on your Vitis version. The terminal will output the MAE and physical microsecond latency for all 100 samples.