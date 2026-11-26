"""
Behavioural model of a pseudo-differential ring-VCO delta-sigma ADC,
built on the physics of the base paper:
  I. Galton, G. Taylor, US 8,542,138 B2 (2013), "Ring oscillator delta sigma ADC
  modulator with replica path nonlinearity calibration" (UCSD).

Physics used (base paper eqs. 1-16):
  * Inverter delay changes ~linearly with input -> ring PERIOD linear in x, so the
    FREQUENCY is reciprocal:  f(x) = fc / (1 - m*x - g*x^3)          (eq. 8-13)
    m : full-scale fractional tuning (m=0.1 -> HD2 = -26 dBc, as in the base paper)
    g : residual cubic delay non-ideality ("in practice ... not perfectly linear")
  * Ring sampler + phase decoder quantize phase to 1/(2M) cycle (M = ring stages).
  * Centre frequency ~ fs, so 0.5fs < f < 1.5fs and phase decode / differentiation
    are done MODULO ONE CYCLE (eq. 2). No revolution counter is needed.
  * Pseudo-differential: path P driven by +x, path N by -x, outputs differenced.
    Even-order terms cancel only to the matching accuracy of the two paths.
  * Optional common-mode noise c[n] enters both paths (P: x+c, N: -x+c); the strong
    per-path 2nd-order term converts it to differential noise (base paper col. 12, 19).

Everything is in normalized units: x in [-1,1] is the differential input / full scale.
"""
import numpy as np

# ------------------------------------------------------------------ operating point
FS   = 50e6          # sample clock (TinyTapeout-class)
OSR  = 128
BW   = FS / (2 * OSR)  # 195.3 kHz
D1, D2 = 16, 4       # sinc^4 /16  ->  125-tap Kaiser FIR /4
D    = D1 * D2       # total decimation 64 -> fo = 781.25 kHz (Nyquist = 2*BW)
ND   = 4096          # output samples kept for the FFT
WARM = 128           # output warm-up samples discarded
import os as _os
FIR2 = np.load(_os.path.join(_os.path.dirname(__file__), "fir2.npy"))

# Calibrated to the base paper's single-path full-scale harmonics (col. 8):
#   HD2=-26, HD3=-47 dBc (fitted)  ->  HD4=-64.7 dBc predicted vs -64 dBc reported.
NOMINAL = dict(m=0.1040, g=-0.00285, fc=1.0)


def ring_freq(x, m, g, fc):
    """Instantaneous ring frequency in cycles per sample (fs-normalized)."""
    return fc / (1.0 - m * x - g * x ** 3)


def path_codes(xin, prm, M, rng, phi0=None):
    """One ring path: phase accumulation, ring-sampler quantization, modulo-one-cycle
    first difference. Returns signed integer codes y in [-M, M)."""
    nst = 2 * M
    f = ring_freq(xin, prm["m"], prm["g"], prm["fc"])
    assert f.min() > 0.5 and f.max() < 1.5, "overload: violates 0.5fs<f<1.5fs (eq.2)"
    if phi0 is None:
        phi0 = rng.random()
    phi = phi0 + np.cumsum(f)                       # cycles
    q = np.floor(phi * nst).astype(np.int64)        # sampled phase state
    y = np.diff(q, prepend=int(np.floor(phi0 * nst)))
    return ((y + M) % nst) - M                      # modulo one cycle, centred


def run_converter(x, M=15, prmP=None, prmN=None, cm=None, rng=None):
    """Pseudo-differential converter. Returns per-path codes (yP, yN)."""
    rng = rng or np.random.default_rng(1)
    prmP = prmP or NOMINAL
    prmN = prmN or NOMINAL
    c = 0.0 if cm is None else cm
    yP = path_codes(x + c, prmP, M, rng)
    yN = path_codes(-x + c, prmN, M, rng)
    return yP, yN


# ------------------------------------------------------------------ decimation
def decimate(y):
    """Realistic 2-stage decimator: sinc^4 by D1, then 125-tap FIR by D2 (unity DC gain)."""
    k = np.ones(D1) / D1
    z = np.asarray(y, float)
    for _ in range(4):
        z = np.convolve(z, k)
    z = z[4 * (D1 - 1)::D1][: len(y) // D1]
    z = np.convolve(z, FIR2)
    return z[len(FIR2) - 1::D2][: len(y) // D]

cic3 = decimate   # backward-compatible name


def stimulus(k_bin, amp, n_dec=ND, warm=WARM):
    """Coherent sine: exactly k_bin cycles in the n_dec decimated window."""
    n = (n_dec + 2 * warm) * D        # guard band at BOTH ends (filter head + tail)
    t = np.arange(n)
    return amp * np.sin(2 * np.pi * k_bin * t / (n_dec * D))


def trim(zd, warm=WARM, n_dec=ND):
    return zd[warm: warm + n_dec]


# ------------------------------------------------------------------ metrics
def metrics(z, k_bin, n_harm=9):
    """SNDR / SNR / THD / SFDR over [0, BW] of a decimated record (fd = FS/D)."""
    z = np.asarray(z, float)
    z = z - z.mean()
    w = np.hanning(len(z))
    X = np.abs(np.fft.rfft(z * w)) ** 2
    fd = FS / D
    kbw = int(BW / (fd / len(z)))                 # last in-band bin
    def grp(k, h=3):
        return X[max(1, k - h): k + h + 1].sum()
    Ps = grp(k_bin)
    harm = [h * k_bin for h in range(2, n_harm + 1) if h * k_bin <= kbw]
    Ph = sum(grp(k) for k in harm) + 1e-300
    mask = np.zeros(len(X), bool)
    mask[1: kbw + 1] = True
    for k in [k_bin] + harm:
        mask[max(1, k - 3): k + 4] = False
    Pn = X[mask].sum() + 1e-300
    spurs = [grp(k) for k in harm] + [X[mask].max()]
    sndr = 10 * np.log10(Ps / (Pn + Ph))
    return dict(SNDR=sndr, SNR=10 * np.log10(Ps / Pn), THD=10 * np.log10(Ph / Ps),
                SFDR=10 * np.log10(Ps / max(spurs)), ENOB=(sndr - 1.76) / 6.02)


def harmonics_dbc(z, k_bin, n=4):
    z = np.asarray(z, float); z = z - z.mean()
    X = np.abs(np.fft.rfft(z * np.hanning(len(z)))) ** 2
    def grp(k, h=3): return X[max(1, k - h): k + h + 1].sum()
    p1 = grp(k_bin)
    return [10 * np.log10(grp(h * k_bin) / p1) for h in range(2, n + 1)]


# ------------------------------------------------------------------ exact inverses
def solve_x(u, m, g, iters=6):
    """Solve m*x + g*x^3 = u for x (Newton)."""
    x = u / m
    for _ in range(iters):
        x = x - (m * x + g * x ** 3 - u) / (m + 3 * g * x ** 2)
    return x


def inv_path(w, prm, sign):
    """Exact per-path inverse: w = f/fc_nom - 1 measured -> input estimate.
    f = fc/(1-u)  ->  u = 1 - fc/(1+w);  input = sign * solve_x(u)."""
    u = 1.0 - prm["fc"] / (1.0 + w)
    return sign * solve_x(u, prm["m"], prm["g"])


def inv_diff(z, prm):
    """Exact static inverse of the differential output for matched paths.
    z = fP - fN = fc*2u/(1-u^2)  ->  u = (sqrt(1+(z/fc)^2) - 1)/(z/fc)."""
    zz = np.asarray(z, float) / prm["fc"]
    safe = np.where(np.abs(zz) < 1e-12, 1e-12, zz)
    u = np.where(np.abs(zz) < 1e-12, zz / 2, (np.sqrt(1 + safe ** 2) - 1) / safe)
    return solve_x(u, prm["m"], prm["g"])
