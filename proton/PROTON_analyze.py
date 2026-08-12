from __future__ import unicode_literals
import csv
import os
import sys

import io
import re
import shutil
import time
import math
import importlib
import config

from config import SNIPER, BENCHMARKS_FOLDER
sys.path.append(SNIPER)

PROTON_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(PROTON_PATH)

from classes import matrix_formulation_func_cli
from proton.classes.analytical_class_cli import *
from proton.classes.spice_function_cli import *
from proton.classes import spice_function_cli
from proton.PROTON_analyze_functions import *
from proton.powergrid_mapping import process_files
from proton import EM_analysis_config

from pggen.pg_gen import DataStore
from hotproton_debug import get_logger


logger = get_logger(__name__)
logger.debug("PROTON path: %s", PROTON_PATH)

failed_subcores = set()

# Custom class to write to both terminal and buffer
class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        elif not isinstance(data, str):
            data = str(data)
        for stream in self.streams:
            stream.write(data)
        for stream in self.streams:
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()

class redirect_stdout(object):
    def __init__(self, new_target):
        self.new_target = new_target
        self.old_target = None

    def __enter__(self):
        self.old_target = sys.stdout
        sys.stdout = self.new_target
        return self.new_target

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.old_target

def initialize(spice_file, results_dir, tech, temp, width, core_name):
    """
    Initializes the project setup, parses the power grid, initializes item paths,
    and formulates the matrix.

    Args:
        spice_file (str): The path to the SPICE file.
        results_dir (str): Directory where the results will be saved.
        tech (str): Technology parameter for matrix formulation.
        temp (float): Temperature parameter for matrix formulation.
        width (float): Width parameter for matrix formulation.

    Returns:
        list: A list of item paths generated during initialization.
    """

    DataStore.line_temperatures = {}
    
    # Setup the project
    set_powergrid(spice_file)
    set_project_path(results_dir)
    project_name = "stress_" + os.path.splitext(os.path.basename(spice_file))[0]
    set_project_name(project_name)

    # Parse the power grid
    parse_powergrid(response=None)

    # Initialize item paths
    stack = [(spice_function_cli.benchmark, "")]
    all_lines = []

    # Get the total number of lines
    lines_num = get_num_lines(spice_function_cli.benchmark)
          
    while stack:
        current_path, indent = stack.pop(0)
        sorted_files = sorted(os.listdir(current_path), key=extract_numbers)

        for item in sorted_files:
            item_path = os.path.join(current_path, item)
            if os.path.isdir(item_path):
                stack.append((item_path, indent + "  "))
            elif os.path.isfile(item_path):
                all_lines.append(item_path)

    set_line_width(width)
    # Formulate the matrix
    points = 100
    for item_path in all_lines:
        # Construct the corresponding CSV path
        subdir = os.path.splitext(os.path.basename(spice_file))[0]
        csv_path = os.path.join(results_dir, project_name, subdir, "M1", os.path.basename(item_path))
        max_temp = temp  # fallback if nothing found

        if os.path.exists(csv_path):
            subcore_temps = []

            with open(csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    segment = row['segment_name']
                    match = re.match(r"RR?_([A-Za-z0-9]+)_", segment)
                    if match:
                        subcore = match.group(1)
                        subcore_entries = DataStore.core_data.get(core_name, [])
                        temps = [entry['temperature'] for entry in subcore_entries if entry['name'] == subcore and entry['temperature'] is not None]
                        subcore_temps.extend(temps)

            if subcore_temps:
                max_temp = max(subcore_temps)
                
        line_name = os.path.splitext(os.path.basename(item_path))[0]
        DataStore.line_temperatures[line_name] = (max_temp + 273.15)
        directory = results_dir + project_name
        matrix_formulation_worker = Matrix_Formulation_Class(
            csv_file=item_path,
            project_location=directory,
            sp_step=None,
            given_disc_point=points,
            technology=tech,
            temperature=(float(max_temp) + 273.15),
            givenWidth=float(width),
        )
        return_message = matrix_formulation_worker.matrix_formulation()
    return lines_num


def report_max_stress(simulation_time, spice_file, results_dir, line_width, critical_stress, lines_num, seconds, first_time):
    """
    Reports the maximum stress from the analysis, logs it to a file, and returns the maximum stress value.

    Args:
        spice_file (str): The path to the SPICE file.
        results_dir (str): Directory where the results will be saved.
        line_width (float): Line width for the analysis.
        critical_stress (float): The critical stress value to compare against.

    Returns:
        float: The maximum stress value found in the analysis.
    """
    # Run the analysis and capture its output
    sim_time = simulation_time  # Simulation time in seconds
    crit_stress = critical_stress  # Critical stress

    # Set up the buffer and the Tee
    output_buffer = io.StringIO()
    tee = Tee(sys.stdout, output_buffer)
    # Redirect stdout to Tee (which writes to both terminal and buffer)
    
    with redirect_stdout(tee):
        analyze_powergrid(sim_time, lines_num, seconds = seconds, first_time = first_time, critical_stress=crit_stress)  # Run the analysis

    # Capture the output from the buffer
    analyze_output = output_buffer.getvalue()
    
    max_stress_line = next((line for line in analyze_output.splitlines() if "Maximum stress found at line" in line), None)
    if max_stress_line:
        print("Analysis result: {}".format(max_stress_line))

        # Extract the maximum stress value using regex
        match = re.search(r"Maximum stress found at line .+ with value ([\d\.e\-]+) Pa", max_stress_line)
        if match:
            max_stress_value = float(match.group(1))  # Extracted max stress value as float
            return max_stress_value
    else:
        print("No stress data found during analysis.")
        return None

def TTF_calculation_bisection(spice_file, results_dir, line_width, critical_stress, all_lines, seconds):
    """
    TTF calculation using the bisection method with selective caching.

    Args:
        spice_file (str): The path to the SPICE file.
        results_dir (str): Directory where the results will be saved.
        line_width (float): Line width for the analysis.
        critical_stress (float): The critical stress value to compare against.

    Returns:
        float: The estimated time to failure (TTF).
    """
    year = 3.1536e7  # Number of seconds in one year
    a = 1            # Left bound of the interval (start at year 0)
    b = 20 * year    # Right bound of the interval (start at 20 years)
    tol_bisection = 1e-6  # Tolerance for the bisection method
    max_iter_bisection = 100  # Maximum number of bisection iterations
    logger.debug(
        "Initial bisection bounds: a=%s years, b=%s years",
        a / year,
        b / year,
    )
    # Compute initial f(a) and f(b)
    f_b = f_bi(seconds, spice_file, results_dir, line_width, critical_stress, all_lines, seconds, False)
    f_a = f_bi(a, spice_file, results_dir, line_width, critical_stress, all_lines, seconds, True)
    logger.debug("Initial bisection values: f(a)=%s, f(b)=%s", f_a, f_b)

    # Bisection Method
    for i in range(max_iter_bisection):
        c = (a + b) / 2  # Midpoint
        f_c = f_bi(c, spice_file, results_dir, line_width, critical_stress, all_lines, seconds, False)
        logger.debug(
            "Bisection iteration %s: c=%s years, f(c)=%s",
            i + 1,
            c / year,
            f_c,
        )

        # Check if the root is found or the interval is small enough
        if abs(f_c) < tol_bisection or (b - a) / 2 < tol_bisection:
            print("Converged at iteration {}: Tolerance met, TTF = {} years".format((i+1), (c/year)))
            break

        # Update interval and selectively reuse values
        if f_a * f_c < 0:
            b = c
            # f_b = f_c  # Store f(c) as the new f(b)
        else:
            a = c
            f_a = f_c  # Store f(c) as the new f(a)

        logger.debug(
            "Updated bisection bounds: a=%s years, b=%s years; f(a)=%s, f(b)=%s",
            a / year,
            b / year,
            f_a,
            f_b,
        )

    t_nucl = c
    logger.debug("Calculated TTF: %s years", t_nucl / year)
    return t_nucl

def f_bi(t, spice_file, results_dir, line_width, critical_stress, all_lines, seconds, first_time):
    """
    Function to evaluate the bisection method.
    
    Args:
        t (float): The current time being evaluated.
        spice_file (str): The path to the SPICE file.
        results_dir (str): Directory where the results will be saved.
        line_width (float): Line width for the analysis.
        critical_stress (float): The critical stress value to compare against.
        max_stress (float): The maximum stress value found during analysis.
    
    Returns:
        float: The difference between the calculated stress and the critical stress.
    """
    year = 3.1536e7

    # Use the analyze method to get the stress at time t
    current_stress = report_max_stress(t, all_lines, spice_file, results_dir, line_width, critical_stress, seconds, first_time)
    
    if current_stress is None:
        return float('inf')  # Return a large number if no stress is found
    logger.debug("Stress at %s years: %s Pa", t / year, current_stress)
    # The difference between the calculated stress and the critical stress
    return current_stress - critical_stress

def get_failed_subcores(file_path):
    try:
        # Open the CSV file
        with open(file_path, mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            
            # Skip the header (if any)
            next(csv_reader, None)
            
            # Iterate through each row and extract the subcore name
            for row in csv_reader:
                if row:  # Avoid empty rows
                    segment_name = row[0]
                    # Split the segment name and check if it follows the expected pattern
                    parts = segment_name.split('_')
                    if len(parts) > 1:
                        subcore = parts[1]  # The subcore name is in the second part of the split
                        
                        # Only add the subcore if it hasn't already been added
                        failed_subcores.add(subcore)  # The set ensures no duplicates

    except Exception as e:
        print("Error reading CSV file: {}".format(e))

import os


def calculate_ttf_for_subcores(folder_path, failed_subcores, critical_stress, t_nucl):
    """
    Searches a folder for subcore names from DataStore.adjusted_subcores, and if the subcore 
    is not in failed_subcores, calculates its time to failure (TTF).

    Additionally, for subcores in failed_subcores, assigns their max stress value.

    :param folder_path: Path to the folder containing subcore stress files
    :param failed_subcores: Set of failed subcores to avoid duplicate processing
    :param critical_stress: Critical stress value
    :param t_nucl: Nucleation time for TTF calculation
    :return: Dictionary of subcore TTF values, including failed subcores with max stress values
    """
    # Ensure adjusted_subcores is not empty
    if not hasattr(DataStore, "adjusted_subcores") or not DataStore.adjusted_subcores:
        print("Error: DataStore.adjusted_subcores is empty or not defined!")
        return {}

    ttf_results = {}

    # Iterate through each subcore in the adjusted_subcores
    for subcore in DataStore.adjusted_subcores:
        subcore_name = subcore['name']

        # If subcore is in failed_subcores, assign max_stress_value and continue
        if subcore_name in failed_subcores:
            ttf_results[subcore_name] = t_nucl/0.886226925
            ttf_results[subcore_name] = 0.027777778/ttf_results[subcore_name]
            continue

        # Construct subcore file path
        subcore_file = os.path.join(folder_path, subcore_name)
        print("Looking for file:", subcore_file)

        # Check if the file exists
        if not os.path.isfile(subcore_file):
            continue

        with open(subcore_file, 'r') as f:
            lines = f.readlines()

        # Handle empty files
        if not lines:
            continue

        # Extract the single stress value from the file
        subcore_max_stress = float(lines[0].strip())
        if subcore_max_stress <= 0:
            # Non-positive tensile stress contributes no degradation during
            # this interval and must not produce a negative lifetime.
            ttf_results[subcore_name] = 0.0
            continue

        # Calculate TTF (Time to Failure)
        TTF = (critical_stress * t_nucl) / subcore_max_stress
        print("Calculated TTF for", subcore_name, ":", TTF)

        # Add TTF result to dictionary
        ttf_results[subcore_name] = TTF/0.886226925 # math.gamma(1 + 1/BETA)
        ttf_results[subcore_name] = 0.027777778/ttf_results[subcore_name]

    print("\nFinal TTF results after gamma function:", ttf_results)
    return ttf_results

import os
import math

def compute_previous_damage(r_value):
    """Recover accumulated Weibull damage from an R(t) value."""
    return math.sqrt(-math.log(r_value)) if r_value > 0 else 0.0  # Avoid log(0) issues

def save_r_ttf_values(ttf_results, core_name, output_dir):
    """
    Write instantaneous R(t) values for a core.

    If the output file does not exist, write the header (subcore names)
    and a line with the current r_t values.
    If the file exists, read the last data line (after the header), recover the
    accumulated damage, add this interval's contribution, and append R(t).
    """
    file_path = os.path.join(output_dir, "PeriodicRvalues_{}".format(core_name))
    
    # Preserve floorplan order in new files and the recorded header order in
    # existing files. Python 3.5 dictionaries do not preserve insertion order.
    floorplan_order = [
        subcore['name'] for subcore in DataStore.adjusted_subcores
        if subcore['name'] in ttf_results
    ]
    subcore_order = floorplan_order
    file_exists = os.path.exists(file_path)

    try:
        if file_exists:
            # File exists: read the last data line
            with open(file_path, "r") as f:
                lines = f.readlines()

            if not lines:
                file_exists = False
                prev_r_values = [1.0] * len(ttf_results)
            else:
                header_prefix = "{}_".format(core_name)
                subcore_order = [
                    name[len(header_prefix):] if name.startswith(header_prefix) else name
                    for name in lines[0].split()
                ]
                if set(subcore_order) != set(ttf_results):
                    raise ValueError("Subcore names differ from the existing R-value header.")

            if lines and len(lines) < 2:
                # No data line present (only header), use zeros as previous values
                prev_r_values = [1.0] * len(ttf_results)  # Assuming R(t) starts at 1
            elif lines:
                # Read last recorded R(t) values
                last_line = lines[-1].strip()
                prev_r_values = [float(val) for val in last_line.split()]
                if len(prev_r_values) != len(ttf_results):
                    raise ValueError("Mismatch between number of subcores in previous data and current data.")
        else:
            # File does not exist: start with R(t) = 1.0 (initial assumption)
            prev_r_values = [1.0] * len(ttf_results)

        previous_damage = [compute_previous_damage(r) for r in prev_r_values]

        # Calculate new summation terms and r_t values
        new_values = []
        for i, subcore in enumerate(subcore_order):
            accumulated_damage = previous_damage[i] + ttf_results[subcore]

            # Compute new R(t) value
            r_t = math.exp(-pow(accumulated_damage, 2))
            new_values.append(r_t)

        # Write to file
        with open(file_path, "a") as f:
            if not file_exists:
                # Write header if the file was just created
                subcore_names = ["{}_{}".format(core_name, subcore) for subcore in subcore_order]
                f.write(" ".join(subcore_names) + "\n")
            f.write(" ".join(map(str, new_values)) + "\n")

    except Exception as e:
        print("Error processing core {}: {}".format(core_name, e))

def PROTON_analyze(spice_file, core_name, seconds):
    # Extract the necessary parameters from the EM_analysis_config
    
    spice_file = spice_file
    # spice_file = EM_analysis_config.spice_file #FOR TESTING
    
    results_dir = EM_analysis_config.results_dir
    line_width = EM_analysis_config.set_width
    critical_stress = 330e6  # Critical stress value, modify as needed
    tech = EM_analysis_config.set_technology
    temp = EM_analysis_config.set_temperature
    
    all_lines = initialize(spice_file, results_dir, tech, temp, line_width, core_name)
    
    #Call the report_max_stress method to initialize INITIAL STRESS
    # max_stress = report_max_stress(simulation_time=seconds,
    #                                 lines_num=all_lines,
    #     							spice_file=spice_file, 
    #                                 results_dir=results_dir, 
    #                                 line_width=line_width, 
    #                                 critical_stress=critical_stress,
    #                                 seconds = seconds,
    #                                 first_time = False)
    
    # if max_stress is not None:
    #     print("The maximum stress value is: {} Pa".format(max_stress))
    # else:
    #     print("No maximum stress value found.")
    
    logger.debug("Adjusted subcores: %s", DataStore.adjusted_subcores)

    # Record the start time
    start_time = time.time()
    # Capture printed output
    old_stdout = sys.stdout
    log_output = io.StringIO()
    sys.stdout = Tee(sys.stdout, log_output)
    print("SECONDS = {}".format(seconds))
    try:
        # Call the function and capture its printed output
        t_nucl = TTF_calculation_bisection(spice_file, results_dir, line_width, critical_stress, all_lines, seconds=seconds)
    finally:
        sys.stdout = old_stdout  # Restore original stdout

    end_time = time.time()
    # Print the extracted values
    print("Time to failure (t_nucl) is: {} years".format(t_nucl / 3.1536e7))
    print("Function execution time: {:.3f} seconds".format(end_time - start_time))
    output = log_output.getvalue()
    # Process the output
    lines = output.split("\n")
    analysis_result = None

    for i, line in enumerate(lines):
        if "Converged at iteration" in line:
            # Look back for "Analysis result: " before this line
            for j in range(i - 1, -1, -1):  # Go backwards
                if "Analysis result: " in lines[j]:
                    analysis_result = lines[j].split("Analysis result: ")[-1].strip()
                    # Use regex to extract line name and max stress value
                    match = re.search(r"Maximum stress found at line (\S+) with value ([\d.]+) Pa", analysis_result)
                    if match:
                        max_stress_line = match.group(1)
                        max_stress_value = float(match.group(2))
                    break
            break  # Stop after finding "Converged at "

    # Process the files
    process_files(spice_file, "M1")
    
    project_name = "stress_" + os.path.splitext(os.path.basename(spice_file))[0]
    # Extract filename without extension
    basename = os.path.basename(spice_file)  # "C_0_T0_b.spice"
    name_without_ext = os.path.splitext(basename)[0]  # "C_0_T0_b"

    failed_line_path = os.path.join(EM_analysis_config.results_dir, project_name, name_without_ext, "M1", "{}.csv".format(max_stress_line))
    
    get_failed_subcores(failed_line_path)
        
    subcores_output_path = os.path.join(EM_analysis_config.results_dir, project_name, "output", "subcore_files")
    ttf_results = calculate_ttf_for_subcores(subcores_output_path, failed_subcores, critical_stress, (t_nucl / 3.1536e7))

    save_r_ttf_values(ttf_results, core_name, BENCHMARKS_FOLDER)
    
    pass # continue without waiting for users input
