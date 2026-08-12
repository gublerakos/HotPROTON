# Embedded PROTON Analytical Engine

This directory contains only the PROTON components exercised by HotPROTON's
Linux analytical electromigration flow:

- SPICE parsing and DC-current extraction;
- analytical matrix formulation;
- analytical line-stress evaluation;
- mapping line stresses back to architectural subcores;
- the Linux `circuit_simulation` and `EMtool_analytical` kernels;
- source for rebuilding the analytical EM kernel.

The standalone PROTON GUI, CLI shell, IBM example power grids, documentation
media, Windows binaries and DLLs, transient simulation, and model-order
reduction implementation are intentionally omitted because HotPROTON does not
invoke them.

This code is derived from <https://github.com/oaxelou/PROTON> and remains under
the BSD 3-Clause license in `LICENSE`. See the repository-level
`THIRD_PARTY.md` for the PROTON citation and additional attribution.

Machine-specific locations are configurable with `PROTON_HOME` and
`HOTPROTON_EM_RESULTS_DIR`; no source edit is required.
