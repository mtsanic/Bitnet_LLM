# BitNet 1.58b FPGA Accelerator: Vivado Hardware Integration



## Overview
This phase covers the physical hardware assembly within **Vivado 2024.1**. In this stage, the custom BitNet IP (synthesized in Phase 2) is imported into Vivado IP Integrator and wired to the Zynq-7000 Processing System (ARM Cortex-A9) using an AXI Direct Memory Access (DMA) engine. 

The result is a complete, bitstream-ready System-on-Chip (SoC) architecture where the ARM processor can push tokens directly from DDR memory into the AI silicon at maximum throughput.

## System Architecture: The Data-Driven Pipeline
Because the BitNet IP was synthesized with `#pragma HLS INTERFACE ap_ctrl_none`, it acts as a pure, free-running stream processor. 
1. **The CPU** prepares the token data in DDR memory and commands the DMA.
2. **The DMA (MM2S)** blasts the 1024-bit token across the AXI-Stream fabric.
3. **The BitNet IP** automatically wakes up upon receiving `TVALID = 1`, computes the MatMul-free ternary additions in a single cycle, and asserts the output.
4. **The DMA (S2MM)** captures the result and writes it back to DDR memory.
5. The CPU reads the result. Zero AXI-Lite polling or CPU-IP handshaking is required.

## Hardware Integration Fixes
Directly connecting an auto-generated HLS stream IP to a strict DMA controller presents several AXI protocol challenges. Here is how they were resolved in the Block Design:

### 1. The `TLAST` Packet Boundary Injection
* **The Problem:** The AXI DMA absolutely requires a `TLAST` (Last) signal on the S2MM (Stream-to-Memory) channel to know when a packet has finished. The BitNet IP outputs raw numbers, not formatted AXI packets, causing the DMA to hang indefinitely.
* **The Solution:** We inserted a **Xilinx AXI4-Stream Subset Converter** between the BitNet IP and the DMA. This block was configured to forcefully inject a constant `1` into the `TLAST` pin. Because the BitNet IP outputs the entire prediction in a single clock beat, that single beat is chronologically always the "last" beat.



### 2. AXI Bus Width Balancing (1024-bit Firehose)
* **The Problem:** The AI accelerator ingests and outputs all 64 features (16 bits each) in parallel, requiring a massive 1024-bit physical data bus. The default DMA is 32 bits, causing connection validation failures. 
* **The Solution:** We explicitly expanded both the Stream and Memory-Mapped widths of the DMA to 1024 bits. This forces the background AXI Interconnects to automatically instantiate highly optimized memory width converters, funneling the massive 1024-bit IP beats cleanly into the Zynq's 64-bit DDR memory port.

## Automated Block Design Generation (Tcl)
To eliminate manual GUI errors and ensure absolute reproducibility, the entire Block Design is generated via a Tcl script. 

### Usage
1. Open Vivado 2024.1 and create an empty RTL project targeting your specific board part (e.g., `xc7z010clg400-1`).
2. Open the **Tcl Console** at the bottom of the Vivado GUI.
3. Source the provided build script:
   ```tcl
   source build_bd.tcl
   ```
4. The script will automatically:
   * Import the custom `mts:hls:BitNet_LLM:1.0` IP.
   * Instantiate the Zynq PS and AXI DMA.
   * Drop in the Subset Converter and configure the `TLAST` remap.
   * Wire all AXI-Stream data paths and AXI-Lite control paths.
   * Map the High-Performance (HP0) memory ports.
   * Validate and save the design.
5. Right-click the generated `design_1` in the Sources tab, select **Create HDL Wrapper**, and click **Generate Bitstream**.

**Output:** A physical `.bit` hardware file and an exported `.xsa` (Xilinx Support Archive) file to hand off to the Vitis software environment.
