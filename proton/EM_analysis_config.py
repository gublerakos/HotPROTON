import os


HERE = os.path.dirname(os.path.abspath(__file__))
HOTPROTON_ROOT = os.path.dirname(HERE)
POWERGRIDS_DIR = os.path.abspath(os.path.expanduser(os.environ.get(
    "HOTPROTON_POWERGRIDS_DIR",
    os.path.join(HOTPROTON_ROOT, "benchmarks", "powergrids"),
)))

# project parameters
project_name = "test_project"
spice_file = os.path.abspath(os.path.expanduser(os.environ.get(
    "HOTPROTON_SPICE_FILE",
    os.path.join(POWERGRIDS_DIR, "C_0_T3_b.spice"),
)))
folder_path = POWERGRIDS_DIR
results_dir = os.path.join(os.path.abspath(os.path.expanduser(os.environ.get(
    "HOTPROTON_EM_RESULTS_DIR",
    os.path.join(HOTPROTON_ROOT, "results", "hotproton_em_runs"),
))), "")

# parameters for the EM analysis
set_line = 'M1_n1_16'
set_points = 1000
set_technology = 'CuDD'
set_temperature = float(338)
set_width = float(0.1)  # um

# set this to true if you want to run EM analysis for a directory
directory = 0
rows = 20
columns = 43
