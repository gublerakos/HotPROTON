#!/usr/bin/env python3
"""Render a HotSpot floorplan without machine-specific paths."""

from __future__ import print_function

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


HERE = os.path.dirname(os.path.abspath(__file__))


def read_floorplan(path):
    units = []
    with open(path, "r") as floorplan_file:
        for raw_line in floorplan_file:
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            fields = line.split()
            if len(fields) != 5:
                raise ValueError("Malformed floorplan line: {}".format(raw_line.rstrip()))
            units.append((
                fields[0], float(fields[1]), float(fields[2]),
                float(fields[3]), float(fields[4]),
            ))
    return units


def plot_floorplan(input_path, output_path):
    units = read_floorplan(input_path)
    if not units:
        raise ValueError("Floorplan is empty: {}".format(input_path))

    figure, axes = plt.subplots(figsize=(10, 8))
    for name, width, height, left_x, bottom_y in units:
        axes.add_patch(plt.Rectangle(
            (left_x, bottom_y), width, height,
            edgecolor="black", facecolor="skyblue", alpha=0.7,
        ))
        axes.text(
            left_x + width / 2.0, bottom_y + height / 2.0, name,
            fontsize=6, ha="center", va="center",
        )

    axes.set_xlim(min(unit[3] for unit in units),
                  max(unit[3] + unit[1] for unit in units))
    axes.set_ylim(min(unit[4] for unit in units),
                  max(unit[4] + unit[2] for unit in units))
    axes.set_aspect("equal", adjustable="box")
    axes.set_xlabel("X-coordinate")
    axes.set_ylabel("Y-coordinate")
    axes.set_title("Floorplan Visualization")
    figure.tight_layout()
    figure.savefig(output_path, dpi=300)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "floorplan", nargs="?", default=os.path.join(HERE, "gainestown_core.flp"),
    )
    parser.add_argument("--output", default="floorplan_plot.png")
    args = parser.parse_args()
    plot_floorplan(args.floorplan, args.output)
    print("Figure saved as {}".format(args.output))


if __name__ == "__main__":
    main()
