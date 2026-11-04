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
