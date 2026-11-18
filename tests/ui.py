"""Ayudante para probar la interfaz con cliclick (ventana del FX en su posición/tamaño por defecto)."""
import subprocess, time, pathlib, re, math
WX, WY = 26, 66 + 53            # esquina del área gráfica del FX (puntos), bajo la cabecera de REAPER
ROOT = pathlib.Path(__file__).resolve().parent.parent
def pt(x, y): return f"{round(WX + x)},{round(WY + y)}"
def cc(*args): subprocess.run(["cliclick", "-w", "60", *args], check=True); time.sleep(0.4)
def wheel(n): subprocess.run(["swift", str(ROOT / "tests/scroll.swift"), str(n)], check=True); time.sleep(0.4)
def shot(path): subprocess.run(["screencapture", "-x", "-R26,66,1000,693", path], check=True); return path
def dump():
    p = ROOT / "tests/out/dump.txt"; p.unlink(missing_ok=True)
    subprocess.Popen(["/Applications/REAPER.app/Contents/MacOS/REAPER", "-nonewinst", str(ROOT / "tests/ui_dump.lua")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if p.exists() and "done" in p.read_text(): return p.read_text().replace("done\n", "")
        time.sleep(0.25)
    return "(sin respuesta)"
def param(n):
    """valor formateado del slider n"""
    m = re.search(rf"^{n} (.*)$", dump(), re.M); return m.group(1).rsplit(" = ", 1)[1] if m else None
def num(s): return float(s.split()[0]) if s else float("nan")
def drag(x0, y0, x1, y1, steps=8):
    # primero llevar el mouse y esperar unos cuadros: si se aprieta en el mismo instante, el JSFX todavia tiene la
    # posicion anterior (p. ej. la del doble clic de antes) y agarra otro control
    cc(f"m:{pt(x0, y0)}"); time.sleep(0.3)
    cc(f"dd:{pt(x0, y0)}")
    for k in range(1, steps + 1): cc(f"m:{pt(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps)}")
    cc(f"du:{pt(x1, y1)}"); cc(f"du:{pt(x1, y1)}")             # soltar extra: ver dclick
def dclick(x, y):
    """doble clic + un 'soltar' extra en el mismo punto: con los clics sinteticos de cliclick, a veces REAPER no le
    entrega al JSFX el ultimo 'soltar' y mouse_cap queda en 1 (el arrastre siguiente se pierde o mueve otro control).
    Si no quedo pegado, el soltar extra no hace nada (no hay clic nuevo ni movimiento)."""
    cc(f"dc:{pt(x, y)}"); cc(f"du:{pt(x, y)}")
# layout (ventana 1000x640): dy = 54, dh = 400, py = 464
PY = 464
MODE = lambda k: (14 + 46 + k * 80 + 38, PY + 20)      # 4 botones de 76 (Partida, Banda, Ancha, Forma)
KNOB = lambda i: (56 + i * 86, PY + 92)
SMALL = lambda i: (582 + i * 76, PY + 92)
LISTEN_S, LISTEN_D = (788, PY + 20), (921, PY + 20)
PRESETS = (208, 22)
MENU_ITEM = lambda k: (300, 37.5 + 24 * k)                  # item k del menu de presets abierto desde el boton
FW = min(400 * 1.3, (1000 - 96 - 90) * 0.42); FX0 = 1000 - 14 - 96 - 16 - FW
f2x = lambda f: FX0 + FW * math.log(f / 700) / math.log(20000 / 700)
HIST = (40 + (FX0 - 16 - 40) / 2, 54 + 200)
