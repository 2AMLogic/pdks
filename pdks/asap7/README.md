# ASAP7 (pinned upstream)

| | |
|---|---|
| What | ASAP7 7 nm predictive FinFET PDK, release 1p7 (Arizona State University and Arm Research) |
| Upstream | https://github.com/The-OpenROAD-Project/asap7_pdk_r1p7 |
| Pin | commit `58d72c9d291e186a77468586ab0c43d8a21eda6a` (`upstream.lock`) |
| Checked files | `models.sha256`: LICENSE and the three HSPICE corner cards (TT, FF, SS, dated 2016-08-03) |
| Licence | BSD-3-Clause, `LICENSE` here is upstream's, verbatim. Upstream ships no NOTICE file. |
| Used here | `models/hspice/7nm_{TT,FF,SS}_160803.pm`, BSIM-CMG 107 cards, adapted for ngspice as recorded in `ngspice/ADAPTATIONS.md` |

Bootstrap fetches only this repository (about 9 MB). It does not fetch the
standard-cell libraries (`asap7sc7p5t_28` and others, several GB, used for
digital place-and-route rather than device simulation) or the Calibre
DRC/LVS decks, which ASU distributes separately from asap.asu.edu.

Please cite the PDK when you publish results that use it:

> L. T. Clark, V. Vashishtha, L. Shifren, A. Gujja, S. Sinha, B. Cline,
> C. Ramamurthy, and G. Yeric, "ASAP: A 7-nm finFET predictive process
> design kit," *Microelectronics Journal*, vol. 53, pp. 105–115, 2016,
> doi:10.1016/j.mejo.2016.04.006.
