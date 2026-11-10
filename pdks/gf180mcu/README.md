# GF180MCU (pinned upstream)

| | |
|---|---|
| What | GlobalFoundries 180 nm MCU process, primitive device models (3.3 V, 5 V, 6 V MOSFETs and passives) |
| Upstream | fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr (the maintained fork of the archived google repository) |
| Pin | commit `b6866b82`, the commit open_pdks `f6eeac7` records for gf180mcu_fd_pr (it replaces `faef89e8`, recorded by `c6d73a35`). The four ngspice model files (`*.spice` upstream) are fetched one by one and checked against `files.sha256` (1.4 MB). |
| Licence | Apache-2.0. `LICENSE` and `AUTHORS` here are upstream's, verbatim. No upstream NOTICE file. |
| Adaptations | none. The cards are ngspice-native BSIM4; no spiceinit settings are needed. |

The full open_pdks build of gf180mcu is a 334 MB tarball, most of it
standard cells and layout; ngspice device simulation needs only these
four files.

## Mismatch and noise

GF publishes the 3.3 V mismatch only as plotted fit lines (Spice Model
Reference Guide 9.4) and, for noise, only the measurement conditions (2.3),
so the checks (`sanity/gf180mcu/reference.py`) are derived from the model
files plus a comparison with the digitised nFET lines; the gaps are listed
there. Line numbers are in `models/ngspice/sm141064.spice` at the pin.

| | |
|---|---|
| Mismatch switch | `.param sw_stat_mismatch=0` in `design.spice` (line 63); set it to 1 after the include. `sw_stat_global` is process variation, not mismatch. |
| Where | `.lib fets_mm` (included by `.lib typical`, line 134; defined from line 46930): X-prefix subcircuits `nfet_03v3`, `pfet_03v3`, `nfet_05v0`, `nfet_06v0`, `pfet_05v0`, `pfet_06v0`. An `M` card has no mismatch. No mismatch in `nfet_06v0_nvt`. |
| Model | `delvto = agauss(0,var_vth,1)`, `mulu0 = 1 - agauss(0,var_k,1)`, `var = 0.7071*par/sqrt((l-par_l)*par*(w-par_w))`, sizes in µm; nfet_03v3 `par_vth` 7.148 mV µm, `par_k` 0.70 % µm (lines 46932-46943) |
| `par` | Multiplies the width in the spread only (the nominal device is unchanged) |
| Not covered | Resistors, BJTs and MIM capacitors (own statistical hooks), pFET and 5 V/6 V mismatch checks |
| Examples | `gf180mcu/ngspice/mismatch.sp` (100 pairs, one process, `setseed` + `reset`) and `noise.sp` (`.noise` with per-source spectra) |
| Noise model | BSIM4 `fnoimod=1` (`noia`, `noib`, `noic` from `.lib noise_corner`, `ef` 0.95 for nfet_03v3) and `tnoimod=0` (`ntnoi=1`); `fnoicor=0` selects the as-extracted flicker level. 2 of 198 MOS models (pfet_06v0) lack `ntnoi` |
