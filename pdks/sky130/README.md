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
| Model | `param + MC_MM_SWITCH*AGAUSS(0,1,1)*slope/sqrt(l*w*mult)` for `vth0`, `toxe` (relative) and `voff`, `l` and `w` in µm. nFET slopes: 3.356 mV µm, 0.344 %µm, 7 mV µm |
| `mult` | Appears only in these terms; the device line has no `m=` |
| Examples | `sky130/ngspice/mismatch.sp` (100 samples of a pair, one process, `setseed` + `reset`) and `noise.sp` (`.noise` with per-source spectra) |
| Noise model | BSIM4 `fnoimod=1`, `tnoimod=1`: flicker `noia=2.5e42`, `ef=0.84`; `kf=0` and unused |
