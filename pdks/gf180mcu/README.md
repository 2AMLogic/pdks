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
