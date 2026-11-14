# SKY130 (pinned upstream)

| | |
|---|---|
| What | SkyWater SKY130 130 nm CMOS, the `sky130A` variant, as built by open_pdks |
| Upstream | open_pdks build `f6eeac7`, from the ciel release assets at github.com/fossi-foundation/ciel-releases (`upstream.lock`). Device models are skywater-pdk-libs-sky130_fd_pr `403964dc`. |
| Pin | SHA-256 of `common.tar.zst` and `sky130_fd_pr.tar.zst`, 21 MB together |
| Extracted | `sky130A/libs.tech/ngspice` (the default, binned models), `sky130A/libs.tech/combined` (SkyWater's continuous models, used by the sanity checks) and `sky130A/libs.ref/sky130_fd_pr/spice` only (about 55 MB) |
| Licence | Apache-2.0. `LICENSE` here is sky130_fd_pr's, verbatim (open_pdks' is byte-identical). No upstream NOTICE file. |
| Adaptations | none. The library is ngspice-native BSIM4. It expects `set ngbehavior=hsa` and `set ng_nomodcheck` (the PDK's own spinit settings), which bootstrap writes to `sky130/ngspice/spiceinit`. |

`f6eeac7` is the build the 2AM fleet uses. It replaces `c6d73a35`, which was
installed with volare (its release feed stopped in Aug 2025). Newer builds are
published at fossi-foundation/ciel-releases.

## Mismatch and noise

SkyWater's documentation at the pinned commit publishes no mismatch
coefficient and no noise level, so the checks (`sanity/sky130/reference.py`)
are derived from the model files, and the gaps are listed there.

| | |
|---|---|
| Mismatch switch | `.lib tt_mm` (and every other `*_mm` corner) sets `mc_mm_switch=1`; `tt` sets 0. `.lib mc` is process variation (`mc_pr_switch`), not mismatch. |
| Where | Each `*__mismatch.corner.spice` (nfet_01v8, nfet_01v8_lvt, pfet_01v8, pfet_01v8_lvt, pfet_01v8_hvt, nfet_03v3_nvt, nfet_05v0_nvt, nfet_g5v0d10v5, pfet_g5v0d10v5) carries the `*_slope` parameters; the `*.pm3.spice` bins apply them, e.g. nfet_01v8 `vth0` at line 76 of `sky130_fd_pr__nfet_01v8__tt.pm3.spice` |
| Model | `param + MC_MM_SWITCH*AGAUSS(0,1,1)*slope/sqrt(l*w*mult)`, `l` and `w` in µm, one independent Gaussian per parameter per instance |
| Which parameters | **Not the same set for the two 1.8 V devices.** All 180 `nfet_01v8` bins carry mismatch on `vth0`, `toxe` (relative) and `voff`; all 108 `pfet_01v8` bins carry it on those three **plus `nfactor`**, the subthreshold-slope factor — a fourth term with no nFET counterpart (the nFET corner file defines `nfactor_slope = 0.0` and no nFET bin references it). The pFET's `voff_slope` is **0.0**, so for the pFET `voff` contributes no variance, where for the nFET it is the largest of the three slopes |
| Slopes | Values as the bin at W/L = 1/0.5 µm applies them. nFET: `vth0` 3.356 mV µm, `toxe` 0.344 %µm, `voff` 7 mV µm. pFET: `vth0` 5.856 mV µm (1.74x the nFET's), `toxe` 0.444 %µm, `nfactor` 0.1 µm, `voff` 0 |
| Slope variants | Each corner file also defines `_slope1` and `_slope2` variants of every term, and **each model bin references exactly one variant per parameter**, so the value a run sees depends on the bin its W/L selects. At L = 0.5 µm — exactly a bin edge in both devices — ngspice binds the bin whose `lmin` equals 0.5 µm and so applies the unsuffixed slopes; the bin below (pFET `model.69`, L in [0.25, 0.5) µm) applies `_slope1`, whose `vth0_slope1` is 7.356 mV µm, 26 % higher. `sanity/sky130/reference.py` records how that was resolved against ngspice (`op` + `showmod`, which prints the bound bin's `vth0`/`lvth0`) |
| `mult` | Appears only in these terms; the device line has no `m=` |
| Examples | `sky130/ngspice/mismatch.sp` (100 samples of an nFET pair, one process, `setseed` + `reset`) and `noise.sp` (`.noise` with per-source spectra). The deck template is parameterised by device and polarity, so the sanity checks render it for both the nFET and the pFET |
| Noise model | BSIM4 `fnoimod=1`, `tnoimod=1`: flicker `noia=2.5e42`, `ef=0.84`; `kf=0` and unused |

## Interconnect

Source research (all public documentation of `google/skywater-pdk` at commit
`7198cf647113f56041e02abf3eb623692820c5e1`, published at
skywater-pdk.readthedocs.io; fetched only to read, nothing is committed):

| Quantity | Published in | File (SHA-256 below) |
|---|---|---|
| Width, spacing (li1, met1–met5; mcon, via–via4 cut size and spacing) | periphery design rules | `docs/rules/periphery-rules.rst` |
| Sheet resistance (li1, met1–met5) | RCX "Resistances" | `docs/rules/rcx/resistance-values.tsv` |
| Parallel-plate and fringe capacitance, layer to layer | RCX "Capacitance Values" | `docs/rules/rcx/capacitance-parallel.tsv`, `capacitance-fringe-upward.tsv`, `capacitance-fringe-downward.tsv` |

Full SHA-256 values: `periphery-rules.rst`
`a4fec57aa417caa1b52d67b684a6b17dfc1ed0b69724ffe121de421bd938d44e`;
`resistance-values.tsv`
`02426104d3a472dd40ecc974bb4421d92096f1a4dc26c9b64d6324eb6d84dbc3`;
`capacitance-parallel.tsv`
`3a89a1081802e5080a8959e6eaa0d1bb0ccdc315a162843e6e3fdbd0d733a4b0`;
`capacitance-fringe-upward.tsv`
`74826cbd1d41fbf81667a5b5d062b041db558429f6de2b8197c455a94c2f719e`;
`capacitance-fringe-downward.tsv`
`420b00a9516b460924b2500f305ebcc9318271bca242ddc51707b222d614cc49`.

Bootstrap installs, next to the models in `<prefix>/sky130/ngspice/`:

- `interconnect.csv`: per layer (li1, met1–met5; mcon, via, via2–via4), one
  row per quantity with its status (`published`, `derived` or `gap`) and
  source. Width and spacing are the design rules; pitch is their sum;
  sheet resistance is the RCX value (mΩ/sq ÷ 1000); the 45 layer-to-layer
  capacitance rows (`c_area_to_<layer>`, `c_fringe_up_to_<layer>`,
  `c_fringe_down_to_<layer>`) are the three published matrices.
  **Gaps:** thickness (it appears only in a figure, `metal_stack.svg`), the
  temperature coefficient, capacitance per length to the substrate
  (isolated and at minimum pitch: the tables are layer-to-layer only) and
  via resistance (the RCX table prints cut values under the label
  "mohms/sq" with no per-cut definition). Nothing is estimated.
- `interconnect.inc`: the published and derived values as
  `.param sky130_<layer>_<w|s|p>` (metres) and `sky130_<layer>_rsh` (ohm/sq).
- `wire.inc`: `wire`, `wire1` … `wire64`, the same pi ladder and interface
  as ASAP7: `X1 a b wire16 l=100u w={sky130_met1_w} rsh={sky130_met1_rsh} cpl=<F/m>`.
  `cpl` has no default (it is a gap), so a deck cannot pick up a made-up
  wire; omitting `w`, `rsh` or `cpl` stops ngspice with an unknown-parameter error.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no
entry; the table is transcribed from the documentation and carries no
upstream file.
