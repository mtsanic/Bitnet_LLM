import torch
import torch.nn as nn
import brevitas.nn as qnn
from brevitas.core.quant import QuantType
from brevitas.quant.solver import WeightQuantSolver
from brevitas.core.scaling import ScalingImplType
from brevitas.core.restrict_val import RestrictValueType
import os
import numpy as np

# hls4ml import is no longer strictly required, but left in case you un-comment later
import hls4ml 

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# --- 1. Brevitas Dependency Workarounds ---
class OverTensorView(nn.Module):
    def __init__(self): super().__init__()
    def forward(self, x): return x

class AbsMean(nn.Module):
    def __init__(self, scaling_stats_reduce_dim=None, keepdim=True):
        super().__init__()
        self.dim = scaling_stats_reduce_dim
        self.keepdim = keepdim
    def forward(self, x):
        return torch.mean(torch.abs(x), dim=self.dim, keepdim=self.keepdim) if self.dim else torch.mean(torch.abs(x))

# --- 2. BitNet 1.58b Quantizer ---
class BitNetWeightQuant(WeightQuantSolver):
    quant_type, scaling_impl_type = QuantType.TERNARY, ScalingImplType.STATS
    scaling_stats_impl, scaling_stats_op = AbsMean, 'MEAN'
    scaling_per_output_channel = False
    scaling_stats_input_view_shape_impl = OverTensorView
    restrict_scaling_type = RestrictValueType.FP
    bit_width, narrow_range, threshold, signed = 2, True, 0.5, True

def export_testbench_data(dummy_input, out_quant, folder_path="./Vitis_HLS/src/tb_data"):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # 1. Export Input Features
    input_data = dummy_input.detach().cpu().numpy().flatten()
    np.savetxt(os.path.join(folder_path, "tb_input_features.dat"), [input_data], delimiter=' ')
    
    # 2. Export Output Predictions (Golden)
    output_data = out_quant.detach().cpu().numpy().flatten()
    np.savetxt(os.path.join(folder_path, "tb_output_predictions.dat"), [output_data], delimiter=' ')
    
    print(f"[Success] Testbench data exported to {folder_path}")

def export_multi_sample_testbench(model, in_dim, num_samples=100, folder_path="./Vitis_HLS/src/tb_data"):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    inputs = []
    predictions = []
    
    print(f"\n[Dataset] Generating {num_samples} samples...")
    for _ in range(num_samples):
        # Generate random input
        sample_input = torch.randn(1, in_dim)
        
        # Get PyTorch "Golden" prediction (already quantized weights)
        with torch.no_grad():
            sample_output = model(sample_input)
            
        inputs.append(sample_input.detach().cpu().numpy().flatten())
        predictions.append(sample_output.detach().cpu().numpy().flatten())
    
    # Save as space-separated values (one sample per line)
    with open(os.path.join(folder_path, "tb_input_features.dat"), "w") as f_in:
        np.savetxt(f_in, inputs, fmt='%.8f', delimiter=' ')
        
    with open(os.path.join(folder_path, "tb_output_predictions.dat"), "w") as f_out:
        np.savetxt(f_out, predictions, fmt='%.8f', delimiter=' ')
    
    print(f"[Success] Exported {num_samples} samples to {folder_path}")

def export_weights_to_hls(ternary_weights, filename="./Vitis_HLS/src/weights_data.h"):
    """
    Converts a 64x64 ternary weight tensor into a C++ 2D array.
    """
    # Create the target directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Ensure weights are integers
    weights = ternary_weights.detach().cpu().numpy().astype(int)
    
    with open(filename, "w") as f:
        f.write("// BitNet 1.58b Ternary Weights (64x64)\n")
        for i in range(weights.shape[0]):
            # Join the row with commas
            row_str = ", ".join(map(str, weights[i]))
            # Wrap in braces and add a comma for the next row
            f.write(f"    {{ {row_str} }},\n")
            
    print(f"[Success] Weights exported to {filename}")


# --- 3. Main Execution ---
if __name__ == "__main__":
    torch.manual_seed(42) 
    in_dim, out_dim = 64, 64 
    
    # 1. Instantiate Brevitas Layer
    temp_quant_layer = qnn.QuantLinear(
        in_dim, out_dim, bias=False, 
        weight_quant=BitNetWeightQuant, return_quant_tensor=False
    )
    
    with torch.no_grad():
        nn.init.uniform_(temp_quant_layer.weight, -1.0, 1.0)
    
    # Define the dummy input and save it to a variable
    dummy_input = torch.randn(in_dim) 
    
    # Run the forward pass and save the result to out_quant
    out_quant = temp_quant_layer(dummy_input)
    
    # Extract Raw Integers and Scale
    qw = temp_quant_layer.quant_weight()
    scale_factor = qw.scale.detach().item()
    ternary_ints = (qw.value.detach() / scale_factor).round()
    
    print(f"Hardware Check - Unique Ints: {torch.unique(ternary_ints).tolist()}")
    print(f"Hardware Check - Scale Factor: {scale_factor:.4f}")

    # 2. Create hls4ml-ready model (now just used as a PyTorch container for inference)
    hls_ready_model = nn.Sequential(
        nn.Linear(in_dim, out_dim, bias=False)
    )
    
    with torch.no_grad():
        hls_ready_model[0].weight.copy_(ternary_ints)

    # =========================================================
    # hls4ml Generation Block (Commented Out for Manual Flow)
    # =========================================================
    '''
    print("\n[Export] Initializing hls4ml conversion...")
    
    config = hls4ml.utils.config_from_pytorch_model(
        hls_ready_model, 
        input_shape=(in_dim,), 
        granularity='name'
    )

    config['Model']['Precision'] = 'ap_fixed<16,6>' 
    config['Model']['AccumulatorPrecision'] = 'ap_fixed<32,12>' 
    
    for layer in config['LayerName'].keys():
        config['LayerName'][layer]['AccumulatorPrecision'] = 'ap_fixed<32,12>'
        config['LayerName'][layer]['ResultPrecision'] = 'ap_fixed<32,12>'
        config['LayerName'][layer]['ReuseFactor'] = 64
        config['LayerName'][layer]['Strategy'] = 'Resource'

    export_path = "./BitNet_LLM/Vitis_HLS/hls4ml_bitnet_prj"
    
    hls_model = hls4ml.converters.convert_from_pytorch_model(
        hls_ready_model,
        project_name='BitNet_HLS',
        hls_config=config,
        output_dir=export_path,
        part='xc7z010clg400-1'
    )
    
    hls_model.write()
    print(f"\n[Success] Project generated in '{export_path}'")
    '''
    
    # =========================================================
    # Export Data for Manual HLS
    # =========================================================
    print(f"\nFinal Step: Apply scale factor {scale_factor:.4f} in your Vitis Testbench/Wrapper.")

    # 1. Export 100 samples to the ./Vitis_HLS/src/tb_data folder
    #export_multi_sample_testbench(hls_ready_model, in_dim, num_samples=100, folder_path="./Vitis_HLS/src/tb_data")
    
    # 2. Export the ternary matrix for your manual C++ code
    export_multi_sample_testbench(temp_quant_layer, in_dim, num_samples=100, folder_path="./Vitis_HLS/src/tb_data")
