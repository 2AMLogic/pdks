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

## Interconnect

Source research (public documentation of `google/gf180mcu-pdk` at commit
`de3240d7529a6970437ac3344820aaae7839f215`, published at
gf180mcu-pdk.readthedocs.io; fetched only to read, nothing is committed):

| Quantity | Published in | File (SHA-256 below) |
|---|---|---|
| Width, spacing (M1–M5), via size and spacing (V1–V5) | Design Rule Manual, Metaln and Vian rules | `docs/physical_verification/design_manual/tables_clear/22_Metaln_58.csv`, `23_Vian_59.csv` |
| Sheet resistance, via resistance, temperature coefficient | Electrical Parameters Specification 5.1, 5.2, 5.7 | `docs/analog/spice/elec_specs/tables_clear/5_General_Specification1.csv`, `…2.csv`, `…7.csv` |
| Thickness (M1–M5) and the same sheet resistance | Interconnect application note | `docs/analog/layout/inter_specs/tables_clear/3_General_conductor.csv`, `5_Sheet_Rho_table.csv` |

`22_Metaln_58.csv` `5b2d176a4273ffe18c38a4a2f851b344b4d756d6bf8ea18b26b0abfb1bce6f05`;
`23_Vian_59.csv` `94606470dba70a4a4267227dc21bf226cb0dd14de91a93df0760b5898f69a6e4`;
`5_General_Specification1.csv` `a20ccbc509cefd992e733472b96a6712efc65793b823a2ccd1aa90d7727c25af`;
`5_General_Specification2.csv` `eb9a9e7983bd4f83205a329b99e9a0516cba079d9067357d5e899c73b584980e`;
`5_General_Specification7.csv` `a5ff93e99b7ed0813cf15d059b59334ef173d560587fd023726f0dacedb766a9`;
`3_General_conductor.csv` `8cc79cb291280a03bed6d08d5bf440cabe81b0e22381a0c358b99d8be6e44114`;
`5_Sheet_Rho_table.csv` `98e9a330fcfea7e1918fa9b90ca7cac457456f29174447337a3c793794e1ce17`.

Bootstrap installs, next to the example in `<prefix>/gf180mcu/ngspice/`:

- `interconnect.csv`: per layer (M1–M5, V1–V5), one row per quantity with
  its status (`published`, `derived` or `gap`) and source. Width and spacing
  are the design rules (M1 0.23 µm, M2–M5 0.28 µm; vias 0.26 µm); pitch is
  their sum; thickness is the application note's "typical cap" value
  (0.55 µm, a simulation parameter, not an EP limit); sheet resistance is
  the EP typical value (90 mΩ/sq, window 76–104) and its temperature
  coefficient 0.33 %/°C; via resistance is 4.5 Ω typical. MetalTop is not
  tabulated: it has four thickness options (6, 9, 11, 30 kÅ).
  **Gaps:** capacitance per length (isolated and at minimum pitch), which
  the application note gives only as plots, and the via height. Nothing is
  estimated.
- `interconnect.inc`: the published and derived values as
  `.param gf180mcu_<layer>_<w|s|p|t>` (metres) and `gf180mcu_<layer>_rsh` (ohm/sq).
- `wire.inc`: `wire`, `wire1` … `wire64`, the same pi ladder and interface
  as ASAP7: `X1 a b wire16 l=100u w={gf180mcu_m1_w} rsh={gf180mcu_m1_rsh} cpl=<F/m>`.
  `cpl` has no default (it is a gap), so omitting `w`, `rsh` or `cpl` stops
  ngspice with an unknown-parameter error.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no
entry.

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
