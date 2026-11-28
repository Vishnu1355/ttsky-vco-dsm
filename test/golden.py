"""Cycle-accurate integer model of vco_dsm_digital (sync -> decoders -> front end -> back end).
Used by the cocotb tests to check the RTL bit-exactly."""
import numpy as np
MASK_ALT = 0b010101010101010
B = 18; MASKB = (1 << B) - 1; F = 16; MASKF = (1 << F) - 1; SAT = (1 << 15) - 1

def phase_dec(s):
    t = s ^ MASK_ALT
    c = bin(t).count("1")
    lo = (t & 1) + ((t >> 1) & 1) + ((t >> 2) & 1)
    hi = ((t >> 12) & 1) + ((t >> 13) & 1) + ((t >> 14) & 1)
    if c == 0: return 0
    return c if lo >= hi else 30 - c

def taps_from_phase(p):
    """Ideal ring state for phase p (0..29), inverse of phase_dec."""
    t = ((1 << p) - 1) if p <= 15 else (((1 << 15) - 1) ^ ((1 << (p - 15)) - 1))
    return t ^ MASK_ALT

def front_end_stream(tapsP, tapsN):
    """Value of the front end's d register during each clock cycle n (what the back end adds)."""
    p1 = n1 = s2P = s2N = 0; dphi_d = 0; dreg = 0; out = []
    for a, b in zip(tapsP, tapsN):
        out.append(dreg)
        pP, pN = phase_dec(s2P), phase_dec(s2N)
        dphi = (pP - pN) % 30
        df = dphi - dphi_d
        dw = df - 30 if df >= 15 else df + 30 if df < -15 else df
        dphi_d, dreg = dphi, dw
        s2P, s2N, p1, n1 = p1, n1, a, b
    return np.array(out)

def wrapB(v): v &= MASKB; return v - (1 << B) if v >> (B - 1) else v
def smul(x, y):
    acc = 0
    for i in range(F): acc = (acc + (x if (y >> i) & 1 else 0)) >> 1
    return acc & MASKF

def backend(d, t1=0, t2=0, bypass=False):
    i1 = i2 = 0; cd = [0, 0]; wh = [0, 0]; out = []
    for n, x in enumerate(d):
        i1 = wrapB(i1 + int(x)); i2 = wrapB(i2 + i1)
        if n % 64 == 63:
            s = i2
            for k in range(2): v = wrapB(s - cd[k]); cd[k] = s; s = v
            w = s; t = w + wh[1]
            y = (wh[0] + (wh[0] >> 2) + (wh[0] >> 3)) - ((t >> 3) + (t >> 4))
            wh = [w, wh[0]]
            o = y
            if not bypass:
                sg = y < 0; a = min(-y if sg else y, MASKF)
                p2 = smul(a, a); p3 = smul(a, p2)
                t3 = (p3 >> 5) - (p3 >> 7)   # Option A: k3 = 2^-5 - 2^-7 (was p3 >> 3)
                o = y + (-t3 if sg else t3)
                for tt in (t1, t2):
                    if (tt >> 4) & 1:
                        u = p2 >> (4 + (tt & 7)); o += -u if (tt >> 3) & 1 else u
            out.append(max(-SAT, min(SAT, o)))
    return np.array(out)

def chip(tapsP, tapsN, t1=0, t2=0, bypass=False):
    return backend(front_end_stream(tapsP, tapsN), t1, t2, bypass)
