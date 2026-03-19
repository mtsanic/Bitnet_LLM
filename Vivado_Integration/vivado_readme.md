# BitNet 1.58b FPGA Accelerator



## Overview
This repository contains a complete, edge-to-edge hardware/software co-design pipeline for training, quantizing, and deploying a **MatMul-free Large Language Model (BitNet 1.58b)** onto Xilinx/AMD Zynq-7000 Series FPGAs.

By constraining network weights to ternary values `{-1, 0, 1}`, this architecture completely eliminates the need for DSP-heavy floating-point multiply-accumulate (MAC) operations. Instead, it relies on highly efficient, purely additive integer trees, allowing for massive parallelization and low-power inference on edge silicon.

This project bridges the gap between high-level AI frameworks and bare-metal physical hardware routing.

## Technology Stack
* **Machine Learning:** Python, PyTorch, Brevitas (Quantization-Aware Training)
* **High-Level Synthesis:** `hls4ml`, `qonnx`
* **Hardware Engineering:** AMD/Xilinx Vitis HLS 2024.1, Vivado 2024.1
* **Embedded Software:** Vitis Unified IDE 2024.1, Bare-Metal C (ARM Cortex-A9)

## Project Structure & Pipeline

This repository is divided into four chronological engineering phases. Click into each folder for detailed documentation, toolchain bypasses, and usage instructions.

### 📁 [Phase 1: Python Toolchain & Export](./Python_Scripts/)
The software front-end. Defines the PyTorch architecture, executes 1.58-bit Quantization-Aware Training (QAT), and utilizes `hls4ml` to export a rigidly clamped, hardware-aware C++ representation of the ONNX graph.

### 📁 [Phase 2: Vitis HLS Synthesis](./Vitis_HLS/)
The bridge from math to silicon. Ingests the auto-generated C++ and synthesizes it into raw RTL. This phase documents our architectural upgrade to a purely data-driven, `ap_ctrl_none` streaming core to eliminate ARM CPU overhead.

### 📁 [Phase 3: Vivado Hardware Integration](./Vivado_Integration/)
The motherboard assembly. Contains the Tcl automation scripts to instantiate the Zynq Processing System, route the 1024-bit AXI Direct Memory Access (DMA) engine, and resolve strict AXI4-Stream protocol mismatches (like `TLAST` injection) to perfectly integrate the `mts:hls:BitNet_LLM:1.0` IP.

### 📁 [Phase 4: Bare-Metal Firmware](./Vitis_Firmware/)
The software execution layer. Contains the bare-metal C drivers running on the Zynq ARM Cortex-A9. This code manages DDR memory cache coherence and triggers the DMA to blast tokens through the physical AI accelerator at maximum throughput.

## Getting Started
To replicate this build, please navigate to **Phase 1** and follow the sequential pipeline. You will need a standard Python environment and an installation of the AMD/Xilinx 2024.1 Unified Design Suite.