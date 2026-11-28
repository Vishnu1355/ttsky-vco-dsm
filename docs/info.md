## How it works

A pseudo-differential ring-oscillator delta-sigma ADC.
- **Rings:** two identical 15-stage current-starved ring oscillators, tuned by Vin+ (`ua[0]`) and Vin- (`ua[1]`).
- **Front end:** the sampled ring phases are subtracted (mod 30) and differentiated once, which gives a first-order
  noise-shaped code.
- **Decimation:** a sinc2 decimator (/64) turns it into 781.25 kS/s samples.
- **Correction:** one shared adder flattens the sinc droop (taps -3/16, 1+3/8, -3/16, shifts only). It then removes
  the rings' curvature with a fixed cubic correction y + (2^-5 - 2^-7) y^3, plus a small even-order trim set from the
  pins. The cube comes from a shift-add multiply on the same adder. There is no multiplier and no calibration loop.

**Analog block (`ring_pair_tt`, 123.6 x 19.9 um, custom layout):**
- **Each ring:**
  - bias mirror: 8 x NMOS 0.42/0.5 on the input, into 8 x PMOS 0.84/0.5;
  - 15 symmetric current-starved stages (starve P 0.84/0.5 and N 0.42/0.5; inverter P 0.84/0.15, N 0.42/0.15), so
    rising and falling edges get equal current;
  - non-inverting two-inverter tap buffers.
- **Layout:** folded stage order, so every stage sees the same load. Every transistor has its own guard ring. A thin
  TinyTapeout wrapper adds met3 power rails.

**Simulated (post-layout rings, tt 27 C, 1.8 V, 50 MHz clock):**
- **Rings:** 50 MHz at 1.00 V, about 57 MHz at 1.04 V; 172-181 MHz/V; 0.28 mA for both rings.
- **Full scale:** about +-27.6 mV per input.
- **Ring-to-ring mismatch (Monte Carlo):** sigma about 2 % in frequency and in gain.
- **SNDR at Vcm 1.04 V, -1 dBFS:**
  - about 73.6 dB with the correction on (best trim t1 = 0x1e, t2 = 0x1f);
  - about 66 dB with the correction bypassed.
  - With the correction on it stays within 0.3 dB up to 6 % ring mismatch.
- The routed gate-level netlist is bit-exact with the model.

**Process, temperature and supply:**
- Re-set the common mode per chip; the 50 MHz point moves between 0.93 and 1.15 V.
- Best of correction on/off, with Vcm set to each corner's 50 MHz point (bench 57 MHz, step 3, is a bit better at
  tt): about 70 dB or more at the tt, ss, ff, sf and fs corners, -40/85 C and 1.62/1.98 V.
- The fixed cubic coefficient suits typical and slow silicon. On fast silicon or away from 1.8 V, bypassing the
  correction is better.
- At the extreme ss / 85 C / 1.62 V corner the rings run short of headroom (about 49 dB).

## Pins

| Pin | Function |
|---|---|
| ua[0], ua[1] | Vin+, Vin- (analog). DC level of both = common mode Vcm, about 1.04 V (set per chip, see below) |
| ui[4:0] | even-order trim term 1: {enable, sign, offset[2:0]}, term = p2 >> (4 + offset) |
| uio[4:0] | even-order trim term 2 (same format), inputs |
| ui[5] | 1 = bypass the correction |
| ui[7:6] | mode: 00 ADC word, 01 ring-P phase, 10 ramp test pattern, 11 raw difference code |
| uo[7:0] | data byte |
| uio[5] | byte select: 0 = high byte, 1 = low byte (32 clocks each) |
| uio[6] | frame: toggles once per new sample |
| uio[7] | saturation flag for the current sample |

Nominal trim (tt, Vcm 1.04 V): term 1 = 0b11110, term 2 = 0b11111. Re-trim per chip on the bench.

## How to test

1. **Readout:** clock 50 MHz. Set mode 10; the 16-bit word must count up once per frame.
2. **Ring alive:** mode 01 with a slow clock; the ring-P phase on uo[4:0] must cycle through 0..29.
3. **Common mode:** bias both inputs at the same DC level Vcm, starting from 1.04 V.
   - In mode 01 at the full 50 MHz clock, the phase stands still when the rings run at exactly 50 MHz. The drift
     rate shows the offset: 1 step per clock = 50 MHz / 30.
   - Set Vcm so the rings run about 10-20 % above the clock (best correction; about 1.04 V on a typical chip).
   - Keep them below 1.5x the clock (75 MHz).
4. **Transfer curve:** mode 11 with DC inputs; the average raw code tracks Vin+ - Vin-.
5. **SNDR:** mode 00. Apply a low-distortion differential sine around Vcm, up to about +-27 mV per input. Capture the
   words (high byte after each frame edge, low byte after byte select rises) and compute SNDR with an FFT.
6. **Trim:** sweep the two trim terms for the best SNDR, then toggle ui[5] to compare correction on/off. Keep the
   better setting for that chip: correction on for typical and slow silicon, bypass for fast silicon or supplies
   away from 1.8 V.

## External hardware

- **Signal source:** a low-distortion differential sine source (THD better than about -80 dB, e.g. an audio DAC with
  a passive filter).
- **Common mode:** an adjustable DC common mode of about 0.9-1.2 V (the source's DC offset, or a buffered divider
  from a clean reference).
- **Capture:** a capture path for about 1.6 MB/s (RP2040 PIO on the demo board, or a logic analyser).
