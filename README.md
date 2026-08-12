# HotPROTON

HotPROTON is a system-level framework for thermal-aware, physics-based
electromigration (EM) analysis in manycore processors. It connects workload
execution in HotSniper to subcore power and temperature estimation, generates
a per-core power-delivery-network (PDN) model, evaluates EM stress with the
PROTON analytical engine, and feeds time-to-failure information back into the
architectural reliability metric.

HotPROTON is described in:

> Maria Pantazi, Olympia Axelou, George Floros, Yixian Shen, Simon Polstra,
> George Stamoulis, and Anuj Pathania. "HotPROTON: A System-Level Framework
> for Thermal-Aware Electromigration Analysis in Manycore Systems."
> ACM Transactions on Architecture and Code Optimization, 2026.

The final DOI will be added when it is assigned. Machine-readable citation
metadata is available in [`CITATION.cff`](CITATION.cff).

## Relationship to HotSniper and PROTON

HotPROTON is built on
[HotSniper](https://github.com/anujpathania/hotsniper), and therefore retains
the HotSniper/Sniper directory hierarchy and build flow. HotPROTON adds the
following integration components:

- `pggen/`: converts interval power, temperature, voltage, and floorplan data
  into per-core SPICE PDN models.
- `proton/`: the analytical PROTON engine path used by HotPROTON. The
  standalone PROTON GUI, example benchmarks, Windows support files, and
  transient/MOR path are intentionally not included.
- `tools/mcpat.py`: invokes PDN generation and physics-based reliability
  analysis during periodic power modeling.
- `hotproton_debug.py`: opt-in diagnostic logging for the integration path.
- `simulationcontrol/`: configures workloads and stores one named directory
  for each architectural simulation.

The inherited HotSniper documentation remains in `README-HotSniper`,
`README_SNIPER`, and `The HotSniper User Manual.pdf`. See `THIRD_PARTY.md` for
upstream projects, citations, and licenses.

## Supported Environment

The artifact is intended for x86-64 Linux and is built inside the supplied
Ubuntu 16.04 Docker environment. The embedded analytical PROTON path is
Linux-only. Docker is recommended because PinPlay, the inherited Sniper
toolchain, and the PROTON kernels depend on older compiler and library
versions.

Install Docker and configure it for use without `sudo` before continuing:

- <https://docs.docker.com/engine/install/ubuntu/>
- <https://docs.docker.com/engine/install/linux-postinstall/>

The initial build and PARSEC setup require network access.

## Repository Preparation

Clone HotPROTON and enter its root directory. The PinPlay archive is retained
in the same form used by HotSniper; extract it before building:

```sh
tar xf pinplay-drdebug-3.2-pin-3.2-81205-gcc-linux.tar.gz
mv pinplay-drdebug-3.2-pin-3.2-81205-gcc-linux pin_kit
```

Do not commit the extracted `pin_kit/` directory. Other inherited dependencies
such as XED, mbuild, McPAT, and the Sniper Python kit are downloaded by the
top-level Makefile when absent.

## Build

Build and enter the Docker image from the repository root:

```sh
cd docker
make
make run
```

The repository is mounted at the same host path inside the container. From
inside the container, return to the repository root and build HotSpot and
HotPROTON:

```sh
cd ..
make -C hotspot
make
```

The build creates downloaded dependencies and compiled files locally. These
paths are excluded by `.gitignore` and are not part of the published source.

The Linux PROTON kernels are included so the integrated workflow can run in
the supplied container. To rebuild the analytical kernel from its retained
source after installing the documented oneAPI, Eigen, FFTW, and Boost
dependencies, run `make -C proton analytical`.

### PARSEC Benchmarks

Still inside the container, define the inherited Sniper variables and build
the benchmark suite:

```sh
export GRAPHITE_ROOT="$(pwd)"
export SNIPER_ROOT="$GRAPHITE_ROOT"
export BENCHMARKS_ROOT="$GRAPHITE_ROOT/benchmarks"
make -C benchmarks
```

`benchmarks/parsec/Makefile` downloads the PARSEC 2.1 core and `simsmall`
inputs from Figshare, validates the archives, applies the HotSniper patches,
and overlays the included `gcc-sniper` build configuration. Downloaded PARSEC
sources remain under `benchmarks/parsec/parsec-2.1/` and must not be committed.

## Configuration

The default experiment is configured in `simulationcontrol/config.py`:

- `NUMBER_CORES`: number of simulated cores.
- `SNIPER_CONFIG`: architecture configuration, `gainestown` by default.
- `RESULTS_FOLDER`: destination for completed architectural runs.
- `ENABLE_HEARTBEATS`: enables supported Heartbeats instrumentation.

Workload scenarios are ordinary Python functions in
`simulationcontrol/run.py`. The default `main()` calls `example()`, which runs
PARSEC Blackscholes with the `simsmall` input. Edit or add a scenario there
before starting a campaign.

The HotPROTON integration also recognizes these environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOTPROTON_FLOORPLAN_FILE` | `pggen/input/gainestown_2x2.flp` | PDN floorplan |
| `HOTPROTON_POWERGRIDS_DIR` | `benchmarks/powergrids` | Standalone SPICE input location |
| `HOTPROTON_EM_RESULTS_DIR` | `results/hotproton_em_runs` | Detailed PROTON project data |
| `HOTPROTON_SPICE_FILE` | `C_0_T3_b.spice` under the power-grid directory | Standalone test design |
| `PROTON_HOME` | `proton/` | Embedded PROTON engine location |
| `HOTPROTON_DEBUG` | disabled | Diagnostic logging (`1`, `true`, or `debug`) |

Paths may be absolute or relative to the shell's current directory. Prefer
environment variables for machine-specific paths; source files contain no
user-specific home-directory paths.

## Run

Run a configured campaign inside the container:

```sh
cd simulationcontrol
PYTHONIOENCODING="UTF-8" python3 run.py
```

Set `HOTPROTON_DEBUG=1` to print detailed PDN and PROTON integration messages:

```sh
HOTPROTON_DEBUG=1 PYTHONIOENCODING="UTF-8" python3 run.py
```

Each architectural run is stored under `results/` using its timestamp,
configuration, and benchmark, for example:

```text
results/results_2026-08-12_05.30_1.0GHz+maxFreq+slowDVFS_parsec-blackscholes-simsmall-4/
```

Detailed EM projects are stored separately under
`results/hotproton_em_runs/`. Their names identify the generated design,
core, and simulated interval, for example `stress_C_0_T1000_b/`. Generated
PDNs are stored in the active Sniper output directory under `powergrids/`.

These result directories can become large and are ignored by Git. Move or
archive result directories outside the repository when retaining long runs.

## Evaluate Results

List completed simulations with:

```sh
cd simulationcontrol
PYTHONIOENCODING="UTF-8" python3 parse_results.py
```

Plots for performance, power, thermal, frequency, and reliability traces are
created in each completed run directory. The `simulationcontrol.resultlib`
package provides helpers for custom analysis.

## Reproducibility Checklist

Before starting a publication experiment, record or verify:

- the HotPROTON Git revision and Docker image tag;
- `NUMBER_CORES`, `SNIPER_CONFIG`, and the workload scenario;
- the active sections of `config/base.cfg`;
- the technology node and McPAT power configuration;
- DVFS levels and periodic sampling interval;
- the floorplan and matching HotSpot configuration;
- PROTON technology, interconnect width, and critical-stress parameters;
- the destination paths for architectural and detailed EM results.

The resulting `sim.cfg`, execution metadata, compressed periodic traces, and
plots are copied into the named architectural run directory.

## Acknowledgements

HotPROTON exists because of the work of the HotSniper, Sniper, PROTON,
HotSpot, McPAT, Intel Pin/PinPlay and XED, Heartbeats, PARSEC, and
CircuitSimulation authors and contributors. We thank those communities for
making their research software available. Please cite the corresponding
projects when using HotPROTON; publication and license details are collected
in `THIRD_PARTY.md`.

## License

HotPROTON combines components with different licenses. The inherited root
`LICENSE`, component-local license files, `NOTICE`, and `THIRD_PARTY.md` apply.
The PinPlay archive is governed by Intel's included software license. The
trimmed PROTON engine retains its BSD 3-Clause license in `proton/LICENSE`.
