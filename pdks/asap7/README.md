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

## Interconnect

Bootstrap installs, next to the models in `<prefix>/asap7/ngspice/`:

- `interconnect.csv`: per layer (M1–M9, V1–V8), one row per quantity with
  its status (`published`, `derived` or `gap`) and source. Width and pitch
  are from the paper's Table 1; spacing is pitch − width; thickness (metal)
  and height (via) are 2 × width from the paper's stated 2:1 aspect ratio.
  **Sheet resistance, its temperature coefficient, via resistance and
  capacitance per length (isolated and at minimum pitch) are gaps**: the
  paper and the PDK's design manual do not print them, and the Calibre RCX
  deck that holds them is distributed separately by ASU. They are not
  estimated. If you have them from a source you may use, pass them to the
  ladder yourself.
- `interconnect.inc`: the published and derived geometry as
  `.param asap7_<layer>_<w|s|t|p|h>` (m1_w, m1_s, v1_w, …).
- `wire.inc`: `wire`, `wire1` … `wire64`, an N-segment pi ladder:
  `X1 a b wire16 l=100u w={asap7_m2_w} rsh=<ohm/sq> cpl=<F/m>`. R = rsh·l/w
  and C = cpl·l. `rsh` and `cpl` have no default, so a deck cannot pick up
  a made-up wire by accident. The far-end Elmore delay of an open wire is
  R·C/2 for any segment count.

Nothing here adapts upstream files, so `ngspice/ADAPTATIONS.md` has no
entry; the table is transcribed from the paper and carries no upstream file.

Please cite the PDK when you publish results that use it:

> L. T. Clark, V. Vashishtha, L. Shifren, A. Gujja, S. Sinha, B. Cline,
> C. Ramamurthy, and G. Yeric, "ASAP: A 7-nm finFET predictive process
> design kit," *Microelectronics Journal*, vol. 53, pp. 105–115, 2016,
> doi:10.1016/j.mejo.2016.04.006.
