import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPER = os.path.dirname(HERE)
sys.path.append(SNIPER)

FLOORPLAN_FILE = os.path.abspath(os.path.expanduser(os.environ.get(
    'HOTPROTON_FLOORPLAN_FILE',
    os.path.join(HERE, 'input', 'gainestown_2x2.flp'),
)))

from pggen.parse_power_subcores_new import *
from hotproton_debug import get_logger


logger = get_logger(__name__)

class DataStore:
    adjusted_subcores = None  # Class variable to store data
    floorplan_width = None
    floorplan_height = None
    core_data = None
    line_temperatures = {}

interval = 0
def pg_gen(power_data, thermal_data, voltage_data, output_dir, seconds):
    """
    Generates the power grid, calculates currents, and creates a heatmap using the
    processed power and thermal data.
    
    Args:
      power_data: Dictionary mapping components to their power values.
      thermal_data: Dictionary mapping components to their thermal values.
      voltage_data: Dictionary mapping cores to their supply voltages.
      output_dir: Directory in which generated SPICE files are stored.
      seconds: Simulated timestamp represented by this sample.
    """
    global interval
    
    floorplan = parse_floorplan(FLOORPLAN_FILE)

    # Convert the flat McPAT/HotSpot dictionaries into per-core subcore records.
    core_data = {}
    core_pattern = re.compile(r"^(C_\d+)_(.*)$")
    for key in power_data:
        match = core_pattern.match(key)
        if match:
            core_name, subcore = match.groups()
            if core_name not in core_data:
                core_data[core_name] = []
            core_data[core_name].append({
                "name": subcore,
                "power": power_data[key],
                "temperature": thermal_data.get(key, None)
            })

    DataStore.core_data = core_data
    
    logger.debug("Power-grid output directory: %s", output_dir)

    grid_resolution = 10000  # set as needed

    # Step 3: Generate power grid for each core at each time interval
    # Now iterate over the cores from the floorplan
    for core_name, subcores in floorplan.items():
        if not core_name.startswith("C_"):
            continue
        
        core_voltage = voltage_data.get(core_name, None)
        if core_voltage is None:
            print("WARNING: No voltage data found for {}".format(core_name))
            continue
        # Generate one PDN for each core represented in the floorplan.
        logger.debug("Generating power grid for %s at %s V", core_name, core_voltage)
        powergrid_generator(
            floorplan, core_voltage, core_name, seconds, core_data,
            output_dir, grid_resolution,
        )
        logger.debug("Finished power grid for %s", core_name)

    print("Power grid generation completed.")
    interval += 1

def parse_floorplan(file_path):
    """
    Parses the floorplan file to extract core and subcore information.

    Returns:
    - A dictionary of cores, with each core containing its subcores' dimensions and positions.
    """
    floorplan = defaultdict(list)
    
    # Ensure the file is properly opened
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Skip empty lines or lines that don't contain data
                line = line.strip()
                if not line:
                    continue
                
                # Split the line into components (assuming space or tab separation)
                parts = line.split()

                # Extract the core, subcore, and remainder
                core_name, subcore_name = extract_core_subcore(parts[0])

                # Ensure we have the right number of columns for dimensions and positions
                if len(parts) >= 5:
                    try:
                        subcore_data = {
                            'name': subcore_name,
                            'dimensions': (float(parts[1]), float(parts[2])),  # width and height of subcore
                            'position': (float(parts[3]), float(parts[4]))  # x, y position of subcore
                        }
                        floorplan[core_name].append(subcore_data)
                    except ValueError:
                        continue  # Skip lines with invalid data

    except Exception as e:
        print("An unexpected error occurred: {}".format(e))
        return None
 
    return floorplan

def extract_core_subcore(core_string):
    """
    Extracts core and subcore from a string based on the format:
    Core is everything before the first underscore, and subcore is everything after it.
    If there is no underscore, the core is the entire string, and subcore is empty.
    
    Parameters:
    - core_string: A string representing a core and subcore (e.g., C_0_FPU, C_3_IC).
    
    Returns:
    - core_name: The core name (everything before the first underscore).
    - subcore_name: The subcore name (everything after the first underscore, or empty if not present).
    """
    parts = core_string.split('_', 2)  # Split at the first two underscores only
    
    # If we have more than two parts, it's a valid split
    core_name = '_'.join(parts[:2])  # Core is everything before the second underscore
    subcore_name = parts[2] if len(parts) > 2 else ''  # Subcore is after the second underscore, or empty
    
    return core_name, subcore_name

def print_floorplan(floorplan_data):
    """
    Prints the floorplan data with cores and subcores, showing their width, height, and position.
    :param floorplan_data: A dictionary containing cores and their subcores with their dimensions and positions.
    """
    logger.debug("Floorplan contains %s cores", len(floorplan_data))
    
    for core, subcores in floorplan_data.items():
        for subcore in subcores:
            subcore_name = subcore['name']
            width, height = subcore['dimensions']
            x_pos, y_pos = subcore['position']
            logger.debug(
                "%s/%s: width=%s, height=%s, position=(%s, %s)",
                core,
                subcore_name,
                width,
                height,
                x_pos,
                y_pos,
            )


def powergrid_generator(floorplan, vsource, core_name, time_interval, core_data, output_dir, grid_resolution=10000):
    """
    Generates the netlist for the power grid based on the floorplan and core data.

    Parameters:
    - floorplan: Dictionary with core and subcore floorplan data {core: {subcore: (x, y, width, height)}}.
    - vsource: Voltage source value.
    - core_name: Name of the core (e.g., "C_0").
    - time_interval: Time interval to consider.
    - core_data: Dictionary with power and voltage data for cores.
    - output_dir: Directory to save the generated netlist file.
    - grid_resolution: Resolution of the power grid in terms of steps per unit.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    logger.debug("Power-grid time interval: %s", time_interval)

    # Output file for this core and time interval
    output_filename = os.path.join(output_dir, core_name + "_T" + str(time_interval) + "_b.spice")

    # Find the minimum (x, y) position of all subcores for the current core to reset the origin
    min_x = float('inf')
    min_y = float('inf')
    for subcore in floorplan[core_name]:
        x, y = subcore["position"]
        min_x = min(min_x, x)
        min_y = min(min_y, y)

    # Adjust the positions of all subcores in the core so that (min_x, min_y) becomes (0, 0)
    adjusted_subcores = []
    for subcore in floorplan[core_name]:
        x, y = subcore["position"]
        width, height = subcore["dimensions"]
        
        # Adjust the position
        adjusted_x = x - min_x
        adjusted_y = y - min_y
        
        # Add the adjusted subcore information
        adjusted_subcores.append({
            "name": subcore["name"],
            "position": (adjusted_x, adjusted_y),
            "dimensions": subcore["dimensions"]
        })
        
    DataStore.adjusted_subcores = adjusted_subcores
    # Recalculate the floorplan width and height with adjusted positions
    floorplan_width = max(x + w for subcore in adjusted_subcores for (x, y), (w, h) in [(subcore["position"], subcore["dimensions"])])
    floorplan_height = max(y + h for subcore in adjusted_subcores for (x, y), (w, h) in [(subcore["position"], subcore["dimensions"])])
    
    DataStore.floorplan_width = floorplan_width
    DataStore.floorplan_height = floorplan_height

    # Grid dimensions based on the resolution and floorplan dimensions
    grid_columns = int(math.floor(floorplan_width * grid_resolution))
    grid_rows = int(math.floor(floorplan_height * grid_resolution))

    # Initialize grid currents
    grid_currents = [[0] * grid_columns for _ in range(grid_rows)]
        
    # Ensure the core_name exists in core_data
    if core_name in core_data:
        core_data_list = core_data[core_name]
    else:
        print("Core data for {} not found!".format(core_name))
        return  # or raise an error if necessary

    # Iterate over the subcores for this core
    for subcore_data in core_data_list:
        subcore_name = subcore_data["name"]
        subcore_powers = subcore_data["power"]

        subcore_power = subcore_powers
        # McPAT provides subcore power while the V/f controller provides one
        # supply voltage per core for the same simulation interval.
        subcore_voltage = subcore_data.get("voltage", vsource)
        if subcore_voltage <= 0:
            raise ValueError("Voltage for {} must be positive".format(core_name))

        # Calculate current for the subcore
        subcore_current = subcore_power / subcore_voltage

        # Distribute the subcore current uniformly over all covered grid points.
        if core_name in floorplan:
            for subcore_info in adjusted_subcores:
                if subcore_info["name"] == subcore_name:
                    position = subcore_info['position']  # (x, y)
                    dimensions = subcore_info['dimensions']  # (width, height)

                    # Unpack the position and dimensions
                    x, y = position
                    width, height = dimensions

                    # Convert subcore area to grid cell indices
                    start_col = int(x * grid_resolution)
                    end_col = int((x + width) * grid_resolution)
                    start_row = int(y * grid_resolution)
                    end_row = int((y + height) * grid_resolution)

                    covered_rows = list(range(
                        max(0, start_row), min(grid_rows, end_row)
                    ))
                    covered_cols = list(range(
                        max(0, start_col), min(grid_columns, end_col)
                    ))

                    # A thin subcore can be smaller than one grid pitch in
                    # either dimension. Map that dimension to the nearest
                    # grid point instead of silently dropping its current.
                    if not covered_rows:
                        center_row = int((y + height / 2.0) * grid_resolution)
                        covered_rows = [max(0, min(grid_rows - 1, center_row))]
                    if not covered_cols:
                        center_col = int((x + width / 2.0) * grid_resolution)
                        covered_cols = [max(0, min(grid_columns - 1, center_col))]

                    num_points = len(covered_rows) * len(covered_cols)
                    point_current = subcore_current / num_points
                    for row in covered_rows:
                        for col in covered_cols:
                            grid_currents[row][col] += point_current

    bottom= grid_rows - 1
    right = grid_columns - 1
    # Write the netlist file
    with open(output_filename, 'w') as fout:
        # Voltage sources
        fout.write('v0 n1_0_0 0 {} \n'.format(vsource))  # Bottom-left corner
        fout.write('v1 n1_0_{} 0 {} \n'.format(right, vsource))  # Bottom-right corner
        fout.write('v2 n1_{}_0 0 {} \n'.format(bottom, vsource))  # Top-left corner
        fout.write('v3 n1_{}_{} 0 {} \n'.format(bottom, right, vsource))  # Top-right corner

        layernum = 1

        # Write information about the layer (required by PROTON)
        fout.write("* layer: M" + str(layernum) + ",VDD net: " + str(layernum) + "\n")

        layernum += 1
        
        # Base grid resolution
        grid_x_res = floorplan_width / grid_columns
        grid_y_res = floorplan_height / grid_rows

        # Store forced resistor positions
        forced_resistors = []
        for subcore in adjusted_subcores:
            x_start, y_start = subcore["position"]
            x_end = x_start + subcore["dimensions"][0]
            y_end = y_start + subcore["dimensions"][1]

            # Force a resistor inside small subcores
            if subcore["dimensions"][0] < grid_x_res * 2 or subcore["dimensions"][1] < grid_y_res * 2:
                # Place the resistor at the center of the subcore
                x_forced = (x_start + x_end) / 2
                y_forced = (y_start + y_end) / 2
                forced_resistors.append((x_forced, y_forced, subcore["name"]))

        # Now, create the resistors based on the grid
        for i in range(grid_columns):
            for j in range(grid_rows):
                x1 = i * grid_x_res
                y1 = j * grid_y_res
                subcore_name = None

                # Check if we need to force a resistor for small subcores
                for x_f, y_f, name in forced_resistors:
                    # Check if current grid point is inside any forced subcore
                    if abs(x_f - x1) < grid_x_res and abs(y_f - y1) < grid_y_res:
                        subcore_name = name  # Force resistor inside the subcore
                        break

                # Regular grid-based resistor placement (not in small subcores)
                if subcore_name is None:
                    for subcore in adjusted_subcores:
                        x_start, y_start = subcore["position"]
                        x_end = x_start + subcore["dimensions"][0]
                        y_end = y_start + subcore["dimensions"][1]

                        # Check if the grid point is inside the subcore
                        if (x_start <= x1 <= x_end and y_start <= y1 <= y_end):
                            subcore_name = subcore["name"]
                            break
                        
                if ((j+1) == grid_rows):
                    break 

                # Write resistor details to output
                lnode = 'n1_{}_{}'.format(j, i)
                rnode = 'n1_{}_{}'.format(j + 1, i)
                rname = 'R_{}_{}_{}'.format(subcore_name, i, j) if subcore_name else 'R_{}_{}'.format(i, j)
                resistor_value = 1.25 #0.0000336 #1.25
                fout.write('{} {} {} {:.9f}\n'.format(rname, lnode, rnode, resistor_value))

        # Resistors for rows (horizontal connections)
        for i in range(grid_rows):
            for j in range(grid_columns):
                x1 = i * grid_y_res
                y1 = j * grid_x_res
                subcore_name = None

                # Check if we need to force a resistor for small subcores
                for x_f, y_f, name in forced_resistors:
                    if abs(x_f - y1) < grid_x_res and abs(y_f - x1) < grid_y_res:
                        x1, y1 = x_f, y_f  # Force the resistor inside the subcore
                        subcore_name = name
                        break

                # Regular grid-based resistor placement (not in small subcores)
                if subcore_name is None:
                    for subcore in adjusted_subcores:
                        x_start, y_start = subcore["position"]
                        x_end = x_start + subcore["dimensions"][0]
                        y_end = y_start + subcore["dimensions"][1]

                        # Check if the grid point is inside the subcore
                        if (x_start <= y1 <= x_end and y_start <= x1 <= y_end):
                            subcore_name = subcore["name"]
                            break
                
                if ((j+1) == grid_columns):
                    break 

                # Write resistor details to output
                lnode = 'n1_{}_{}'.format(i, j)
                rnode = 'n1_{}_{}'.format(i, j + 1)
                rname = 'R_{}_{}_{}'.format(subcore_name, i, j) if subcore_name else 'R_{}_{}'.format(i, j)
                resistor_value = 1.25#0.0000336 #1.25
                # The extra R distinguishes horizontal RR_* segments from
                # vertical R_* segments in the downstream PROTON mapping.
                fout.write('R{} {} {} {:.9f}\n'.format(rname, lnode, rnode, resistor_value))


        # Attach each distributed current sample to its corresponding node.
        for row in range(grid_rows):
            for col in range(grid_columns):
                if grid_currents[row][col] > 0:
                    fout.write('i_{}_{} n1_{}_{} 0 {:.6f}\n'.format(row, col, row, col, grid_currents[row][col]))

        # Final netlist commands
        fout.write('*\n.op\n')
    return grid_currents
