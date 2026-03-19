# BitNet 1.58b FPGA Accelerator: Vitis HLS Synthesis



## Overview
This directory documents the High-Level Synthesis (HLS) phase of the pipeline. In this stage, the auto-generated C++ code from `hls4ml` is ingested by **Vitis HLS 2024.1**, verified via C-Simulation, synthesized into raw RTL (Verilog), and packaged into a Vivado-ready IP block.

This stage bridges the gap between software math and physical silicon logic gates.

## Architectural Optimization: The Data-Driven Core
By default, `hls4ml` generates IP with a standard AXI-Lite control interface (`ap_ctrl`). For a pure streaming neural network, this creates unnecessary overhead where the ARM CPU must manually start the IP for every single inference.

We refactored the architecture by explicitly injecting:
```cpp
#pragma HLS INTERFACE ap_ctrl_none port=return
```
**Why this matters:**
* **Zero CPU Overhead:** The IP is converted into a free-running, purely data-driven processor.
* **Hardware Handshaking:** It relies entirely on the AXI4-Stream `TVALID` and `TREADY` physical pins to know when to compute.
* **LUT Savings:** Strips out the internal state machine (`ap_start`, `ap_done`, `ap_idle`), saving physical logic units on the Zynq-7000 fabric.



## Toolchain Bug Fixes (Vitis HLS 2024.1)
When bridging open-source compilers (`hls4ml`) with strict proprietary toolchains (Vitis 2024.1), several known clashes occur. Here is how we patched them for a clean build:

### 1. The Clang Code Analyzer Crash
* **The Bug:** The new aggressive Clang-based Code Analyzer in 2024.1 panics and crashes when parsing `hls4ml`'s heavily templated macros (e.g., `nnet::convert_data`).
* **The Fix:** Disabled the strict analyzer in `hls_config.cfg` to force Vitis to use the classic, stable GCC compiler for simulation:
  ```ini
  csim.code_analyzer=0
  ```

### 2. Duplicate Symbol Linker Error
* **The Bug:** `hls4ml` generates two test files (`bitnet_test.cpp` and a Python wrapper `bitnet_bridge.cpp`) that define the exact same global debugging variables. The strict Clang linker throws a fatal `duplicate symbol` error during compilation.
* **The Fix:** Removed `bitnet_bridge.cpp` from the standalone C-Simulation project. The bridge is only needed if simulating from inside Python via CFFI, which is unnecessary for bare-metal FPGA deployment.

### 3. Execution Sandbox Missing Weights
* **The Bug:** Vitis HLS creates an isolated sandbox directory to execute the C-Simulation but fails to automatically copy the binary weight `.txt` files, causing a `File Not Found` runtime crash.
* **The Fix:** Explicitly mapped the target data folders in `hls_config.cfg` to force the tool to copy them into the sandbox:
  ```ini
  tb.file=./firmware/weights
  tb.file=./tb_data
  ```

## Usage & Synthesis
Once the configuration is patched, the workflow is standard:

1. **Run C-Simulation:** Verifies the C++ ternary math perfectly matches the Python PyTorch model.
2. **Run C-Synthesis:** Translates the code into Verilog. *(Verify DSP48E utilization is 0, proving the MatMul-free design worked).*
3. **Export RTL:** Packages the design as `Vivado IP for IP Catalog`.

**Output:** A packaged `.zip` file inside `solution1/impl/ip/`, ready to be imported into Vivado IP Integrator.