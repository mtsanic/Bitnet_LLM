#include "BitNet_HLS.h"

void BitNet_HLS(
    input_t in[IN_SIZE],
    result_t out[OUT_SIZE]
) {
    // AXI-Lite interfaces for Zynq PS-PL communication
    #pragma HLS INTERFACE s_axilite port=return
    #pragma HLS INTERFACE s_axilite port=in
    #pragma HLS INTERFACE s_axilite port=out

    // Include the Python-generated PyTorch weights using Xilinx's 8-bit int
    static const ap_int<8> weights[OUT_SIZE][IN_SIZE] = {
        #include "weights_data.h" 
    };

    // Internal 32-bit accumulators
    ap_fixed<32, 12> acc[OUT_SIZE];
    #pragma HLS ARRAY_PARTITION variable=acc complete

    // Initialize accumulators to 0
    Init_Loop: for(int i = 0; i < OUT_SIZE; i++) {
        #pragma HLS UNROLL
        acc[i] = 0;
    }

    // Multiply-Accumulate Loop (0 DSPs Used)
    Input_Loop: for (int i = 0; i < IN_SIZE; i++) {
        #pragma HLS PIPELINE II=1
        input_t val = in[i];

        Output_Loop: for (int j = 0; j < OUT_SIZE; j++) {
            ap_int<8> w = weights[j][i];
            
            // Explicit Ternary Logic
            if (w == 1) {
                acc[j] += val;
            } else if (w == -1) {
                acc[j] -= val;
            }
        }
    }

    // Write back to AXI-Lite output ports
    Write_Loop: for (int k = 0; k < OUT_SIZE; k++) {
        #pragma HLS UNROLL
        out[k] = (result_t)acc[k];
    }
}