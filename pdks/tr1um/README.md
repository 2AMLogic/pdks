# Tokai Rika TR-1um (pinned upstream)

| | |
|---|---|
| What | Tokai Rika 1 µm CMOS (OpenSUSI's IP62 open release): 5 V NMOS and PMOS, plus diodes, resistors and capacitors |
| Upstream | https://github.com/OpenSUSI/TR-1um |
| Pin | release v1.2609.0, commit `c5bcc378` (`upstream.lock`). The five files under `libs.tech/spice/models/`, `LICENSE` and the layer design-rule table `Document/TR-1um_Drawing_Layer_DR_Table.csv` are fetched one by one and checked against `files.sha256` (about 35 KB). |
| Licence | Apache-2.0. `LICENSE` (OpenSUSI, ISHI-KAI, Tokai Rika) and `IP62-LICENSE.txt` (Tokai Rika's notice for the original IP62 data) are upstream's, verbatim. No NOTICE file. |
| Adaptations | none for the MOSFETs. They are BSIM3v3 subcircuits and load in ngspice unchanged, including the `simulator lang=spectre` comment line. |

Caveats:
- **Typical corner only.** Tokai Rika marks its corner model sets
  "非公開" (not disclosed).
- **Weak reference data.** The only device reference data are plotted
  curves (reference manual, Table I-2-7), which we digitised, so the
  checks are coarse (±5 %).
- **Capacitor CSIO doesn't load.** ngspice can't parse its
  voltage-dependent capacitor with `m=m` ("unknown parameter (e9)").
  Instantiating CSIO fails; the other models load fine.
- **RR resistor unchecked.** It reads about 36 % below its table value
  for a reason we haven't identified, so it isn't checked.

## Mismatch and noise

There is no mismatch model and no published noise model. The reference
manual's Table I-1-2 (p. 6) lists "Noise model" and "Matching" as not
provided (無), and the model cards carry no statistical terms (the only
variation hooks are the global `vthMN`/`vthMP`/`vthMNE`/`vthMPE`
shifts, which are 0 and move every instance alike). So there is no
`mismatch.sp` and no Pelgrom check.

`noise.sp` shows what the BSIM3v3 defaults give, since the four MOS cards set
no noise parameter: `noimod=1` with `kf=0` means **zero flicker noise**, and the
thermal noise is `2/3*4kT*(gm+gmbs+gds)` (gamma 0.94 of the 30/10 µm NMOS,
theory 2/3 to 1; the Nyquist ratio at Vds = 0 is 0.667, a known deviation).
None of it is a Tokai Rika value: do not use it for noise budgets.
`sanity/tr1um/reference.py` lists the gaps.

## Interconnect

Source research (pin `c5bcc378`, document text searched for per-layer
width, spacing, thickness, sheet resistance, capacitance and via
resistance):

| Document | Prints | Does not print |
|---|---|---|
| `Document/TR-1um_Drawing_Layer_DR_Table.csv` (fetched, SHA-256 in `files.sha256`) | M1 width ≥ 1.8 µm, spacing ≥ 1.4 µm; M2 width ≥ 3.0 µm, spacing ≥ 2.0 µm; V1 width 1.4 µm (rules M1.W1, M1.S1, M2.W1, M2.S1, V1.W1) | thickness, resistance, capacitance |
| Reference manual `OS00_リファレンスマニュアル_rev1.1.pdf` (rev 1.1, 2025-09-19) | sheet resistance and capacitance of the diffusion and poly-Si resistors and the CSIO capacitor (Tables I-2-4, I-2-5); electromigration limits M1 900 µA at 2 µm, M2 3.7 mA at 3 µm (Table I-3-1) | any metal sheet resistance, wire capacitance, thickness or via resistance; the cross-section figures are marked 非公開 (not disclosed) |
| Circuit-simulation guideline `OS02_…rev1.pdf` | nothing on interconnect | |

The device resistor/capacitor calculator workbook is not fetched (devices
only). Bootstrap installs, next to the models in `<prefix>/tr1um/ngspice/`:

- `interconnect.csv`: M1, M2 and V1, one row per quantity with its status
  (`published`, `derived` or `gap`) and source. Width and spacing are the
  design rules above; pitch is their sum. **Thickness, sheet resistance and
  its temperature coefficient, capacitance per length and via resistance are
  gaps**: no public document prints them. They are not estimated.
- `interconnect.inc`: the published and derived geometry as
  `.param tr1um_<layer>_<w|s|p>` (m1_w, m1_s, v1_w, …), in metres.
- `wire.inc`: `wire`, `wire1` … `wire64`, the same pi ladder as ASAP7:
  `X1 a b wire16 l=100u w={tr1um_m1_w} rsh=<ohm/sq> cpl=<F/m>`. `rsh` and
  `cpl` have no default, so a deck cannot pick up a made-up wire by accident.
  The far-end Elmore delay of an open wire is R·C/2 for any segment count.

The sanity run checks the table against the design-rule file and the ladder
against the closed-form Elmore delay with test-supplied `rsh`/`cpl` (not
TR-1um values). Nothing here adapts upstream files, so
`ngspice/ADAPTATIONS.md` has no entry.
