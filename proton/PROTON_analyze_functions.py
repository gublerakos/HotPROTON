import os
from sys import platform
import shutil
import json
import time
from tqdm import tqdm
from functools import partial
import concurrent.futures
from threading import Lock
import threading
import random
import signal

import sys
import locale

HERE = os.path.dirname(os.path.abspath(__file__))
SNIPER = os.path.dirname(HERE)
sys.path.append(SNIPER)
from proton.classes.spice_function_cli import *
from proton.classes import spice_function_cli
from proton.classes.matrix_formulation_func_cli import *
from proton.classes.analytical_class_cli import *

from pggen.pg_gen import DataStore
from hotproton_debug import get_logger


logger = get_logger(__name__)

json_data_sim = {}

IS_LINUX = platform != "win32"
INSTALLATION_FOLDER = os.path.abspath(os.path.expanduser(
	os.environ.get("PROTON_HOME", HERE)
))

def write_message_in_log(message_log_path, message, mestype='info'):
	locale.setlocale(locale.LC_TIME, 'en_US.UTF-8') # Language always in Enghlish. Comment out for system language
	cur_time = time.localtime()
	timestamp = time.strftime("%a %d %b %Y %H:%M:%S", cur_time)
	if mestype == 'info':
		message_log_mestype = "INF"
	elif mestype == "error":
		message_log_mestype = "ERR"
	elif mestype == "success":
		message_log_mestype = "SUC"
	else:
		print("mestype: " + mestype)
		return
		
	message_log_string = "[" + message_log_mestype + "] " + "[" + timestamp + "] " + message + "\n"
	
	with open(message_log_path, "a") as fd:
		fd.write(message_log_string)

def extract_number_between(string, start_word, end_word):
	pattern = r"" + re.escape(start_word) + r"\s+(\d+(\.\d+)?)\s+" + re.escape(end_word)
	match = re.search(pattern, string)
	if match:
		return float(match.group(1))
	else:
		return None

def extract_numbers(string):
    matches = re.findall(r'\d+', string)
    return tuple(map(int, matches))

width = 0
def set_line_width(given_width):
	global width
	if spice_function_cli.benchmark == "":
		depend_string = "For set_line_width command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	try:
		if float(given_width) > 0:
			width = float(given_width)
			return 0
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for line width: It must be a positive real number.")
		return 1

directory = ""
powergrid = ""
def set_powergrid(spice_file):
	global powergrid
	powergrid = spice_file
 
def set_project_path(given_path):
	global project_path
	project_path = given_path
 
project_name = ""
def set_project_name(given_name):
	global project_name
	if not all(ord(char) < 128 for char in given_name):
		print("Project name should be an ASCII string.")
		return 1
	project_name = given_name

def save_project_details(project_name, project_path, spice_path, benchmark):
	temp_dictionary = {
		"magic_word": "papaya56",
		"project_name": project_name,
		"project_path": project_path,
		"full_path_to_project": project_path+ "/" + project_name,
		"spice_path": spice_path,
		"parsed_spice_path": benchmark
	}
 
def save_config_file(save, given_directory=None):
	global SELECTED_LINE, directory
	if given_directory is None:
		given_directory = directory
	full_path = given_directory + "/config.json"

	if save:
		dictionary_json = json.dumps(json_data_sim, indent = 4)
		with open(full_path, "w") as fd:
			fd.write(dictionary_json)
	else:
		#save default values for the window to open
		#full_path
		temp_dict1 = {"technology": "CuDD", "temperature": 0, "width": 0}
		temp_dict2 = {"parameter": "points","points": 0, "step": 0}
		temp_dict3 = {"selected_line" : ""}
		dictionary = {"line": temp_dict1, "discretization": temp_dict2, "workspace_details": temp_dict3}
		dictionary_json = json.dumps(dictionary, indent = 4)
		with open(full_path, "w") as fd:
			fd.write(dictionary_json)
	return

def get_num_lines(folder_path):
	stack = [(folder_path, "")]
	
	num_lines = 0
	while stack:
		current_path, indent = stack.pop()
		sorted_files = sorted(os.listdir(current_path), key=extract_numbers)
		
		for item in sorted_files:
			item_path = os.path.join(current_path, item)
			
			if os.path.isfile(item_path):
				num_lines += 1
			elif os.path.isdir(item_path):
				stack.append((item_path, indent + "  "))
	return num_lines

parsed_powergrid = False
def parse_powergrid(response=None):
	global directory, parsed_powergrid, powergrid, project_path, project_name, max_stress_loc, IS_LINUX, INSTALLATION_FOLDER
	spice_file_entry = powergrid
	project_location_entry = project_path
	project_name_entry = project_name
		
	if parsed_powergrid:
		print("Powergrid file has already been parsed for this project.")
	if (project_name_entry and project_location_entry and spice_file_entry):
		project_location_entry = project_location_entry
		spice_file_entry = spice_file_entry

		if not os.path.exists(project_location_entry):
			try:
				os.makedirs(project_location_entry)
			except OSError as e:
				if e.errno != 17:  # Error code for FileExistsError
					raise

		directory = os.path.join(project_location_entry, project_name_entry)
		try:
			os.mkdir(directory, 0o777)
		except OSError as e:
			if e.errno == 17:  # Error code for FileExistsError
				print("'{0}' project exists already. Choose a different path or project name.".format(project_name_entry))
				directory = ""
				return 1
			elif e.errno == 13:  # Error code for PermissionError
				print("The project cannot be created at {0} due to permission errors.".format(directory))
				directory = ""
				return 1

		#-----------------------------------------------------#

		message_log_path = directory + "/history_log.txt"
		open(message_log_path, "w")
		
		# # # # # # THREAD # # # # # # # #
		spice_parser_worker = Spice_Parser_Class(spice_file_entry,directory, IS_LINUX, INSTALLATION_FOLDER)
		return_message = spice_parser_worker.spice_parser()

		if "seconds" in return_message:
			return_string = 'Spice file was successfully parsed %s and the project has been created at %s.' % (return_message, os.path.normpath(directory))

			save_project_details(project_name_entry, project_location_entry, spice_file_entry, spice_function_cli.benchmark)
			save_config_file(False, directory)
			with open(os.path.join(directory, "config.json"), "r") as json_file:
				json_data_sim = json.load(json_file)

			# Call the function for the new layout
			exec_time = extract_number_between(return_message, "in", "seconds")
			parsed_powergrid = True
			print(return_string)
			max_stress_loc = None
			return 0

			if "seconds" not in return_message or exec_time is None:
				if "seconds" in return_message and exec_time is None:
					return_string = "An error occured while parsing the parsing execution time."
					print(return_string)
				print(return_message)
				print("Going to delete project {}...".format(directory))
				shutil.rmtree(directory)
			
			return 1

		print("Should never reach this")
		return 1
		# # # # # # # # # # # # # #

	else:
		depend_string = "For parse_powergrid command, the following dependencies are missing:\n"
		if powergrid is None or powergrid == "":
			depend_string += "  set_powergrid\n"
		if project_path is None or project_path == "":
			depend_string += "  set_project_path\n"
		if project_name is None or project_name == "":
			depend_string += "  set_project_name\n"
		print(depend_string)
		return 1

def analytical(time, silent=False, line=None):
	global disc_points, disc_step, selected_line, width, technology, temperature
	global IS_LINUX, INSTALLATION_FOLDER
	if spice_function_cli.benchmark == "" or (not silent and selected_line == ""):
		depend_string = "The following dependencies are missing:\n"
		if spice_function_cli.benchmark == "": depend_string += "  set_powergrid or open_project\n"
		if selected_line == "": depend_string += "  select_line\n"
		print(depend_string)
		return 1
	
	# Check simulation time
	try:
		if float(time) > 0:
			sim_time = float(time)
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for simulation time: It must be a positive real number.")
		return 1
	
	# Check technology 
	if technology == "":
		if not silent:
			print(" No technology was set. Selected the default technology: Copper dual-damascene (CuDD).")
		tech = "CuDD"
	else:
		tech = technology

	temp = DataStore.line_temperatures[line]

	if not silent:
		analytical_worker=Analytical_Class(sim_time=sim_time,directory=directory,selected_line=line,TECHNOLOGY=tech,TEMPERATURE=temp,WIDTH=width,IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)
	else:
		try:
			analytical_worker = Analytical_Class(
				sim_time=sim_time,
				directory=directory,
				selected_line=line,
				TECHNOLOGY=tech,
				TEMPERATURE=temp,
				WIDTH=width,
				IS_LINUX=IS_LINUX,
				INSTALLATION_FOLDER=INSTALLATION_FOLDER
			)
		except Exception as e:
			print("Error during Analytical_Class initialization:", e)
			raise
	return_message = analytical_worker.analytical_function()

	if "seconds" in return_message:
		line_path = line+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"

		if not silent:
			output_files = os.path.normpath(directory + "/output/"+line_path)
			print("The simulation results can be found at {}".format(output_files))
		return 0
	else:
		write_message_in_log(directory+ "/history_log.txt", return_message, "error")
		if(not silent and not selected_line):
			message = 'No line was selected and discretized prior to simulation.'
			print(message)
		return 1

# Function to remove old stress files
def remove_old_stress_files(output_files):
    if os.path.exists(output_files) and os.path.isdir(output_files):  # Ensure directory exists
        files = [f for f in os.listdir(output_files) if f.startswith("stress") and f.endswith(".txt")]
        if files:  # Only proceed if there are files to delete
            for filename in files:
                os.remove(os.path.join(output_files, filename))


def move_old_stress_files(output_files):
    if not os.path.exists(output_files) or not os.path.isdir(os.path.dirname(output_files)):
        print("Directory does not exist: " + output_files)
        return

    # Construct the input path by replacing 'output' with 'input'
    new_path = output_files.replace("/output/", "/input/")

    # Ensure the destination directory exists
    if not os.path.exists(new_path):
        print("Creating directory: " + new_path)
        os.makedirs(new_path)

    # Define the final destination file name
    new_file_path = os.path.join(new_path, "initial_stress.csv")

    # If `initial_stress.csv` already exists, remove it
    if os.path.exists(new_file_path):
        os.remove(new_file_path)


    shutil.move(output_files, new_file_path)
            
# FUNTIONS FOR TTF CALCULATION #
def analyze_line(item_path, exiting, problematic_lines, problematic_lines_lock, max_stress_powergrid, max_stress_powergrid_lock, simulation_time, tech, temp, critical_stress, seconds, first_time):
	item = os.path.splitext(os.path.basename(item_path))[0]
	with open(item_path, 'r') as csv_file:
		lines = csv_file.readlines()
	lengths = []
	for line in lines:
		if line[0] == 'R':
			line_components = line.split(',')
			lengths.append(float(line_components[3]))
	min_length = min(lengths)
	
	temp = DataStore.line_temperatures[os.path.splitext(item)[0]]

	discr_times = 0
	if discr_times < 10 or min_length > 0:
		# Remove the previous stress file before creating the new
		line_path = os.path.splitext(item)[0]+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"
		output_files = os.path.normpath(directory + "/output/"+line_path)
		if first_time is True:
			move_old_stress_files(output_files)
   
		remove_old_stress_files(output_files)
  
		if exiting.is_set():
			return 1
		if analytical(simulation_time, True, os.path.splitext(item)[0]) == 0:
			if exiting.is_set():
				return 1
			# Setting next line as comment in order to find max stress even if critical stress is not set #
			# if critical_stress is not None:
			#  Get results, check if ok, else store it in the problematic_lines
			line_path = os.path.splitext(item)[0]+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"
			output_files = os.path.normpath(directory + "/output/"+line_path)

			stress_file_pattern = r"stress_([\d.]+)\."
			lines = []
			for filename in os.listdir(output_files):
				if filename.endswith(".txt") and filename.startswith("stress"):
					match = re.search(stress_file_pattern, filename)
					if match:
						number = float(match.group(1))
						# if "{:.2f}".format(float(number)) == "{:.2f}".format(float(simulation_time)):
						with open(os.path.join(output_files, filename), 'r') as f_stress:
							lines = f_stress.readlines()
				
			if len(lines) == 0:
				print("The file is empty!")
				return 1
  
			max_stress = float(lines[0])
			for l in lines:
				if float(l) > max_stress:
					max_stress = float(l)
				if critical_stress is not None: # moving the check for critical stress HERE #
					if max_stress > critical_stress:
						# Acquire the lock before modifying the shared dictionary
						with problematic_lines_lock:
							problematic_lines[os.path.splitext(item)[0]] = max_stress
		else:
			# The line could not be analyzed
			print("The line %s could not be analyzed" % os.path.splitext(item)[0])
			pass
	else:
		print("%s The line was discarded" % os.path.splitext(item)[0])
		pass

	with max_stress_powergrid_lock:
		logger.debug("Maximum stress: %s", max_stress)
		max_stress_powergrid[os.path.splitext(item)[0]] = max_stress
		logger.debug("Maximum stresses by line: %s", max_stress_powergrid)
  

technology = ""
temperature = 0
max_stress_loc = None
def analyze_powergrid(simulation_time, lines_num, seconds, first_time, critical_stress=40e6, sample_lines=None):
	global selected_line, width, technology, temperature, max_stress_loc
 
	crit_stress = float(330e6)
 
	# Get the technology, temperature and width 
	if technology == "":
		logger.debug("Using default technology: Copper dual-damascene (CuDD)")
		tech = "CuDD"
	else:
		tech = technology
	
	if temperature == 0:
		logger.debug("Using default temperature: 338 K")
		temp = 338.0
	else:
		temp = temperature
	start_time = time.time()
	
	if sample_lines is not None:
		_sample_lines = int(sample_lines)
		all_lines = random.sample(all_lines, _sample_lines)
		lines_num = _sample_lines

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
				
	progress_bar = tqdm(total=lines_num, unit=' line')

	max_stress_powergrid = {} # Global shared dictionary
	max_stress_powergrid_lock = Lock() # Lock for synchronizing access to global variable
	problematic_lines = {}  # Global shared dictionary
	problematic_lines_lock = Lock()  # Lock for synchronizing access to the dictionary

	exiting = threading.Event()
	def signal_handler(signum, frame):
		print("Setting exiting event")
		exiting.set()
	signal.signal(signal.SIGTERM, signal_handler)
	
	partial_analyze_line_item  = partial(analyze_line, exiting=exiting, problematic_lines=problematic_lines, problematic_lines_lock=problematic_lines_lock, max_stress_powergrid=max_stress_powergrid, max_stress_powergrid_lock=max_stress_powergrid_lock, simulation_time=simulation_time, tech=tech, temp=temp, critical_stress=crit_stress, seconds = seconds, first_time = first_time)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		for item in all_lines:
			future = executor.submit(partial_analyze_line_item, item)
			future.add_done_callback(lambda _: progress_bar.update(1))
			futures.append(future)
		# Wait for all futures to complete
		concurrent.futures.wait(futures)

	end_time = time.time()
	progress_bar.close()

	# if critical_stress is not None:
	if len(problematic_lines) != 0:
		max_stress = None
		max_stress_loc = None
		with problematic_lines_lock:
			for failed_line in problematic_lines:
				if max_stress is None:
					max_stress = problematic_lines[failed_line]
					max_stress_loc = failed_line
				elif problematic_lines[failed_line] > max_stress:
					max_stress = problematic_lines[failed_line]
					max_stress_loc = failed_line
		max_key = max(max_stress_powergrid, key=max_stress_powergrid.get)  # Finds the maximum value
		print("Maximum stress found at line %s with value %s Pa." % (max_key, max_stress_powergrid[max_key]))
	else:
		max_key = max(max_stress_powergrid, key=max_stress_powergrid.get)  # Finds the maximum value
		print("Maximum stress found at line %s with value %s Pa." % (max_key, max_stress_powergrid[max_key]))

   
	return 0
