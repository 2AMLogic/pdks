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

## Mismatch and noise

ASAP5 is a predictive PDK, so there are no measured mismatch or noise
statistics. At the pinned commit:

| | |
|---|---|
| Authors' recommendation | None stated. ASAP5's paper discusses lithography variability (CDU, overlay, LER) for the layout rules only. |
| Mismatch | Not modelled. The cards (the 40 checked files) contain no statistical construct, so there is no mismatch switch, no Monte Carlo deck and no Pelgrom check. No coefficient is estimated. |
| Noise parameters | None set: the "noise" section of every card is empty, so BSIM-CMG 107's defaults apply (`ef` 1.0, `em` 4.1e7, `noia` 6.25e39, `noib` 3.125e24, `noic` 8.75e7, `ntnoi` 1.0). `tnoimod` does not exist in this release. These are the model's generic values, not extracted for ASAP5. |
| Example | `<prefix>/asap5/ngspice/noise.sp`: `.noise` on `nmos_rvt`, 10 fins, with the drain through an ideal inductor |
| Checks | Drain noise at Vds = 0 equals `4kT*gds` within 2 % (derived); flicker slope 1 to 100 Hz equals `-ef` (derived). Flicker level and thermal gamma are printed as information; their published values are gaps. Definitions: `sanity/asap5/reference.py`. |

Please cite the PDK when you publish results that use it:

> V. Vashishtha and L. T. Clark, "ASAP5: A predictive PDK for the 5 nm
> node," *Microelectronics Journal*, vol. 126, 105481, 2022,
> doi:10.1016/j.mejo.2022.105481.
