"""Compara los renders de tests/out con lo que dice la teoría. Sale con código 1 si algo falla."""
import numpy as np, soundfile as sf, pathlib, sys
D = pathlib.Path(__file__).parent / "out"; S = pathlib.Path(__file__).parent / "signals"; SR = 48000
def a(db): return 10 ** (db / 20)
def db(x): return 20 * np.log10(np.abs(x) + 1e-15)
def load(name):
    x, sr = sf.read(D / f"{name}.wav"); assert sr == SR; return x
def tone(name, f, t0=1.0, t1=1.9, ch=0, x=None):
    """amplitud (dBFS) de un seno de frecuencia f (ajuste por mínimos cuadrados)"""
    x = load(name)[:, ch] if x is None else x
    seg = x[int(t0 * SR):int(t1 * SR)]; tt = np.arange(int(t0 * SR), int(t1 * SR)) / SR
    M = np.stack([np.sin(2 * np.pi * f * tt), np.cos(2 * np.pi * f * tt)], 1)
    c, *_ = np.linalg.lstsq(M, seg, rcond=None); return db(np.hypot(*c))
def env(x, ms=1.0):
    """envolvente (Hilbert) promediada por ms"""
    from scipy.signal import hilbert
    e = np.abs(hilbert(x)); n = int(SR * ms / 1000); m = len(e) // n; return e[:m * n].reshape(m, n).mean(1)

fails = 0
def scalar(name, got, want, tol):
    global fails
    ok = abs(got - want) <= tol; fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:34s} {got:+8.2f}   (esperado {want:+.2f} ± {tol})")
def inrange(name, got, lo, hi):
    global fails
    ok = lo <= got <= hi; fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:34s} {got:+8.2f}   (entre {lo:+.2f} y {hi:+.2f})")

def w4(f, fc): return (np.tan(np.pi * f / SR) / np.tan(np.pi * fc / SR)) ** 4   # con la deformación bilineal
def partida(f, g, f1=5000): w = w4(f, f1); return db((1 + g * w) / (1 + w))
def banda(f, g, f1=5000, f2=10000):
    w1, w2 = w4(f, f1), w4(f, f2); return db((1 + w2 + g * w1 + w1 * w2) / ((1 + w1) * (1 + w2)))
def gcomp(L, T, R, W=4):
    o = L - T; s = 1 - 1 / R
    return 0 if 2 * o <= -W else s * (o + W / 2) ** 2 / (2 * W) if 2 * o < W else s * o
HP8 = db(w4(8000, 5000) / (1 + w4(8000, 5000)))     # nivel de 8 kHz en la zona (LR4 desde 5 kHz)

for p in sorted(q for q in D.glob("*.wav") if not q.stem.startswith("perf_")):
    x = load(p.stem)
    if not np.all(np.isfinite(x)) or np.abs(x).max() > 4:
        fails += 1; print("MAL", p.stem, "tiene NaN o pasa de +12 dBFS")

g10 = a(-10)
scalar("relativa: 1 kHz (voz) intacto", tone("rel_1k", 1000), -6, 0.05)
scalar("relativa: 8 kHz baja el rango", tone("rel_8k", 8000), -6 + partida(8000, g10), 0.1)
scalar("relativa: 8 kHz a -30 baja igual", tone("rel_8k_m30", 8000), -30 + partida(8000, g10), 0.1)
gA = gcomp(-6 + HP8, -20, 4)
scalar("absoluta: curva (umbral -20, 4:1)", tone("abs_8k", 8000), -6 + partida(8000, a(-gA)), 0.2)
scalar("absoluta: bajo el umbral intacto", tone("abs_8k_m30", 8000), -30, 0.05)
scalar("absoluta: ratio 2", tone("abs_ratio2", 8000), -6 + partida(8000, a(-gcomp(-6 + HP8, -20, 2))), 0.2)

imp = np.zeros(SR); imp[SR // 2] = 0.5
for m in ("partida", "banda", "ancha"):
    y = load(f"flat_{m}")[:SR, 0]
    H = np.abs(np.fft.rfft(y)) / np.abs(np.fft.rfft(imp)); f = np.fft.rfftfreq(SR, 1 / SR)
    dev = np.abs(db(H[(f > 20) & (f < 20000)])).max()
    scalar(f"plano sin reducir ({m})", dev, 0, 0.05)

scalar("partida: 8 kHz baja", tone("partida_15k", 8000), -6 + partida(8000, g10), 0.15)
scalar("partida: 15 kHz baja", tone("partida_15k", 15000), -6 + partida(15000, g10), 0.15)
scalar("banda 5-10k: 8 kHz baja", tone("banda_15k", 8000), -6 + banda(8000, g10), 0.15)
scalar("banda 5-10k: 15 kHz casi intacto", tone("banda_15k", 15000), -6 + banda(15000, g10), 0.15)
r1, r8 = -6 - tone("ancha_1k8k", 1000), -12 - tone("ancha_1k8k", 8000)
inrange("ancha: baja 1 kHz", r1, 2, 6)
scalar("ancha: 1k y 8k bajan igual", r1 - r8, 0, 0.2)
scalar("partida: 1 kHz intacto con s", tone("partida_1k8k", 1000), -6, 0.1)
inrange("partida: 8 kHz baja", -12 - tone("partida_1k8k", 8000), 2, 6)
inrange("escuchar s: 1 kHz casi nada", tone("listen_det_1k", 1000), -200, -50)
scalar("escuchar s: 8 kHz", tone("listen_det_8k", 8000), -6 + HP8, 0.1)
scalar("escuchar cambios: 8 kHz", tone("delta_8k", 8000), -6 + HP8 + db(1 - g10), 0.15)
scalar("solo centro: baja", tone("solo_mid", 8000), -6 + partida(8000, g10), 0.1)
scalar("solo lados: intacto (mono)", tone("solo_side", 8000), -6, 0.05)
scalar("enlace 100 % R", tone("link100", 8000, ch=1), -30 + partida(8000, a(-gA)), 0.2)
scalar("enlace 0 % R", tone("link0", 8000, ch=1), -30, 0.05)
scalar("enlace 0 % L", tone("link0", 8000, ch=0), -6 + partida(8000, a(-gA)), 0.2)
scalar("salida +6", tone("salida6", 1000), 0, 0.05)

# tiempos (modo Ancha: la atenuación = la ganancia)
ins, _ = sf.read(S / "step8k.wav")
g = db(env(ins[:, 0]) / np.maximum(env(load("timing")[:, 0]), 1e-9))
gt = gcomp(-10 + HP8, -30, 4)
print("    GR tras el escalón: " + " ".join(f"{t}ms:{g[1000 + t]:.1f}" for t in (1, 3, 5, 10, 20)) + f"   (meta {gt:.2f})")
inrange("ataque 5 ms (GR a 5 ms)", g[1005], gt * (1 - np.exp(-1)) - 3, gt * (1 - np.exp(-1)) + 2)
scalar("GR sostenida", g[1800], gt, 0.3)
print("    GR tras bajar:      " + " ".join(f"{t}ms:{g[2000 + t]:.1f}" for t in (10, 50, 100, 200)))
inrange("release 100 ms (GR a 100 ms)", g[2100], gt * np.exp(-1) - 1.5, gt * np.exp(-1) + 1.5)

for name in ("la_off", "la_2"):
    x = load(name)[:, 0]; on = np.argmax(np.abs(x) > 1e-4)
    print(f"    {name}: arranca en la muestra {on} (debe ser ~48000)")
    if abs(on - 48000) > 3: fails += 1; print("MAL", name, "desalineado: la latencia no se compensó")
p0 = db(np.abs(load("la_off")[48000:48048, 0]).max()); p2 = db(np.abs(load("la_2")[48000:48048, 0]).max())
print(f"    pico del primer ms: sin lookahead {p0:.1f}, con 2 ms {p2:.1f}")
inrange("lookahead agarra el inicio (dB menos)", p0 - p2, 4, 20)
scalar("lookahead: el inicio ya llega bajado", p2, -16, 0.5)

# voz real: bandas por cuadros de 10 ms
from scipy import signal as sg
LO = sg.butter(4, 3000, "low", fs=SR, output="sos"); HI = sg.butter(4, 5500, "high", fs=SR, output="sos")
def frames(x, sos):
    y = sg.sosfilt(sos, x.mean(1)); n = SR // 100; m = len(y) // n
    return 10 * np.log10(np.mean(y[:m * n].reshape(m, n) ** 2, 1) + 1e-20)
def voz_stats(proc, seca, hi=HI):
    s_lo, s_hi = frames(load(seca), LO), frames(load(seca), hi)
    p_lo, p_hi = frames(load(proc), LO), frames(load(proc), hi)
    loud = s_lo.clip(-200) > s_lo.max() - 45
    ss = (s_hi > s_lo - 6) & (s_hi > s_hi.max() - 40)            # cuadros de s
    vv = loud & (s_hi < s_lo - 25)                                 # vocales
    return ss.sum(), np.median(s_hi[ss] - p_hi[ss]), np.median(np.abs(s_lo[vv] - p_lo[vv])), np.median(np.abs(s_hi[vv] - p_hi[vv]))
n, rs, rv_lo, rv_hi = voz_stats("voz_normal", "voz_seca")
print(f"    voz: {n} cuadros de s, bajan {rs:.1f} dB; vocales cambian {rv_lo:.2f} dB (graves) / {rv_hi:.2f} dB (agudos)")
inrange("voz: las s bajan (mediana)", rs, 3, 12)
inrange("voz: vocales intactas (graves)", rv_lo, 0, 0.1)
inrange("voz: vocales casi intactas (agudos)", rv_hi, 0, 1.0)
n2, rs2, _, _ = voz_stats("voz_m20", "voz_m20_seca")
scalar("voz -20 dB: las s bajan igual", rs2, rs, 1.0)
for p in range(1, 11):
    _, r, rlo, _ = voz_stats(f"preset{p}", "voz_seca", sg.butter(4, [4000, 6000], "band", fs=SR, output="sos") if p == 6 else HI)
    if p == 8: inrange(f"preset {p} (hi-hats): no rompe la voz", rlo, 0, 0.5)
    else: inrange(f"preset {p}: baja las s", r, 1, 18)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
