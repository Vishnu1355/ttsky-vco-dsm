"""Ring tap sequences from the validated converter model: sampled ring phase (0..29) per clock,
mapped to 15-bit tap patterns, with optional bubbles (one tap misread near the wavefront)."""
import numpy as np, vco_model as mdl, json, os
from golden import taps_from_phase

# Ring transfer curves: by default the post-layout ring_pair curves (TinyTapeout SKY130, tt 27 C, Vcm 1.04 V, ring N
# with its own curve + 1 % extra gain mismatch) from ring_curves.json; RING_MODEL=patent selects the base-paper model.
_CURVES = os.path.join(os.path.dirname(__file__), "ring_curves.json")
def _freq(x, prm):
    if prm.get("type") == "poly":
        return prm.get("fc", 1.0) * np.polyval(list(prm["c"])[::-1], x)
    return mdl.ring_freq(x, prm["m"], prm["g"], prm["fc"])

def ring_phases(x, prmP, prmN, M=15, seed=3):
    rng = np.random.default_rng(seed); out = []
    for xin, prm in ((x, prmP), (x, prmN)) if prmP.get("type") == "poly" else ((x, prmP), (-x, prmN)):
        f = _freq(xin, prm)
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
    if os.environ.get("RING_MODEL", "post_layout") == "patent":
        nom = mdl.NOMINAL; N = dict(nom, m=nom["m"] * (1 + mism))
    else:                              # curveN already maps +x to ring N's (Vcm - v) input
        c = json.load(open(_CURVES)); nom, N = c["curveP"], c["curveN"]
    x = mdl.stimulus(k_bin, amp, n_dec=n_dec)
    pP, pN = ring_phases(x, nom, N, seed=seed)
    return taps(pP, bubble_rate, seed + 1), taps(pN, bubble_rate, seed + 2)
