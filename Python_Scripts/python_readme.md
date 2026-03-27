# Python Quantization and Data Generation

This folder contains the Python scripts required to model the BitNet 1.58b layer, generate the golden reference data, and format that data for physical hardware-in-the-loop (HIL) verification.



## Included Scripts

### 1. `bitnet.py` (Core Quantization & Modeling)
Because FPGA hardware lacks native floating-point efficiency, we rely on the BitNet 1.58b architecture to quantize the network weights to ternary values (`-1, 0, 1`). 

This script performs the following tasks:
* **Model Simulation:** Runs a forward pass of a single linear layer using dummy features.
* **Quantization:** Converts the floating-point weights into ternary integers.
* **Scale Extraction:** Calculates the necessary floating-point scale factor (e.g., `0.5038f`) that the hardware will use to de-quantize the final output.
* **Test Vector Generation:** Exports 100 samples of input features (`tb_input_features.dat`) and their corresponding golden PyTorch outputs (`tb_output_predictions.dat`). These `.dat` files are used natively by the Vitis HLS C-simulation testbench.

### 2. `generate_vitis_testbed_h.py` (Bare-Metal C-Header Generation)
When validating the physical silicon on the Zynq-7000, the bare-metal ARM Cortex-A9 processor does not have an operating system or file system to read the `.dat` files dynamically. 

This script acts as a bridge by:
* Loading the generated `.dat` files.
* Formatting the 100 test samples into static, multi-dimensional C arrays (`tb_inputs` and `tb_golden`).
* Automatically generating a `test_data.h` header file and saving it directly to the `./Vitis/src/tb_data/` directory so it can be compiled directly into the hardware test application.

## Usage Workflow

**Step 1:** Generate the model data, extract the scale factor, and create the `.dat` test vectors:
```bash
python bitnet.py
python generate_vitis_testbed_h.py
