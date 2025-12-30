import subprocess
import os

SUMO_GUI = r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE_DIR, "run.sumocfg")

print(" Starting SUMO replay...")
print("Using SUMO:", SUMO_GUI)
print("Config:", CFG)

subprocess.Popen([
    SUMO_GUI,
    "-c", CFG,
    "--start",
    "--delay", "100"
])

