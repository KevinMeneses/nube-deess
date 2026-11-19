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
for p in range(1, 19):
    zona = {6: [4000, 6000], 14: [5000, 10000], 16: [3000, 8000]}.get(p)   # presets de banda: se mide en su zona
    _, r, rlo, _ = voz_stats(f"preset{p}", "voz_seca", sg.butter(4, zona, "band", fs=SR, output="sos") if zona else HI)
    if p in (8, 17, 18): inrange(f"preset {p} (no es para voz): no rompe la voz", rlo, 0, 0.5)
    else: inrange(f"preset {p}: baja las s", r, 1, 18)

print("== presets y ajustes de la 1.1.0 suenan igual en la 1.2.0")
def null(a, b): return db(np.abs(load(a) - load(b)).max())
for p in range(1, 20):
    q = 26 if p == 19 else p                       # "Por defecto" paso del 19 al 26
    inrange(f"preset {p} = 1.1.0 (dB de diferencia)", null(f"preset{q}", f"ref_preset{p}"), -999, -140)
inrange("ajustes de Nube baja = 1.1.0", null("old_proj_nd", "old_proj_ref"), -999, -140)
inrange("banda + M/S + lookahead = 1.1.0", null("old_msla_nd", "old_msla_ref"), -999, -140)

print("== comparado con claude_deesser_lr (el relativo original)")
for c in ("lr", "lr_suave"):
    _, ro, vo, _ = voz_stats(f"{c}_ref", "voz_seca"); _, rn, vn, _ = voz_stats(f"{c}_nd", "voz_seca")
    print(f"    {c}: s bajan {ro:.1f} dB (original) / {rn:.1f} dB (Nube); vocales {vo:.2f} / {vn:.2f} dB")
    # diferencia conocida: el original detecta con envolvente de pico (0.5 / 40 ms), Nube con RMS de 1.5 ms
    inrange(f"{c}: diferencia con el original (dB)", rn - ro, -3.5, 1)
    inrange(f"{c}: vocales intactas en Nube", vn, 0, 0.05)

print("== modo Forma de las s")
for c, src in (("shaper", "voz"), ("shaperbaja", "voz"), ("shaper45", "s45_m12")):
    inrange(f"{c}: Nube De-Ess = claude_s_shaper (dB)", null(f"eq_{c}_nd", f"eq_{c}_ref"), -999, -120)
    x = sf.read(S / f"{src}.wav")[0]
    inrange(f"{c}: el original si cambia el audio (dB)", db(np.abs(load(f"eq_{c}_ref") - x).max()), -60, 20)
from scipy.signal import freqz
def rbj_bp(f, q):
    w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q); a0 = 1 + al
    return [al / a0, 0, -al / a0], [1, -2 * np.cos(w) / a0, (1 - al) / a0]
def rbj_hp(f):
    w = 2 * np.pi * f / SR; c = np.cos(w); al = np.sin(w) / (2 * 0.70710678); a0 = 1 + al
    return [(1 + c) / 2 / a0, -(1 + c) / a0, (1 + c) / 2 / a0], [1, -2 * c / a0, (1 - al) / a0]
def mag(ba, f): return np.abs(freqz(*ba, worN=[f], fs=SR)[1][0])
def forma_cut(f, f0=4500, q=1, thr=6, amt=0.6, mx=8, det=-12):
    """dB que baja un seno de frecuencia f = f0 (centro de la campana) en estado estable. Como en el original,
    mientras corta el detector de la campana usa b0 = a0 de la campana: se busca el punto fijo."""
    r = f0 / 4500
    is_s = db(mag(rbj_hp(4000 * r), f) / mag(rbj_bp(2000, 0.7), f)) > det
    tilt = db(mag(rbj_bp(4500 * r, 1.4), f) / mag(rbj_bp(7700 * r, 1.6), f))
    if not (is_s and tilt > thr): return 0
    w = 2 * np.pi * 4500 * r / SR; b0 = np.sin(w) / 2.8 / (1 + np.sin(w) / 2.8); alq = np.sin(2 * np.pi * f0 / SR) / (2 * q)
    c = min(mx, (tilt - thr) * amt)
    for _ in range(200):
        a0 = 1 + alq / 10 ** (-c / 40)
        c = min(mx, (tilt + db(a0 / b0) - thr) * amt)
    return c
c45 = forma_cut(4500)
print(f"    4.5 kHz: teoria baja {c45:.2f} dB")
scalar("forma: 4.5 kHz baja (defecto)", tone("fo_45", 4500), -12 - c45, 0.3)
scalar("forma: cuanto 0.1 (punto fijo)", tone("fo_45_poco", 4500), -12 - forma_cut(4500, amt=0.1), 0.3)
scalar("forma: corte maximo 3", tone("fo_45_max3", 4500), -12 - forma_cut(4500, mx=3), 0.3)
scalar("forma: Q 2", tone("fo_45_q2", 4500), -12 - forma_cut(4500, q=2), 0.3)
scalar("forma: 3.8 kHz (las zonas siguen)", tone("fo_38", 3800), -12 - forma_cut(3800, f0=3800), 0.3)
scalar("forma: campana en 8 kHz", tone("fo_8k", 8000), -6 - forma_cut(8000, f0=8000), 0.3)
inrange("forma: campana en 8 kHz si baja", -6 - tone("fo_8k", 8000), 1, 20)
scalar("forma: 8 kHz con la campana en 4.5 (no la toca)", tone("fo_8k_off", 8000), -6 - forma_cut(8000), 0.3)
inrange("forma: 1 kHz (vocal) intacto tras 50 ms", db(np.abs(load("fo_1k") - sf.read(S / "s1k_m6.wav")[0])[SR // 20:].max()), -999, -140)
inrange("forma: sin s (deteccion 10) intacto", db(np.abs(load("fo_sin_s") - sf.read(S / "s45_m12.wav")[0])[SR // 20:].max()), -999, -140)
nz = sf.read(S / "noise.wav")[0][:, 0]; yn = load("fo_ruido")[:, 0]
dn = db(np.sqrt(np.mean((yn - nz) ** 2)) / np.sqrt(np.mean(nz ** 2)))
inrange("forma: s pareja (ruido) casi intacta (dB)", dn, -999, -30)
scalar("forma: solo centro baja", tone("fo_solo_mid", 4500), -12 - c45, 0.3)
inrange("forma: solo lados intacto (mono)", db(np.abs(load("fo_solo_side") - sf.read(S / "s45_m12.wav")[0])[SR // 20:].max()), -999, -140)
scalar("forma: L/R distintos, L", tone("fo_lr", 4500, ch=0), -12 - c45, 0.3)
scalar("forma: L/R distintos, R", tone("fo_lr", 4500, ch=1), -30 - c45, 0.3)
scalar("forma: M/S = estereo (R)", tone("fo_ms", 4500, ch=1), tone("fo_lr", 4500, ch=1), 0.01)
scalar("forma: escuchar s (campana)", tone("fo_escuchar", 4500), -12, 0.05)
scalar("forma: escuchar cambios", tone("fo_delta", 4500), -12 + db(1 - a(-c45)), 0.3)
scalar("forma: salida +6", tone("fo_salida", 4500), -6 - c45, 0.3)
for name in ("fo_la_off", "fo_la_2"):
    x = load(name)[:, 0]; on = np.argmax(np.abs(x) > 1e-4)
    print(f"    {name}: arranca en la muestra {on} (debe ser ~48000)")
    if abs(on - 48000) > 3: fails += 1; print("MAL", name, "desalineado: la latencia no se compenso")
p0 = db(np.abs(load("fo_la_off")[48000:48096, 0]).max()); p2 = db(np.abs(load("fo_la_2")[48000:48096, 0]).max())
print(f"    pico de los 2 primeros ms: sin lookahead {p0:.1f}, con 2 ms {p2:.1f}")
inrange("forma: lookahead agarra el inicio (dB menos)", p0 - p2, 0.5, 20)
HS = sg.butter(4, [4000, 5500], "band", fs=SR, output="sos")
n, rs, rv_lo, rv_hi = voz_stats("eq_shaperbaja_nd", "voz_seca", HS)
print(f"    voz (Forma Nube baja): {n} cuadros de s, 4-5.5 kHz bajan {rs:.2f} dB; vocales {rv_lo:.2f} / {rv_hi:.2f} dB")
inrange("forma voz: las s bajan en 4-5.5 kHz", rs, 0.3, 8)
inrange("forma voz: vocales intactas (graves)", rv_lo, 0, 0.05)
_, rs2, _, _ = voz_stats("fo_voz_m20", "voz_m20_seca", HS)
scalar("forma voz -20 dB: bajan igual", rs2, rs, 0.5)
for p in range(19, 26):
    zona = {24: [3200, 4500], 25: [6000, 8500]}.get(p, [4000, 5500])   # se mide en la zona de cada campana
    _, r, rlo, rhi = voz_stats(f"preset{p}", "voz_seca", sg.butter(4, zona, "band", fs=SR, output="sos"))
    print(f"    preset {p}: en la zona, s {r:.2f} dB / vocales {rhi:.2f} dB")
    if p == 25:   # solo para pocas s muy silbadas en ~7 kHz (la voz de prueba no las tiene): se prueba con un seno
        c7 = forma_cut(7073, f0=7073, q=2.81, thr=7, amt=0.55, mx=18, det=3.4)
        print(f"    preset 25: teoria baja {c7:.2f} dB un seno de 7 kHz")
        scalar("preset 25 (forma): s silbada en 7 kHz baja", tone("fo_p25_7k", 7073), -12 - c7, 0.3)
        inrange("preset 25 (forma): y baja de verdad", c7, 3, 18)
    else: inrange(f"preset {p} (forma): baja las s", r, 1, 12)
    inrange(f"preset {p} (forma): vocales intactas en la zona", rhi, 0, 0.3)
    inrange(f"preset {p} (forma): graves intactos", rlo, 0, 0.1)
print("\nFALLAS:", fails)
sys.exit(1 if fails else 0)
