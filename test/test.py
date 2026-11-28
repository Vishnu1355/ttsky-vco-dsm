"""cocotb tests for vco_dsm_digital: readout path, bring-up modes, bit-exact ADC chain vs the golden
model (with ring bubbles), correction on/off A/B, and SNDR from the captured pin data."""
import numpy as np, cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import golden as G, ring_vectors as R, vco_model as mdl

T1, T2 = 0x1e, 0x1f                   # even-order trim, best for the post-layout ring_pair at Vcm 1.04 V (Option A)

async def reset(dut, ui=0, uio=0):
    cocotb.start_soon(Clock(dut.clk, 20, unit="ns").start())      # 50 MHz
    dut.ena.value = 1; dut.ui_in.value = ui; dut.uio_in.value = uio
    dut.tapP_a.value = 0; dut.tapN_a.value = 0; dut.rst_n.value = 0
    await ClockCycles(dut.clk, 3)
    dut.rst_n.value = 1

async def run_capture(dut, tapsP, tapsN):
    """Drive one tap pair per clock; rebuild 16-bit words from the pins (frame/byte_sel protocol)."""
    words, hi, last_fr = [], None, 0
    for a, b in zip(tapsP, tapsN):
        dut.tapP_a.value = int(a); dut.tapN_a.value = int(b)
        await RisingEdge(dut.clk)
        uio = int(dut.uio_out.value); fr, bs = (uio >> 6) & 1, (uio >> 5) & 1
        byte = int(dut.uo_out.value)
        if fr != last_fr:                                  # new sample: high byte now on the pins
            hi, last_fr = byte, fr
        elif bs and hi is not None:                        # low byte phase
            w = (hi << 8) | byte; words.append(w - 65536 if w & 0x8000 else w); hi = None
    return np.array(words)

@cocotb.test()
async def test_ramp_readout(dut):
    """Mode 10: the word counts up once per sample -> proves the byte/frame protocol."""
    await reset(dut, ui=0b10 << 6)
    n = 64 * 40
    words = await run_capture(dut, [0] * n, [0] * n)
    assert len(words) >= 35, len(words)
    assert np.all(np.diff(words) == 1), words[:10]
    dut._log.info(f"ramp: {len(words)} words, {words[0]}..{words[-1]}")

@cocotb.test()
async def test_phase_debug(dut):
    """Mode 01: uo_out shows the decoded ring-P phase (bring-up check that the ring is alive)."""
    await reset(dut, ui=0b01 << 6)
    for p in range(30):
        dut.tapP_a.value = G.taps_from_phase(p)
        await ClockCycles(dut.clk, 3)
        assert int(dut.uo_out.value) == p, (p, int(dut.uo_out.value))

async def adc_run(dut, bypass, bubble_rate):
    await reset(dut, ui=T1 | (bypass << 5), uio=T2)
    tP, tN = R.make(bubble_rate=bubble_rate)
    got = await run_capture(dut, tP, tN)
    exp = G.chip(tP, tN, T1, T2, bypass)
    n = min(len(got), len(exp)) - 1
    assert n > 1200, n
    mism = int(np.sum(got[:n] != exp[:n]))
    sndr = mdl.metrics(mdl.trim(got.astype(float), n_dec=1024), 29)["SNDR"]
    dut._log.info(f"bypass={bypass} bubbles={bubble_rate}: {n} words, {mism} mismatches, SNDR {sndr:.1f} dB")
    assert mism == 0
    return sndr

@cocotb.test()
async def test_adc_bitexact_with_bubbles(dut):
    """Full chain from ring taps to pins, 2 % ring bubbles, bit-exact against the golden model."""
    s = await adc_run(dut, bypass=0, bubble_rate=0.02)
    assert s > 70.0, s

@cocotb.test()
async def test_correction_on_off(dut):
    """Correction bypassed: still bit-exact, and the SNDR drop shows what the corrector buys."""
    s_off = await adc_run(dut, bypass=1, bubble_rate=0.0)
    s_on = await adc_run(dut, bypass=0, bubble_rate=0.0)
    dut._log.info(f"correction buys {s_on - s_off:.1f} dB ({s_off:.1f} -> {s_on:.1f})")
    assert s_off < 70.0 and s_on > s_off + 3.0, (s_off, s_on)
