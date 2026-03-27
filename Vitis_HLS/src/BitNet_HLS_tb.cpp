#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <iomanip>
#include <sstream>
#include "BitNet_HLS.h"

// Update this if Python generates a different scale factor!
#define BITNET_SCALE 0.5038f 
#define ERROR_THRESHOLD 0.002

int main() {
    std::ifstream fin("tb_data/tb_input_features.dat");
    std::ifstream fpr("tb_data/tb_output_predictions.dat");

    if (!fin.is_open() || !fpr.is_open()) {
        std::cout << "ERROR: Cannot find tb_data files. Make sure tb_data folder is in the work directory." << std::endl;
        return 1;
    }

    input_t  hls_input[IN_SIZE];
    result_t hls_output[OUT_SIZE];
    
    double total_mae = 0.0;
    int sample_count = 0;

    std::cout << std::string(60, '=') << std::endl;
    std::cout << std::setw(8) << "Sample" 
              << std::setw(15) << "MAE" 
              << std::setw(15) << "Max Diff" 
              << std::setw(15) << "Status" << std::endl;
    std::cout << std::string(60, '-') << std::endl;

    std::string line_in, line_out;
    while (std::getline(fin, line_in) && std::getline(fpr, line_out)) {
        if (line_in.empty()) continue;

        std::stringstream ss_in(line_in);
        std::stringstream ss_out(line_out);

        for (int i = 0; i < IN_SIZE; i++) {
            float val_in;
            ss_in >> val_in;
            hls_input[i] = (input_t)val_in;
        }

        BitNet_HLS(hls_input, hls_output);

        double sample_error = 0.0;
        float max_diff = 0.0;
        for (int i = 0; i < OUT_SIZE; i++) {
            float gold;
            ss_out >> gold;
            float scaled_hls = (float)hls_output[i] * BITNET_SCALE;
            
            float diff = std::abs(gold - scaled_hls);
            sample_error += diff;
            if (diff > max_diff) max_diff = diff;
        }

        double mae = sample_error / OUT_SIZE;
        total_mae += mae;

        if (sample_count % 10 == 0 || sample_count == 99) {
            std::cout << std::setw(8) << sample_count 
                      << std::setw(15) << std::fixed << std::setprecision(5) << mae 
                      << std::setw(15) << max_diff 
                      << std::setw(15) << (mae < ERROR_THRESHOLD ? "PASS" : "FAIL") << std::endl;
        }
        sample_count++;
    }

    double final_avg_mae = (sample_count > 0) ? (total_mae / sample_count) : 0.0;
    
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "TESTBENCH SUMMARY" << std::endl;
    std::cout << "Total Samples: " << sample_count << std::endl;
    std::cout << "Average MAE:   " << std::setprecision(6) << final_avg_mae << std::endl;
    std::cout << std::string(60, '=') << std::endl;

    fin.close();
    fpr.close();
    return 0;
}