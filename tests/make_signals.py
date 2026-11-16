"""Señales de prueba (48 kHz, float32)."""
import numpy as np, soundfile as sf, pathlib
D = pathlib.Path(__file__).parent / "signals"; D.mkdir(exist_ok=True)
SR = 48000
def a(db): return 10 ** (db / 20)
def save(name, *ch): sf.write(D / name, np.stack(ch, 1).astype(np.float32), SR, subtype="FLOAT")
n = SR * 2; t = np.arange(n) / SR
s = lambda f, db, tt=t: a(db) * np.sin(2 * np.pi * f * tt)
save("s1k_m6.wav", s(1000, -6), s(1000, -6))
save("s8k_m6.wav", s(8000, -6), s(8000, -6))
save("s8k_m30.wav", s(8000, -30), s(8000, -30))
save("s8k_15k.wav", s(8000, -6) + s(15000, -6), s(8000, -6) + s(15000, -6))
save("s1k_8k.wav", s(1000, -6) + s(8000, -12), s(1000, -6) + s(8000, -12))
save("lr8k.wav", s(8000, -6), s(8000, -30))
# impulso (respuesta en frecuencia)
imp = np.zeros(n); imp[SR // 2] = 0.5; save("impulse.wav", imp, imp)
# escalon en 8 kHz: -40 dBFS 0-1 s, -10 dBFS 1-2 s, -40 dBFS 2-3 s
t3 = np.arange(SR * 3) / SR
lv = np.where((t3 >= 1) & (t3 < 2), a(-10), a(-40))
st = lv * np.sin(2 * np.pi * 8000 * t3); save("step8k.wav", st, st)
# rafaga 8 kHz desde 1.0 s (lookahead)
b = np.zeros(n); i0 = SR; b[i0:] = a(-6) * np.cos(2 * np.pi * 8000 * (t[i0:] - 1.0)); save("burst8k.wav", b, b)
print("ok", sorted(p.name for p in D.iterdir()))
# voz seca real (de las demos de Nube Verb) para la prueba de voz
import shutil
v = pathlib.Path.home() / "Music/NubeVerb/demos/0 - seca.wav"
if v.exists():
    x, sr = sf.read(v)
    print("voz", sr, x.shape)
    if sr == SR: shutil.copy(v, D / "voz.wav")
