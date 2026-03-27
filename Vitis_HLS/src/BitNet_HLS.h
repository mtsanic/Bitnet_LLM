#ifndef BITNET_HLS_H
#define BITNET_HLS_H

#include <ap_fixed.h>
#include <ap_int.h>

// --- DIMENSIONS ---
#define IN_SIZE 64
#define OUT_SIZE 64

// --- PRECISION TYPES ---
// input_t: 16 bits total, 6 integer bits
typedef ap_fixed<16, 6> input_t;

// result_t: 32 bits total, 12 integer bits (Prevents accumulator overflow)
typedef ap_fixed<32, 12> result_t;

// --- FUNCTION PROTOTYPE ---
void BitNet_HLS(
    input_t in[IN_SIZE],
    result_t out[OUT_SIZE]
);

#endif