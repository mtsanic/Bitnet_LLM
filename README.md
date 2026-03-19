# Bitnet_LLM
A BitNet LLM integration on Xilinx Zynq 7000 Series Development Board AX7010

## 🐍 Phase 1: Python Toolchain (Model & HLS Export)

The journey from abstract AI model to physical silicon begins in the `Python_Scripts/` directory. This module handles the Quantization-Aware Training (QAT) of our MatMul-free network and its translation into synthesizable hardware.

**Key operations in this stage:**
* **1.58-bit Quantization:** Leverages PyTorch and Brevitas to train a network using exclusively ternary weights `{-1, 0, 1}`.
* **Graph Optimization:** Exports and sanitizes the model via QONNX.
* **Silicon Generation:** Utilizes `hls4ml` to translate the Python graph into a cycle-accurate, data-driven Vitis HLS C++ IP block, perfectly clamped to fit the Zynq-7000 AXI4-Stream bus limits.

📁 **[Read the full Python Toolchain documentation and usage instructions here](./Python_Scripts/)**
