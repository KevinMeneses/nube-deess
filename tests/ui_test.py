"""Pruebas de la interfaz con el mouse. Requiere la demo abierta (tests/reopen.sh) y la ventana del FX al frente."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ui import *
OUT = os.environ.get("NUBE_SHOTS", str(ROOT / "tests/out"))
fails = 0
def check(name, got, want):
    global fails
    ok = (want(got) if callable(want) else got == want); fails += not ok
    print(f"{'OK ' if ok else 'MAL'} {name:44s} {got!r}")

subprocess.run(["osascript", "-e", 'tell application "REAPER" to activate']); time.sleep(0.6)
cc(f"c:{pt(500, 5)}")                                       # foco en la ventana del FX
check("arranca con preset 2 (umbral -10)", num(param(1)), -10.0)
cc(f"c:{pt(*MODE(1))}"); check("clic en Banda", param(11), lambda v: v.startswith("Banda"))
cc(f"c:{pt(*MODE(0))}"); check("clic en Partida", param(11), lambda v: v.startswith("Partida"))
x, y = KNOB(0); drag(x, y, x, y - 50)
check("arrastrar Umbral hacia arriba sube", num(param(1)), lambda v: v > -5)
cc(f"dc:{pt(x, y)}"); check("doble clic en Umbral = -10", num(param(1)), -10.0)
x, y = KNOB(1); cc(f"m:{pt(x, y)}"); r0 = num(param(2)); wheel(5)
check("rueda sobre Rango sube", num(param(2)), lambda v: v > r0 + 0.5)
x, y = SMALL(1); drag(x, y, x, y - 40)
check("arrastrar Release (perilla chica) sube", num(param(7)), lambda v: v > 60)
d0 = num(param(4)); x = f2x(5000); drag(x, 54 + 200, x + 40, 54 + 200)
check("arrastrar la linea Desde a la derecha", num(param(4)), lambda v: v > 6000)
x = FX0 + FW - 3; drag(x, 54 + 200, x - 60, 54 + 200)
check("arrastrar Hasta a la izquierda (con limite)", num(param(5)), lambda v: v < 16000)
cc(f"dc:{pt(x - 60, 54 + 200)}"); check("doble clic en Hasta = sin limite", num(param(5)), 20000.0)
u0 = num(param(1)); drag(*HIST, HIST[0], HIST[1] - 60)
check("arrastrar en el historial sube el umbral", num(param(1)), lambda v: v > u0 + 5)
cc(f"c:{pt(*LISTEN_S)}"); check("Escuchar s", param(14), lambda v: v.startswith("Solo las s"))
shot(f"{OUT}/ui_escuchar_s.png")
cc(f"c:{pt(*LISTEN_D)}"); check("Escuchar cambios", param(14), lambda v: v.startswith("Solo lo que"))
cc(f"c:{pt(*LISTEN_D)}"); check("Escuchar cambios apagado", param(14), "Normal")
cc(f"c:{pt(*MODE(1))}"); time.sleep(1.5); shot(f"{OUT}/ui_banda.png")
cc(f"c:{pt(*PRESETS)}"); time.sleep(0.6); cc("kp:arrow-down", "kp:return")
check("menu Presets -> Voz - suave (umbral -7)", (num(param(1)), param(11)[:7]), (-7.0, "Partida"))
print("FALLAS:", fails)
sys.exit(1 if fails else 0)
