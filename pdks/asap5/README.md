# ASAP5 (pinned upstream)

| | |
|---|---|
| What | ASAP5 r0p4: 5 nm predictive PDK with gate-all-around nanowire FETs (Arizona State University) |
| Upstream | https://github.com/The-OpenROAD-Project/asap5 |
| Pin | commit `97962f34` (`upstream.lock`). Sparse, blob-filtered fetch of `LICENSE` and the nanowire model cards only, about 0.3 MB. `LICENSE` and the 40 cards are also checked against `models.sha256`. |
| Licence | BSD-3-Clause. `LICENSE` here is upstream's, verbatim. Upstream ships no NOTICE file. |
| Used here | `asap5PDK_r0p4/models/hspice/allvt_cgp44_210623a/nwfet/*_210623a.pm`: BSIM-CMG 107 cards for SRAM/RVT/LVT/SLVT n- and p-FETs in TT/FF/SS/FS/SF. Adapted for ngspice as recorded in `ngspice/ADAPTATIONS.md`, without changing any result. |

Not fetched: the Cadence libraries, the standard-cell views, the journal
paper in `docs/`, and the Calibre decks (not yet released upstream).

Please cite the PDK when you publish results that use it:

> V. Vashishtha and L. T. Clark, "ASAP5: A predictive PDK for the 5 nm
> node," *Microelectronics Journal*, vol. 126, 105481, 2022,
> doi:10.1016/j.mejo.2022.105481.
