#include <stdio.h>
#include "xil_printf.h"
#include "xil_io.h"
#include "xparameters.h"
#include "test_data.h" 

#define BITNET_BASE_ADDR 0x40000000

#define CTRL_REG_OFFSET  0x000
#define IN_ARRAY_OFFSET  0x080  
#define OUT_ARRAY_OFFSET 0x100 

#define FLOAT_TO_FIXED_16_6(val) ((short)((val) * 1024.0f))
#define FIXED_32_12_TO_FLOAT(val) (((float)(int)(val)) / 1048576.0f)
#define BITNET_SCALE 0.5038f

// --- Direct Memory Addresses for Zynq ARM Global Timer ---
#define ZYNQ_TIMER_LOWER_32 0xF8F00200
#define ZYNQ_TIMER_CTRL     0xF8F00208

int main() {


     xil_printf("\r\n========================================\r\n");
    xil_printf("   BitNet 1.58b Hardware Accelerator\r\n");
    xil_printf("========================================\r\n");

    // 1. Generate some dummy float data 
    float input_features[64];
    for(int i = 0; i < 64; i++) {
        input_features[i] = 0.5f; // Simple test vector
    }

    xil_printf("[PS] Writing packed inputs to FPGA Fabric...\r\n");
    
    // 2. Write inputs to the AXI memory map (PACKING REQUIRED)
    // We step by 2 because we write two 16-bit values per 32-bit address
    for(int i = 0; i < 64; i += 2) {
        short val0 = FLOAT_TO_FIXED_16_6(input_features[i]);
        short val1 = FLOAT_TO_FIXED_16_6(input_features[i+1]);
        
        // Pack val1 into the top 16 bits, val0 into the bottom 16 bits
        u32 packed_val = ((u32)((u16)val1) << 16) | (u16)val0;
        
        // Write to address offset: word index (i/2) * 4 bytes
        Xil_Out32(BITNET_BASE_ADDR + IN_ARRAY_OFFSET + ((i / 2) * 4), packed_val);
    }

    xil_printf("[PS] Sending Start Command...\r\n");
    
    // 3. Start the IP (Write a '1' to Bit 0 of the Control Register)
    Xil_Out32(BITNET_BASE_ADDR + CTRL_REG_OFFSET, 0x01);

    // 4. Poll the Done bit (Wait for Bit 1 of the Control Register to flip to '1')
    while ((Xil_In32(BITNET_BASE_ADDR + CTRL_REG_OFFSET) & 0x02) == 0x00) {
        // Spinning... 
    }

    xil_printf("[PL] Computation Complete!\r\n");

    // 5. Read the results back and apply the scale
    // Outputs are 32-bit, so they are NOT packed. One output per word.
    float output_predictions[64];
    for(int i = 0; i < 64; i++) {
        // Read the raw 32-bit register
        u32 raw_val = Xil_In32(BITNET_BASE_ADDR + OUT_ARRAY_OFFSET + (i * 4));
        
        // Convert to float and apply the scale factor
        float unscaled_out = FIXED_32_12_TO_FLOAT(raw_val);
        output_predictions[i] = unscaled_out * BITNET_SCALE;
    }

    // 6. Print the first 5 results
    xil_printf("\r\n--- First 5 Output Predictions ---\r\n");
    for(int i = 0; i < 5; i++) {
        // xil_printf doesn't support floats natively, so we split into whole/fraction
        int whole = (int)output_predictions[i];
        int frac = (int)((output_predictions[i] - whole) * 10000);
        if (frac < 0) frac = -frac; 
        
        xil_printf("Out[%d]: %d.%04d\r\n", i, whole, frac);
    }

    xil_printf("\r\n[SYSTEM] Run Finished Successfully.\r\n");
    xil_printf("\r\n========================================\r\n\n\n");



    xil_printf("\r\n========================================\r\n");
    xil_printf("   BitNet Hardware-in-the-Loop Test\r\n");
    xil_printf("========================================\r\n");

    // 1. Force the ARM Global Timer ON (Write 1 to the control register)
    Xil_Out32(ZYNQ_TIMER_CTRL, 0x01);

    float total_mae = 0.0f;

    for (int sample = 0; sample < NUM_SAMPLES; sample++) {
        
        // Write Packed Inputs
        for(int i = 0; i < 64; i += 2) {
            short val0 = FLOAT_TO_FIXED_16_6(tb_inputs[sample][i]);
            short val1 = FLOAT_TO_FIXED_16_6(tb_inputs[sample][i+1]);
            u32 packed_val = ((u32)((u16)val1) << 16) | (u16)val0;
            Xil_Out32(BITNET_BASE_ADDR + IN_ARRAY_OFFSET + ((i / 2) * 4), packed_val);
        }

        // ==========================================
        //         HARDWARE TIMING BLOCK
        // ==========================================
        // Read the timer's current tick count
        u32 t_start = Xil_In32(ZYNQ_TIMER_LOWER_32);

        // Start the IP and Poll
        Xil_Out32(BITNET_BASE_ADDR + CTRL_REG_OFFSET, 0x01);
        while ((Xil_In32(BITNET_BASE_ADDR + CTRL_REG_OFFSET) & 0x02) == 0x00) {}

        // Read the timer again the exact microsecond it finishes
        u32 t_end = Xil_In32(ZYNQ_TIMER_LOWER_32);
        // ==========================================

        // Calculate elapsed ticks
        u32 raw_ticks = t_end - t_start;

        // Read Outputs and Calculate Error
        float sample_mae = 0.0f;
        for(int i = 0; i < 64; i++) {
            u32 raw_val = Xil_In32(BITNET_BASE_ADDR + OUT_ARRAY_OFFSET + (i * 4));
            float unscaled_out = FIXED_32_12_TO_FLOAT(raw_val);
            float final_out = unscaled_out * BITNET_SCALE;
            
            float diff = tb_golden[sample][i] - final_out;
            if (diff < 0) diff = -diff; 
            
            sample_mae += diff;
        }
        
        sample_mae /= 64.0f;
        total_mae += sample_mae;

        // Print progress every 10 samples
        if (sample % 10 == 0 || sample == NUM_SAMPLES - 1) {
            int whole_mae = (int)sample_mae;
            int frac_mae = (int)((sample_mae - whole_mae) * 10000);
            
            // Calculate microseconds: The timer runs at 333.33 MHz on standard Zynq
            float us_latency = (float)raw_ticks / 333.333f;
            int whole_us = (int)us_latency;
            int frac_us = (int)((us_latency - whole_us) * 1000);

            xil_printf("Sample %3d | MAE: %d.%04d | Raw Ticks: %u | Latency: %d.%03d us\r\n", 
                        sample, whole_mae, frac_mae, (unsigned int)raw_ticks, whole_us, frac_us);
        }
    }

    float avg_mae = total_mae / NUM_SAMPLES;
    int f_whole = (int)avg_mae;
    int f_frac = (int)((avg_mae - f_whole) * 10000);

    xil_printf("\r\n========================================\r\n");
    xil_printf("Total Samples Evaluated: %d\r\n", NUM_SAMPLES);
    xil_printf("Final Physical Silicon MAE: %d.%04d\r\n", f_whole, f_frac);
    xil_printf("========================================\r\n");

    return 0;
}
