# ASAP5 (pinned upstream)

| | |
|---|---|
| What | ASAP5 r0p4: 5 nm predictive PDK with gate-all-around nanowire FETs (Arizona State University) |
| Upstream | https://github.com/The-OpenROAD-Project/asap5 |
| Pin | commit `97962f34` (`upstream.lock`). Sparse, blob-filtered fetch of `LICENSE` and the nanowire model cards only, about 0.3 MB. `LICENSE` and the 40 cards are also checked against `models.sha256`. |
| Licence | BSD-3-Clause. `LICENSE` here is upstream's, verbatim. Upstream ships no NOTICE file. |
| Used here | `asap5PDK_r0p4/models/hspice/allvt_cgp44_210623a/nwfet/*_210623a.pm`: BSIM-CMG 107 cards for SRAM/RVT/LVT/SLVT n- and p-FETs in TT/FF/SS/FS/SF. Adapted for ngspice as recorded in `ngspice/ADAPTATIONS.md`, without changing any result. |

Not fetched: the Cadence libraries, the standard-cell views, the journal
paper in `docs/` (read once to transcribe the interconnect table below; its
SHA-256 is recorded in `sanity/asap5/reference.py`), and the Calibre decks
(not yet released upstream).

## Interconnect

Bootstrap installs, next to the models in `<prefix>/asap5/ngspice/`:

- `interconnect.csv`: per layer (M1-M12, V1-V12), one row per quantity with
  its status (`published`, `derived` or `gap`) and source. Width and pitch
  are from the paper's Table 5; spacing is pitch - width; thickness (metal)
  and height (via) are 2 x width from the stated 2:1 aspect ratio (section
  5.1). V1-V3 list "21/13" in the table; the 13 nm width the text gives is
  used. **Sheet resistance, its temperature coefficient, via resistance and
  capacitance per length are gaps**: the paper only plots line resistivity
  (Fig. 8) and the Calibre decks are not released. They are not estimated.
  If you have them from a source you may use, pass them to the ladder
  yourself.
- `interconnect.inc`: the published and derived geometry as
  `.param asap5_<layer>_<w|s|t|p|h>` (m1_w, m1_s, v1_w, ...).
- `wire.inc`: `wire`, `wire1` ... `wire64`, an N-segment pi ladder:
  `X1 a b wire16 l=100u w={asap5_m2_w} rsh=<ohm/sq> cpl=<F/m>`. R = rsh*l/w
  and C = cpl*l. `rsh` and `cpl` have no default, so a deck cannot pick up
  a made-up wire by accident. The far-end Elmore delay of an open wire is
  R*C/2 for any segment count.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no
hashed entry; the table is transcribed from the paper.

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
