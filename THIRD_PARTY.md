# Third-Party Software and Research Tools

HotPROTON extends and integrates several research tools. This document is an
attribution guide, not a replacement for the license files distributed with
each component.

## HotSniper and Sniper

The repository layout and architectural/thermal simulation flow are based on
[HotSniper](https://github.com/anujpathania/hotsniper), which in turn is based
on the [Sniper multicore simulator](https://snipersim.org/). The inherited
Sniper notices and licensing terms are retained in `LICENSE`, `NOTICE`,
`CONTRIBUTORS`, and component-local files.

Please cite:

> A. Pathania and J. Henkel, "HotSniper: Sniper-Based Toolchain for Many-Core
> Thermal Simulations in Open Systems," IEEE Embedded Systems Letters, vol. 11,
> no. 2, pp. 54-57, 2019. DOI: 10.1109/LES.2018.2866594.

> T. E. Carlson, W. Heirman, and L. Eeckhout, "Sniper: Exploring the Level of
> Abstraction for Scalable and Accurate Parallel Multi-Core Simulation," SC,
> 2011.

## PROTON

The analytical EM engine is derived from
[PROTON](https://github.com/oaxelou/PROTON), originally integrated at commit
`7d6c039d676a1da748acce58bad88fcccd9d26c5`. HotPROTON retains only the Linux
analytical path used by the system-level workflow. Its BSD 3-Clause license is
stored in `proton/LICENSE`.

Please cite:

> O. Axelou, E. Tselepi, G. Floros, N. Evmorfopoulos, and G. Stamoulis,
> "PROTON - A Python Framework for Physics-Based Electromigration Assessment on
> Contemporary VLSI Power Grids," SMACD, 2023. DOI:
> 10.1109/SMACD58065.2023.10192229.

PROTON's bundled Linux DC solver is based on Christos Kalonakis's
[CircuitSimulation](https://github.com/hrkalona/CircuitSimulation) project.

## Thermal, Power, and Instrumentation Tools

- [HotSpot](https://github.com/uvahotspot/HotSpot): compact thermal modeling.
  Its license is retained in `hotspot/LICENSE`.
- [McPAT](https://www.hpl.hp.com/research/mcpat/): integrated power, area, and
  timing modeling. The source is downloaded by the inherited build system.
- [Heartbeats](https://github.com/libheartbeats/heartbeats): application
  performance monitoring. Its license is retained in `heartbeats/LICENSE`.

## Execution and Benchmark Infrastructure

- Intel Pin/PinPlay and Intel XED provide binary instrumentation and decoding.
  Their applicable licenses are retained with the distributed archives and in
  the root license/notice files.
- [PARSEC](https://parsec.cs.princeton.edu/) supplies the principal workloads
  used by the HotPROTON evaluation. Its source and inputs are downloaded during
  benchmark preparation and are not republished in this repository.
- The inherited Sniper tree contains additional third-party components with
  their own local notices. Those notices remain authoritative for those files.
