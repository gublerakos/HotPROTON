import csv
import re
from collections import defaultdict

from hotproton_debug import get_logger


logger = get_logger(__name__)

# Function that extracts core prefixes like C_0, C_1, C_2, C_3
def find_core_prefixes(header):
    core_prefixes = set()
    pattern = re.compile(r'(C_\d+)_')  # Match 'C_<number>_' in each column name
    
    for col_name in header:
        match = pattern.match(col_name)
        if match:
            core_prefixes.add(match.group(1))  # Extract 'C_<number>' without the trailing '_'
    
    return core_prefixes

from collections import defaultdict

import re

import re

def parse_power_and_thermal_files(power_file, thermal_file):
    """
    Parses power and thermal files and creates a structured representation of core data.

    Args:
    - power_file: Path to the power file.
    - thermal_file: Path to the thermal file.

    Returns:
    - core_data: A dictionary with the structure:
        {
            "C_0": [
                {"name": "IALU", "powers": [0.237217, ...], "temperatures": [45.08, ...]},
                ...
            ],
            "C_1": [...],
            ...
        }
    """
    core_data = {}

    # Read both files
    with open(power_file, 'r') as pf, open(thermal_file, 'r') as tf:
        power_lines = pf.readlines()
        thermal_lines = tf.readlines()

    # Validate the files have the same number of lines
    if len(power_lines) != len(thermal_lines):
        raise ValueError("Power and thermal files have mismatched line counts.")

    # Extract subcore names from the first line
    power_subcore_names = power_lines[0].strip().split('\t')
    thermal_subcore_names = thermal_lines[0].strip().split('\t')

    # Ensure the headers match between power and thermal files
    if power_subcore_names != thermal_subcore_names:
        raise ValueError("Subcore names in power and thermal files do not match.")

    subcore_names = power_subcore_names
    core_pattern = re.compile(r"^C_\d+$")  # Regex pattern for validating core names (e.g., C_<index>)

    # Parse data from subsequent lines
    for time_interval, (power_line, thermal_line) in enumerate(zip(power_lines[1:], thermal_lines[1:])):
        power_values = list(map(float, power_line.strip().split('\t')))
        thermal_values = list(map(float, thermal_line.strip().split('\t')))

        # Validate data length
        if len(power_values) != len(subcore_names) or len(thermal_values) != len(subcore_names):
            raise ValueError("Mismatch in number of values at time interval {}.".format(time_interval))


        for subcore_name, power, thermal in zip(subcore_names, power_values, thermal_values):
            # Extract core and subcore names
            parts = subcore_name.split('_')
            if len(parts) < 3:
                logger.debug("Skipping invalid subcore name: %s", subcore_name)
                continue  # Skip this entry

            core_name = '_'.join(parts[:2])  # Core name (e.g., "C_0")
            subcore_identifier = '_'.join(parts[2:])  # Subcore name (e.g., "IALU")

            # Validate core name format
            if not core_pattern.match(core_name):
                logger.debug("Skipping invalid core name: %s", core_name)
                continue

            # Initialize the core in core_data if not present
            if core_name not in core_data:
                core_data[core_name] = []

            # Find or create the subcore entry
            subcore = next((s for s in core_data[core_name] if s["name"] == subcore_identifier), None)
            if not subcore:
                subcore = {"name": subcore_identifier, "powers": [], "temperatures": []}
                core_data[core_name].append(subcore)

            # Append power and thermal data
            subcore["powers"].append(power)
            subcore["temperatures"].append(thermal)

    return core_data


def print_core_data_by_time_interval(core_data):
    """
    Prints the core data (power and voltage) for each time interval.

    Args:
    - core_data: The core data structure containing power and voltage values for each subcore.

    Prints the core data in a format that shows all subcores for each core with their power and voltage values.
    """
    # Get the number of time intervals from one core's first subcore
    first_core = next(iter(core_data.values()))  # Get the first core
    first_subcore = first_core[0]  # Get the first subcore dictionary
    num_time_intervals = len(first_subcore["powers"])  # Number of time intervals

    for time_interval in range(num_time_intervals):
        logger.debug("Time interval %s", time_interval + 1)
        
        for core_name, subcores in core_data.items():
            logger.debug("Core: %s", core_name)
            for subcore in subcores:
                subcore_name = subcore["name"]
                
                # Ensure powers and voltages are synchronized
                if len(subcore["powers"]) != len(subcore["voltages"]):
                    raise ValueError(
                        "Subcore {} in Core {} has mismatched powers ({}) and voltages ({}).".format(
                            subcore_name, core_name, len(subcore['powers']), len(subcore['voltages'])
                        )
                    )
                
                power = subcore["powers"][time_interval]
                voltage = subcore["voltages"][time_interval]
                logger.debug(
                    "Subcore %s: power=%.6f, voltage=%.6f",
                    subcore_name,
                    power,
                    voltage,
                )

def parse_core_subcore(col_name):
    """
    Parses the core name and subcore name from the column header.
    
    Returns:
    - Core name and subcore name as a tuple.
    """
    parts = col_name.split('_')
    core_name = '_'.join(parts[:2])  # First part is the core name (e.g., C_0)
    subcore_name = '_'.join(parts[2:]) if len(parts) > 2 else None  # Everything after the first two underscores is the subcore
    return core_name, subcore_name

def parse_voltage_file(voltage_file, core_data):
    """
    Parses the voltage file and adds voltage data to the core_data structure.

    Args:
    - voltage_file: Path to the voltage file.
    - core_data: The core data structure that contains power information.

    Modifies core_data to include voltage values for each subcore.
    """
    with open(voltage_file, 'r') as file:
        lines = file.readlines()

    # First line contains core names
    core_names = lines[0].strip().split('\t')  # Core names, e.g., ["Core0", "Core1", ...]

    # Iterate over time intervals (remaining lines in the voltage file)
    for time_interval, line in enumerate(lines[1:]):
        voltages = line.strip().split('\t')  # Voltage values for this time interval

        # Ensure that the number of cores in the voltage file matches the number of subcores in core_data
        if len(voltages) != len(core_names):
            raise ValueError("Mismatch between number of core names ({}) and voltage values ({})".format(len(core_names), len(voltages)))


        # Iterate through the cores
        for core_name, voltage in zip(core_names, voltages):
            # Extract the core name (e.g., "Core0" -> "C_0")
            core_identifier = "C_" + core_name[4:]  # "Core0" -> "C_0"

            # Skip if the core is not in the core_data
            if core_identifier not in core_data:
                continue

            # Add voltage to each subcore in the core
            for subcore in core_data[core_identifier]:
                # Initialize voltages list if not already present
                if "voltages" not in subcore:
                    subcore["voltages"] = []

                # Append voltage value to the subcore
                subcore["voltages"].append(float(voltage))

    return core_data
