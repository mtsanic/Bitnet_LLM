# BitNet 1.58b FPGA Accelerator: Python Toolchain

## Overview
This directory contains the Python-based front-end toolchain for designing, quantizing, and exporting a ternary (1.58-bit) MatMul-free Large Language Model (LLM) block for FPGA deployment.

The pipeline leverages PyTorch and Brevitas for Quantization-Aware Training (QAT), and hls4ml to translate the quantized ONNX graph into synthesizable C++ for Xilinx/AMD Vitis HLS.

## Architecture Highlights
* **Ternary Weights:** The network utilizes weights constrained to {-1, 0, 1}, completely eliminating traditional DSP-heavy floating-point MAC (Multiply-Accumulate) operations in favor of purely additive integer trees.
* **Hardware-Aware Clamping:** The export script strictly clamps the internal precision of all layers to `ap_fixed<16,6>`. This physically constrains the AXI4-Stream bus width to 2048 bits (128 features × 16 bits), safely bypassing the Vivado 4096-bit physical interface limit.
* **Data-Driven Streaming:** The generated HLS core is configured for `io_stream` to allow continuous, cycle-accurate throughput.

## Dependencies
Ensure you have the following packages installed in your Python environment:

```bash
pip install torch torchvision
pip install brevitas
pip install qonnx
pip install hls4ml
```

## Core Scripts

### 1. `bitnet.py` (Model Definition & Training)
Defines the `QuantBitNetBlock` architecture.
* Constructs the ternary linear layers using Brevitas quantization primitives.
* Handles the training loop or loads pre-trained weights.
* **Outputs:** `trained_bitnet.pth` (PyTorch State Dictionary).

### 2. `export_hls.py` (The HLS Bridge)
This is the critical bridge between the software model and the physical silicon blueprint.
* **QONNX Export:** Loads the `.pth` file and exports the strictly quantized graph to an intermediate ONNX format.
* **Graph Cleanup:** Runs constant folding and shape inference via the `qonnx` optimizer to strip software overhead.
* **hls4ml Configuration:** * Target Part: `xc7z010clg400-1` (Zynq-7000).
  * Strategy: Resource (optimizes for LUT utilization over massive parallelization).
  * Reuse Factor: 4.
  * Precision Override: Forces 16-bit accumulators to prevent AXI-Stream bus overflow.
* **Outputs:** A complete, ready-to-synthesize Vitis HLS 2024.1 project in the `bitnet_hls_workspace/` directory.

## Usage

**Step 1:** Train or instantiate the model to generate the weights.

```bash
python bitnet.py
```

**Step 2:** Run the hardware export script to generate the Vitis HLS C++ workspace.

```bash
python export_hls.py
```

Upon successful execution, the `bitnet_hls_workspace/` folder will contain `bitnet.cpp`, the weights headers, and the Tcl scripts necessary to synthesize the IP block.