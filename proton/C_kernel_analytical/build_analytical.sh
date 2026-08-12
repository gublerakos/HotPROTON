#!/bin/bash
set -e

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MKLROOT=${MKLROOT:-/opt/intel/oneapi/mkl/latest}

g++ -std=c++11 \
  "$HERE"/src/*.cpp "$HERE"/src/simulation_engine/*.cpp \
  -I"$MKLROOT/include" -I/usr/local/include/eigen3 \
  -L"$MKLROOT/lib/intel64" -Wl,-rpath,"$MKLROOT/lib/intel64" \
  -lmkl_intel_lp64 -lmkl_sequential -lmkl_core \
  -lpthread -lm -ldl -fopenmp -lfftw3 -lboost_filesystem \
  -o "$HERE/../bin/EMtool_analytical"
