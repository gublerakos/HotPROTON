#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
import pandas as pd
import sys
from pathlib import Path

argparser = argparse.ArgumentParser(description="Plot r-values")
argparser.add_argument("rvalues", help="R-values csv file")
argparser.add_argument("--noplot", default=False, action='store_true',
        help="Do not open a plot window")
args = argparser.parse_args()

rvalue_file = args.rvalues

# Load your CSV file into a pandas dataframe
df = pd.read_csv(rvalue_file, index_col=0)

# Show the plot with all (sub)components

fig, axs = plt.subplots(figsize=(12,12))
df.plot(ax=axs)
axs.set_ylabel('Reliability value')
axs.set_xlabel('Time (years)')

filename = Path(rvalue_file)
fig.savefig(str(filename.with_suffix('.pdf')))
fig.savefig(str(filename.with_suffix('.png')))
fig.savefig(str(filename.with_suffix('.eps')))

if args.noplot == False:
    plt.show()

