## How it works

A pseudo-differential ring-oscillator ADC. Two 15-stage rings are tuned by Vin+ (`ua[0]`) and Vin-
(`ua[1]`). Their sampled phases are subtracted (mod 30) and differentiated once, giving a first-order
noise-shaped code. A sinc2 decimator (/64) turns it into 781.25 kS/s samples. One shared adder then
flattens the sinc droop (taps -3/16, 1+3/8, -3/16, shifts only) and removes the rings' curvature with
a fixed cubic correction y + (2^-3 - 2^-7) y^3 plus a small even-order trim set from the pins. There
is no multiplier and no calibration loop.

Simulated: SNDR about 73 dB at -1 dBFS with correction, about 49 dB with correction bypassed.

## Pins

| Pin | Function |
|---|---|
| ua[0], ua[1] | Vin+, Vin- |
| ui[4:0] | even-order trim term 1: {enable, sign, offset[2:0]}, term = p2 >> (4 + offset) |
| uio[4:0] | even-order trim term 2 (same format), inputs |
| ui[5] | 1 = bypass the correction (for on/off comparison) |
| ui[7:6] | mode: 00 ADC word, 01 ring-P phase, 10 ramp test pattern, 11 raw difference code |
| uo[7:0] | data byte |
| uio[5] | byte select: 0 = high byte, 1 = low byte (32 clocks each) |
| uio[6] | frame: toggles once per new sample |
| uio[7] | saturation flag for the current sample |

Nominal trim: term 1 = 0b10100 (+2^-8), term 2 = 0b11111 (-2^-11). Re-trim per chip on the bench.

## How to test

1. Clock 50 MHz. Set mode 10: the 16-bit word must count up once per frame (checks the readout).
2. Mode 01 with a slow clock: the ring-P phase on uo[4:0] must cycle through 0..29 (ring alive).
3. Mode 11: apply DC inputs; the average raw code tracks Vin+ - Vin- (transfer curve).
4. Mode 00: apply a low-distortion sine, capture words (read the high byte after each frame edge, the
   low byte after byte select rises), compute SNDR with an FFT.
5. Sweep the two trim terms for best SNDR, then toggle ui[5] to measure the correction's gain on the
   same chip.

## External hardware

Low-distortion differential sine source (THD better than about -80 dB, e.g. an audio DAC with a passive
filter), DC bias for the common mode, and a capture path for about 1.6 MB/s (RP2040 PIO on the demo
board, or a logic analyser).
