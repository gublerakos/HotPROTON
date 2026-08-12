#!/usr/bin/env python3

import subprocess
import sys
import os

if len(sys.argv) != 2:
    print('usage: {} steady-state-temperatures-file-in-celsius'.format(sys.argv[0]))
    sys.exit(1)

# Get the absolute path of the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

temp_file = sys.argv[1]

# This script continuously calls the reliability_external program to generate
# r values.  It then reads the most recent r-values and prints the r value of
# the first core.

def ms_to_hour(t):
    return t / (1000 * 60 * 60)

def hour_to_year(t):
    return t / (24 * 365)

def ms_to_year(t):
    return hour_to_year(ms_to_hour(t))

# cleanup
subprocess.run("rm -f rvalues.txt states.txt", shell=True, check=True)

# delta_t = 100_000_000  # sample time in ms
delta_t = 8640000000 # 100 days in ms
#delta_t = 21600000000 # 250 days in ms

t = 0  # in ms
r_limit = 0.01
area = 0  # in hours

# Print header with time and component names.
with open(temp_file) as tfile:
    print(','.join(['time'] + tfile.readline().split('\t')), end='')

executable_path = os.path.join(script_dir, 'reliability_external')

while True:
    subprocess.run("{} {} {} states.txt rvalues.txt".format(executable_path, delta_t, temp_file), shell=True, check=True)
    t += delta_t
    # if t % 1_000_000 == 0:
    with open('rvalues.txt') as f:
        f.readline()  # read and ignore header
        rvalues = list(map(float, f.readline().split('\t')))
        #print(ms_to_hour(t), ',', ', '.join(map(str, rvalues)))
        print(hour_to_year(ms_to_hour(t)), ',', ', '.join(map(str, rvalues)))

        area += rvalues[0] * ms_to_hour(delta_t)
        if min(rvalues) <= r_limit:
            break;
print("R <= {} after {} years".format(r_limit, ms_to_year(t)), file=sys.stderr)
print("Area under curve first component: {} years".format(hour_to_year(area)), file=sys.stderr)
