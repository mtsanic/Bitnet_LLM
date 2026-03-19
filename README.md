# Bitnet_LLM
A BitNet LLM integration on Xilinx Zynq 7000 Series Development Board AX7010

## 🐍 Phase 1: Python Toolchain (Model & HLS Export)

The journey from abstract AI model to physical silicon begins in the `Python_Scripts/` directory. This module handles the Quantization-Aware Training (QAT) of our MatMul-free network and its translation into synthesizable hardware.

**Key operations in this stage:**
* **1.58-bit Quantization:** Leverages PyTorch and Brevitas to train a network using exclusively ternary weights `{-1, 0, 1}`.
* **Graph Optimization:** Exports and sanitizes the model via QONNX.
* **Silicon Generation:** Utilizes `hls4ml` to translate the Python graph into a cycle-accurate, data-driven Vitis HLS C++ IP block, perfectly clamped to fit the Zynq-7000 AXI4-Stream bus limits.

📁 **[Read the full Python Toolchain documentation and usage instructions here](./Python_Scripts/)**


## ⚙️ Phase 2: Vitis HLS (C++ to Silicon RTL)



Once the Python toolchain generates the heavily optimized C++ workspace, this phase focuses on synthesizing that high-level code into physical hardware logic using Vitis HLS 2024.1.

**Key operations in this stage:**
* **RTL Synthesis:** Translating the ternary MatMul-free adder trees into raw, highly optimized Verilog/VHDL.
* **Data-Driven Architecture Optimization:** By injecting `#pragma HLS INTERFACE ap_ctrl_none`, we intentionally stripped out the AXI-Lite control state machine (`ap_start`, `ap_done`). This converts the IP into a pure, free-running AXI4-Stream processor, saving physical LUTs and eliminating ARM CPU overhead.
* **IP Packaging:** Exporting the final synthesized hardware as a standalone Vivado IP block (`.zip`), specifically tailored for the `xc7z010clg400-1` fabric.

📁 **[Read the full Vitis HLS synthesis guide and toolchain workarounds here](./Vitis_HLS/)**

## 🏗️ Phase 3: Vivado Hardware Integration



With the standalone silicon synthesized, this phase covers the physical hardware assembly within Vivado 2024.1. This is where we build the System-on-Chip (SoC) architecture, wiring the AI accelerator to the ARM Cortex-A9 processor via Direct Memory Access (DMA).

**Key operations in this stage:**
* **Data-Driven Routing:** Integrating the custom `mts:hls:BitNet_LLM:1.0` IP. Because we stripped the control registers (`ap_ctrl_none`), the ARM processor never micromanages the IP; it only talks to the DMA.
* **Protocol Bridging (TLAST Injection):** Resolving strict AXI4-Stream protocol mismatches by inserting a Xilinx Subset Converter to forcefully inject packet boundary (`TLAST`) signals, preventing DMA lockups.
* **Bus Width Balancing:** Expanding the AXI Interconnects to handle the massive 1024-bit physical data bus required to move all 64 feature tokens in a single clock cycle.
* **Tcl Automation:** The entire motherboard assembly—from IP instantiation to system clock routing—is fully automated via a deterministic Tcl script for perfect reproducibility.

📁 **[Read the full Vivado integration guide and hardware routing fixes here](./Vivado_Integration/)**
