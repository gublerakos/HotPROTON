#!/usr/bin/env python3

from scipy.constants import convert_temperature

import sys

if len(sys.argv) != 2:
    print('usage: {} temperature-file-kelvin'.format(sys.argv[0]))
    sys.exit(1)

temperature_file = sys.argv[1]

def k_to_c(k):
    return convert_temperature(k, 'Kelvin', 'Celsius')

with open(temperature_file) as f:
    print(f.readline(), end='')  # Copy header
    temperatures = list(map(float, f.readline().split('\t')))
    temperatures = list(map(k_to_c, temperatures))
    first = True
    for t in temperatures:
        if first:
            first = False
        else:
            print('\t', end='')
        print("{:.4}".format(t), end='')
    print()
