import time
import os
import subprocess

from hotproton_debug import get_logger


logger = get_logger(__name__)

os.system("")

class Analytical_Class(object):

  def __init__(self,sim_time,directory,selected_line,TECHNOLOGY,TEMPERATURE,WIDTH,IS_LINUX, INSTALLATION_FOLDER):
    super(Analytical_Class, self).__init__()
    self.sim_time=sim_time
    self.directory=directory
    self.selected_line=selected_line
    self.TECHNOLOGY=TECHNOLOGY
    self.TEMPERATURE=TEMPERATURE
    self.WIDTH=WIDTH
    self.IS_LINUX = IS_LINUX
    self.INSTALLATION_FOLDER = INSTALLATION_FOLDER

  def analytical_function(self):
	
    Acoef = ""
    nxTotal = ""
    logger.debug("Starting analytical simulation for line %s", self.selected_line)

    if not self.selected_line:
      return('No line was selected and discretized prior to simulation.')

    # Read the internal configuration file for analytical provided by matrix formulation
    line_path = self.selected_line+"/"+self.TECHNOLOGY+"_"+str(self.TEMPERATURE)+"_"+str(self.WIDTH)+"/"
    analytical_file = self.directory+"/"+"input"+"/"+line_path+"analytical.txt"
    logger.debug("Reading analytical configuration from %s", analytical_file)

    try:
      with open(analytical_file) as f_anal:
        lines=f_anal.readlines()
        for line in lines:
          words = line.split()
          if'Acoef'in words: Acoef=words[2]
          if'nx_total'in words: nxTotal = words[2]
        f_anal.close()
    except (IOError, OSError) as e:
      return "No discretization has been performed for line %s with params: %s, %s, %s." % (self.selected_line, self.TECHNOLOGY, self.TEMPERATURE, self.WIDTH)


    # Check that the input files directory exists (not much of a check but for precaution)
    input_files = self.directory + "/input/"+line_path
    if not os.path.exists(input_files):
      return "Input files directory for %s does not exist." % self.selected_line

    # Create the configuration file for C++ Analytical code here
    config_file = self.directory+"/input/"+line_path+"analytical.cfg"
    try:
      with open(config_file, "w") as f:
        f.write("input_files {}\nnum_nodes {}\n".format(input_files, nxTotal))
        f.write("A_coeff {}\nsimulation_time {}\n".format(Acoef, self.sim_time))
        f.close()
        logger.debug("Wrote analytical configuration to %s", config_file)
    except Exception as e:
      print("Error writing to file:", e)

    start_time = time.time()
    if not self.IS_LINUX:
      return "HotPROTON's embedded PROTON engine currently supports Linux only."

    exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin", "EMtool_analytical")
    logger.debug("Running analytical executable %s with %s", exec_path, config_file)
    return_value = subprocess.call([
      "bash", "-lc",
      'export HOTPROTON_ANALYTICAL="$1" HOTPROTON_CONFIG="$2"; '
      '. /opt/intel/oneapi/mkl/latest/env/vars.sh && '
      'exec "$HOTPROTON_ANALYTICAL" "$HOTPROTON_CONFIG"',
      "hotproton-analytical", exec_path, config_file,
    ])
    elapsed_time = time.time() - start_time
    logger.debug("Analytical executable returned %s", return_value)
    if return_value == 0:
      return_message = "EM stress analysis was successfully performed in {:.3f} seconds for the line {} (Configuration: {}, {}K, {}um).".format(elapsed_time, self.selected_line, self.TECHNOLOGY, self.TEMPERATURE, self.WIDTH)
      
    elif return_value == -1073740791: # 0xc0000409
      return_message = "Line analysis terminated with exception (0xc0000409) in system settings or system files or registry entries or critical utilities."
    elif return_value == -1073741819: # 0xC0000005
      return_message = "Line analysis terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to."
    elif return_value == -1073741676: # 0xC0000094
      return_message = "Line analysis terminated with exception (0xC0000094). Integer division by zero exception code on Windows"
    elif return_value == -1073741515:
      return_message = "Line analysis terminated with exception (-1073741515). Problem with the dependencies"
    elif return_value in (127, 32512):
      return_message = "Line analysis could not start because a dependency is missing."
    elif return_value == -1073741510:
      raise KeyboardInterrupt
    else:
      return_message = "Line analysis terminated with unknown error {}".format(return_value)

    logger.debug("Analytical result: %s", return_message)
    return(return_message)

    
