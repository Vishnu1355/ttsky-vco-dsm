# Ring pair: interface spec for the analog design

Everything except this block is done and verified. The analog ring pair must meet this spec so the
digital macro decodes it correctly. All numbers come from the behavioural model the digital design
was verified against (`test/vco_model.py`, parameters `NOMINAL`).

## Topology
- Two identical 15-stage single-ended current-starved inverter rings (odd stage count, so they oscillate).
- Pseudo-differential: ring P is tuned by `ua[0]` (Vin+), ring N by `ua[1]` (Vin-). No shared bias node
  that couples them strongly.
- Supply: VDPWR (1.8 V) only; no VAPWR.

## Frequency plan (clock = 50 MHz)
| Quantity | Value | Why |
|---|---|---|
| Centre frequency at Vin+ = Vin- = Vcm | 50 MHz (1.0 x clock) | Model fc = 1.0 cycle/clock |
| Frequency at full-scale input (each ring) | about 45.4 to 55.6 MHz (-9 % / +11 %) | m = 0.104, reciprocal tuning |
| Hard limit, all PVT corners and inputs | 25 MHz < f < 75 MHz | Decoder assumes 0.5 fs < f < 1.5 fs (no revolution counter) |
| Mismatch between rings | below about 2 % | Corrector + one-time trim handle up to about 2 % |
| Tuning-gain drift after trim | within about +-2 % | Fixed cubic coefficient tolerance |

The cubic coefficient k3 = 2^-3 - 2^-7 assumes the base paper's curvature (m = 0.104, g = -0.00285).
After layout, extract the real V-to-f curve, fit m and g, and re-check k3 with `e9d.py`-style simulation.
If the fitted curvature differs a lot, change the two shifts in `backend.v` (S_A1/S_A2).

## Taps (digital outputs of the rings)
- 15 taps per ring: `tapP[i]` / `tapN[i]` = output of stage i, where stage i drives stage i+1 and stage 14
  drives stage 0. The decoder's alternating-inversion mask (`15'b010101010101010`) depends on this order.
- Each tap needs a small buffer (e.g. a minimum inverter pair) so it swings rail to rail at 1.8 V and the
  synchronizer flip-flop loads do not slow the ring unevenly. Load every stage identically.
- Taps are sampled asynchronously by 2-flop synchronizers. Occasional bubbles are tolerated: the
  decoder counts ones, so a single misread tap moves the phase by at most one step, and the error
  cancels after the differentiator (verified with 2 % bubble rate, 0 mismatches vs golden).

## Pin and placement
- Digital macro (`vco_dsm_digital`, about 150 x 170 um) sits at the bottom of the 160 x 225 um tile;
  rings go in the strip above it (about 160 x 50 um), taps enter the macro's north edge.
- `ua[0]`, `ua[1]` connect to the ring tuning inputs. Analog path from pad: < 500 ohm, < 5 pF, < 4 mA.
