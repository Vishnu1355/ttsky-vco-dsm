"""Ring tap sequences from the validated converter model: sampled ring phase (0..29) per clock,
mapped to 15-bit tap patterns, with optional bubbles (one tap misread near the wavefront)."""
import numpy as np, vco_model as mdl
from golden import taps_from_phase

def ring_phases(x, prmP, prmN, M=15, seed=3):
    rng = np.random.default_rng(seed); out = []
    for xin, prm in ((x, prmP), (-x, prmN)):
        f = mdl.ring_freq(xin, prm["m"], prm["g"], prm["fc"])
        phi = rng.random() + np.cumsum(f)
        out.append(np.floor(phi * 2 * M).astype(np.int64) % (2 * M))
    return out

def taps(phases, bubble_rate=0.0, seed=7):
    rng = np.random.default_rng(seed); t = np.array([taps_from_phase(int(p)) for p in phases])
    if bubble_rate:
        hit = rng.random(len(t)) < bubble_rate
        for i in np.nonzero(hit)[0]:
            p = int(phases[i]); edge = p % 15                       # stage at the wavefront
            t[i] ^= 1 << min(14, edge + int(rng.integers(0, 2)))     # flip the tap at/after the edge
    return t

def make(k_bin=29, amp=0.891, n_dec=1024, mism=0.012, bubble_rate=0.0, seed=3):
    nom = mdl.NOMINAL; N = dict(nom, m=nom["m"] * (1 + mism))
    x = mdl.stimulus(k_bin, amp, n_dec=n_dec)
    pP, pN = ring_phases(x, nom, N, seed=seed)
    return taps(pP, bubble_rate, seed + 1), taps(pN, bubble_rate, seed + 2)
