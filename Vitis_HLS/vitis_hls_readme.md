# Vitis HLS Hardware Synthesis

This folder contains the C++ source code that defines the custom BitNet IP and the testbench used to verify its logic before generating RTL.



## Hardware Architecture
The accelerator is designed with specific pragmas to optimize for the Zynq architecture:
* **Zero-DSP Math:** By leveraging the ternary nature of BitNet, multiplications are replaced entirely with conditional addition/subtraction (`if w == 1...`), utilizing FPGA LUTs instead of DSP slices.
* **Fixed-Point Precision:** Inputs use `ap_fixed<16,6>` and internal accumulators use `ap_fixed<32,12>` to maintain precision without floating-point overhead.
* **AXI4-Lite Interfaces:** All arrays and control signals are mapped to `s_axilite` pragmas. 
* **Memory Packing:** To maximize bus efficiency, two 16-bit inputs are packed into a single 32-bit AXI memory word.

## Files
* `bitnet.cpp`: The core hardware IP.
* `bitnet.h`: Data types and interface definitions.
* `bitnet_tb.cpp`: C-simulation testbench evaluating the IP against the Python golden dataset.

## Flow
1. Run **C Simulation** to verify the 0.0016 MAE.
2. Run **C Synthesis** to generate the Verilog/VHDL RTL.
3. **Export RTL** as a standard Vivado IP ZIP file.
