# Vivado Block Design

This directory contains the Vivado project used to wire the custom BitNet IP to the Zynq Processing System (PS).



## System Integration
The block design utilizes a standard AXI interconnect topology:
1.  **ZYNQ7 Processing System:** Configured with UART and DDR enabled.
2.  **Processor System Reset:** Generates synchronized resets across the fabric.
3.  **AXI Interconnect:** Routes the 32-bit AXI4-Lite master from the ARM Cortex-A9 to the slave ports of the BitNet IP.
4.  **BitNet LLM IP:** The exported custom IP. 

*Note: The `interrupt` pin on the IP is intentionally left disconnected. Due to the ultra-low execution latency (~133 clock cycles), bare-metal processor polling is significantly faster than the overhead of triggering a hardware interrupt routine.*

## Quick Build
A fully automated build script (`build_vivado.tcl`) is provided. Open the Vivado Tcl Console and run:
```tcl
source build_vivado.tcl
launch_runs impl_1 -to_step write_bitstream -jobs 8
