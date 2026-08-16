import os
import glob
import sys
import io
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPER = os.path.dirname(HERE)
sys.path.append(SNIPER)

from proton import EM_analysis_config
from pggen.pg_gen import DataStore

def get_covered_discretization_indices(start_pos, sub_width, total_length, num_points):
    """
    Finds the set of discretization points covered by a subcore.

    :param start_pos: The starting position of the subcore along the axis
    :param sub_width: The width of the subcore
    :param total_length: The total length of the floorplan (width or height)
    :param num_points: The total number of discretization points
    :return: A list of discretization indices covered by the subcore
    """
    
    if not (0 <= start_pos <= total_length):
        raise ValueError("Start position out of range")
    if not (0 < sub_width <= (total_length - start_pos + 0.00001)):
        raise ValueError("Subcore width out of range")

    step_size = float(total_length) / float(num_points - 1)  # Ensure float division in Python 2.7

    # Find start and end indices
    start_index = int(round(start_pos / step_size))
    end_index = int(round((start_pos + sub_width) / step_size))  # Change ceil to round

    # Ensure end_index does not exceed the last discretization point
    end_index = min(end_index, num_points - 1)

    return list(range(start_index, end_index + 1))  # Ensure it includes the last index

def get_points_from_folders(subcore_folder):
    """
    From a starting directory:
        - Find first and last folders (alphabetically).
        - Search each for analytical.txt recursively.
        - Extract the number after 'nx_total = ' in its first line.

    Returns
    -------
    vertical_points : int or None
    horizontal_points : int or None
    """
    base_input_path = os.path.abspath(os.path.join(subcore_folder, "../../../input"))

    def natural_key(s):
        # Split into digit and non-digit parts: ['M1_n1_', 10, '']
        return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

    subfolders = sorted(
        [f for f in os.listdir(base_input_path)
         if os.path.isdir(os.path.join(base_input_path, f))],
        key=natural_key
    )
    if not subfolders:
        raise ValueError("No subfolders found in %s" % base_input_path)

    first_folder = os.path.join(base_input_path, subfolders[0])
    last_folder  = os.path.join(base_input_path, subfolders[-1])

    def find_nx_total(base):
        for dirpath, _, filenames in os.walk(base):
            if "analytical.txt" in filenames:
                file_path = os.path.join(dirpath, "analytical.txt")
                with open(file_path, "r") as f:
                    first_line = f.readline().strip()
                    # Expected format: "nx_total = <number>"
                    if first_line.startswith("nx_total"):
                        # split on '=' and convert
                        try:
                            return int(float(first_line.split("=")[1].strip()))
                        except (IndexError, ValueError):
                            pass
        return None

    vertical_points = find_nx_total(first_folder)
    horizontal_points = find_nx_total(last_folder)

    return vertical_points, horizontal_points
    

def process_discretization(subcore_folder, floorplan_width, floorplan_height, datastore):
    """
    Reads files created by process_files, finds the corresponding output files, and calls 
    get_covered_discretization_indices to compute discretization points.

    :param subcore_folder: Path to the folder containing subcore files.
    :param floorplan_width: Total width of the floorplan.
    :param floorplan_height: Total height of the floorplan.
    :param datastore: List of dictionaries mapping subcore names to their position and dimensions.
    """

    # Navigate two folders back and into 'output'
    base_output_path = os.path.abspath(os.path.join(subcore_folder, "../../../output"))
    get_points_from_folders(subcore_folder)
    # Ensure subcore_files directory exists
    subcore_output_path = os.path.join(base_output_path, "subcore_files")
    if not os.path.exists(subcore_output_path):
        os.makedirs(subcore_output_path)

    # Iterate over subcore files
    for subcore_filename in os.listdir(subcore_folder):
        subcore_path = os.path.join(subcore_folder, subcore_filename)
        if not os.path.isfile(subcore_path):
            continue

        # Read the subcore file
        with io.open(subcore_path, 'r', encoding='utf-8') as file:
            processed_lines = set()  # Track processed line_names to avoid duplicates

            for line in file:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue  # Skip malformed lines

                line_name, orientation = parts  # Extract name and orientation
                
                if line_name in processed_lines:
                    continue  # Skip duplicate processing of the same line_name
                
                processed_lines.add(line_name)  # Mark line_name as processed

                # Find the corresponding output folder
                output_subfolder = os.path.join(base_output_path, line_name, "{}_{}_{}".format(EM_analysis_config.set_technology, DataStore.line_temperatures[line_name], EM_analysis_config.set_width))

                if not os.path.exists(output_subfolder):
                    continue

                # Find the .txt file in the output path folder
                output_file_path = None
                for f in os.listdir(output_subfolder):
                    if f.endswith(".txt"):
                        output_file_path = os.path.join(output_subfolder, f)
                        break  # Exit the loop as soon as the file is found

                if not output_file_path or not os.path.exists(output_file_path):
                    continue

                # Read discretization values from the .txt file
                with io.open(output_file_path, 'r', encoding='utf-8') as txt_file:
                    discretization_values = [float(line.strip()) for line in txt_file]

                # Look up subcore info from DataStore
                subcore_info = next((subcore for subcore in DataStore.adjusted_subcores if subcore['name'] == subcore_filename), None)

                if subcore_info is None:
                    continue

                subcore_position = subcore_info['position']
                subcore_dimensions = subcore_info['dimensions']
                
                vertical_points, horizontal_points = get_points_from_folders(subcore_folder)
                # Determine parameters for discretization function
                if orientation == "H":
                    start_pos = subcore_position[0]
                    sub_width = subcore_dimensions[0]
                    total_length = floorplan_width
                    num_points = horizontal_points
                else:  # Vertical (V)
                    start_pos = subcore_position[1]
                    sub_width = subcore_dimensions[1]
                    total_length = floorplan_height
                    num_points = vertical_points

                # Get covered discretization indices
                covered_indices = get_covered_discretization_indices(start_pos, sub_width, total_length, num_points)

                # Append the corresponding discretization values inside subcore_files/{subcore_filename}.csv
                subcore_output_file = os.path.join(subcore_output_path, "{}".format(subcore_filename))
                with io.open(subcore_output_file, 'a', encoding='utf-8') as output_file:  # Append mode
                    for idx in covered_indices:
                        if 0 <= idx < len(discretization_values):  # Ensure index is within bounds
                            output_file.write(u"{}\n".format(repr(discretization_values[idx])))
                            
                # Read the file and find the max value
                with io.open(subcore_output_file, 'r', encoding='utf-8') as input_file:
                    values = [float(line.strip()) for line in input_file]

                max_value = max(values) if values else None  # Avoid error if file is empty

                # Overwrite file with only the max value
                if max_value is not None:
                    with io.open(subcore_output_file, 'w', encoding='utf-8') as output_file:
                        output_file.write(u"{}\n".format(repr(max_value)))
                
def process_files(design_name, metal):
    project_name = "stress_" + os.path.splitext(os.path.basename(design_name))[0]
    # Extract filename without extension
    basename = os.path.basename(design_name)  # "C_0_T0_b.spice"
    name_without_ext = os.path.splitext(basename)[0]  # "C_0_T0_b"

    csv_files_path = os.path.join(EM_analysis_config.results_dir, project_name, name_without_ext, metal)
    output_path = os.path.join(EM_analysis_config.results_dir, project_name, name_without_ext, metal, "subcore_files")

    # Ensure output directory exists (Python 2.7 compatible)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Dictionary to store lines for each subcore
    subcore_lines = {}
    rows = EM_analysis_config.rows - 1
    # Iterate over all files in the folder
    for file_path in glob.glob(os.path.join(csv_files_path, "*")):
        if os.path.isdir(file_path):  # Skip directories
            continue

        with io.open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()  # Read all lines to count them
            total_lines = len(lines) - 1  # Exclude header

            if total_lines <= 0:
                continue  # Skip empty or malformed files
            
            orientation = "V" if total_lines == rows else "H"

            for line in lines[1:]:  # Skip the first line
                parts = line.strip().split(',')
                if len(parts) < 5:
                    continue  # Skip malformed lines
                
                segment_name, left_node, right_node, length, curden = parts
                line_identifier = os.path.basename(file_path)  # e.g., M1_n1_1.csv
                subcore = segment_name.split('_')[1]  # Extract subcore name (e.g., IALU from R_IALU_0_19)

                if subcore not in subcore_lines:
                    subcore_lines[subcore] = set()
                
                subcore_lines[subcore].add((line_identifier[:-4], orientation))  # Store tuple (name, orientation)

    
    # Write results to subcore files
    for subcore, lines in subcore_lines.items():  # Use iteritems() for Python 2.7 compatibility
        subcore_filename = os.path.join(output_path, "{}".format(subcore))
        with io.open(subcore_filename, 'w', encoding='utf-8') as subcore_file:
            for line_name, orientation in sorted(lines):
                subcore_file.write(u"{} {}\n".format(line_name, orientation))
    process_discretization(output_path, DataStore.floorplan_width, DataStore.floorplan_height, DataStore)
