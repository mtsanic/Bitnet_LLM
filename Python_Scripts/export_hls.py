import torch
import hls4ml
import onnx
import os
import warnings
from brevitas.export import export_qonnx
from qonnx.util.cleanup import cleanup

warnings.filterwarnings("ignore", message=".*Named tensors and all their associated APIs.*")
from bitnet import QuantBitNetBlock


def generate_vitis_hls():
    print("="*50)
    print("🛠️ INITIATING HLS4ML VITIS HLS 2024.1 GENERATION")
    print("="*50)

    hidden_dim = 64
    model = QuantBitNetBlock(hidden_dim=hidden_dim)
    
    weights_path = "./BitNet_LLM_Trained_Models/trained_bitnet.pth"
    onnx_path = "./BitNet_LLM_Trained_Models/bitnet_158b.onnx"
    output_dir = "./Vitis_HLS/bitnet_hls_workspace"
    
    if os.path.exists(weights_path):
        print(f"[*] Loading trained weights from: {weights_path}")
        model.load_state_dict(torch.load(weights_path, weights_only=True))
    else:
        print(f"⚠️ FATAL: {weights_path} not found. Run bitnet.py first.")
        return
    
    model.eval() 
    
    input_shape = (1, hidden_dim)
    dummy_input = torch.randn(input_shape)

    print(f"[*] Exporting strictly quantized Brevitas model to: {onnx_path}")
    export_qonnx(model, dummy_input, onnx_path)

    print("[*] Running QONNX cleanup (Constant Folding & Shape Inference)...")
    cleanup(onnx_path, out_file=onnx_path)

    print("[*] Loading sanitized ONNX model into memory...")
    onnx_model = onnx.load(onnx_path)

    fpga_part = 'xc7z010clg400-1'
    print(f"[*] Generating hls4ml configuration for part: {fpga_part}")
    
    config = hls4ml.utils.config_from_onnx_model(
        onnx_model, 
        granularity='name', 
        backend='Vitis' 
    )
    
    config['Model']['Strategy'] = 'Resource'
    config['Model']['ReuseFactor'] = 4 

    # ---------------------------------------------------------
    # THE FIX: Hardware Bus Width Clamping
    # ---------------------------------------------------------
    # Force the compiler to use strict 16-bit precision across 
    # all layers to guarantee the bus width stays under 4096 bits.
    for layer in config['LayerName'].keys():
        config['LayerName'][layer]['Precision'] = {
            'default': 'ap_fixed<16,6>',
            'accum': 'ap_fixed<16,6>',
            'result': 'ap_fixed<16,6>',
            'weight': 'ap_fixed<8,2>',
            'bias': 'ap_fixed<16,6>'
        }

    print(f"[*] Compiling pure integer graph into Vitis HLS C++ at ./{output_dir} ...")
    
    hls_model = hls4ml.converters.convert_from_onnx_model(
        onnx_model,                  
        hls_config=config,
        output_dir=output_dir,
        project_name="bitnet",   
        part=fpga_part,
        clock_period=10.0,           
        io_type='io_stream',         
        backend='Vitis'              
    )

    hls_model.write()
    
    print("✅ Vitis HLS project successfully generated with CLAMPED precision!")
    print("="*50)

if __name__ == "__main__":
    generate_vitis_hls()
