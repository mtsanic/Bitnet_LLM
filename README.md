# BitNet 1.58b FPGA Accelerator

This repository contains a full-stack, hardware-in-the-loop implementation of a 1.58b (ternary) BitNet neural network layer mapped to physical silicon. It demonstrates how to transition a quantized PyTorch model into a custom, zero-DSP hardware accelerator using High-Level Synthesis (HLS) and deploy it on a Zynq-7000 SoC.

Built to support research in ultra-low-latency edge AI, such as real-time reinforcement learning for UAV-to-UAV mmWave communication networks, this architecture prioritizes deterministic execution speed and efficient logic utilization.



## Key Physical Silicon Results
* **Target Hardware:** Zynq XC7Z010 (xc7z010clg400-1)
* **Clock Speed:** 100 MHz (Shared PS-PL AXI boundary)
* **Execution Latency:** ~1.6 microseconds (measured via raw ARM Cortex-A9 hardware timer ticks)
* **Mathematical Accuracy:** 0.0016 Mean Absolute Error (MAE) compared to PyTorch golden baseline.
* **Architecture Highlights:** Zero-DSP utilization, entirely combinatorial ternary math (`{-1, 0, 1}`), and 16-bit AXI memory packing.

## Repository Structure
The project is divided into four main stages, tracking the standard FPGA ML deployment pipeline:

1. **`Python_Script/`**: PyTorch quantization, golden test data generation, and scale factor extraction.
2. **`Vitis_HLS/`**: C++ hardware description, testbench simulation, and RTL synthesis.
3. **`Vivado/`**: Block design, Zynq Processing System (PS) integration, and bitstream generation.
4. **`Vitis/`**: Bare-metal C application for physical hardware-in-the-loop verification.

Refer to the individual `README.md` inside each folder for step-by-step instructions.
