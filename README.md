# Open PDKs for ngspice

One command to set up open process design kits for analog and mixed-signal
simulation in [ngspice](https://ngspice.sourceforge.io), on a fresh macOS
or Linux host. Each upstream source is pinned by commit or SHA-256 and
fetched at setup, so the clone is small. The setup is reproducible, and
results are checked against each foundry's or author's published values.

| `--pdk` | Process | Models | Fetched | Sanity checks |
|---|---|---|---|---|
| `asap7` | ASAP7 r1p7: 7 nm predictive FinFET (ASU / Arm) | BSIM-CMG 107, compiled to OSDI | 9 MB | 73/73 against the PDK paper |
| `asap5` | ASAP5 r0p4: 5 nm predictive gate-all-around nanowire FET (ASU) | BSIM-CMG 107, compiled to OSDI | 0.3 MB | 47/47 against the PDK paper, plus 1 known deviation |
| `sky130` | SkyWater SKY130 (`sky130A`; `sky130B`'s ngspice libraries are identical in this release) | BSIM4, built in | 21 MB | 25/25 against SkyWater's e-test windows, device tables (continuous models) and corner tables, plus 5 known deviations |
| `gf180mcu` | GlobalFoundries GF180MCU | BSIM4, built in | 1.4 MB | 54/54 against GF's slow/typical/fast EP targets and spec limits, incl. passives and their temperature coefficients, plus 1 known deviation |
| `ihp-sg13g2` | IHP SG13G2 SiGe BiCMOS | PSP 103 (OSDI), VBIC HBT | 3 MB | 83/83 against IHP's process spec (1.2 V and 3.3 V MOS, corners, resistors and MIM with their temperature coefficients, the HBT) and IHP's measured silicon over temperature, plus 7 known deviations |
| `ihp-sg13cmos5l` | IHP SG13CMOS5L CMOS | PSP 103 (OSDI) | 5 MB | 59/59 against IHP's process spec: 1.2 V and 3.3 V MOS, corners, resistors and their temperature coefficients, plus 1 known deviation |
| `tr1um` | Tokai Rika TR-1um 1 µm CMOS (OpenSUSI) | BSIM3v3, built in | 30 KB | 16/16 against Tokai Rika's published I-V curves (digitised), plus 1 known deviation |

## Quick start

```sh
git clone https://github.com/2AMLogic/pdks && cd pdks
./bootstrap.sh --pdk sky130            # or asap7,gf180mcu,... or all; --prefix DIR (default ~/pdks)
. ~/pdks/env.sh                        # puts the pinned ngspice on PATH
cd ~/pdks/sky130/ngspice && ngspice -b example.sp
```

The first run takes about 3 minutes: ngspice is built from source. Each PDK
then takes seconds to a minute to set up. The SKY130 checks are the slowest,
at about 2 minutes. A re-run skips finished steps.

You need the Xcode Command Line Tools on macOS, or `build-essential bison
flex curl git python3 libllvm18` on Debian/Ubuntu, plus `zstd` for SKY130.
Bootstrap installs what it can with apt-get or Homebrew (`--no-prereqs` to
skip).

## Using a PDK in your own deck

Each `<prefix>/<pdk>/ngspice/` holds a working `example.sp` and, where the
PDK needs ngspice settings, a `spiceinit`. Copy that file to
`~/.spiceinit`, or to your simulation directory as `.spiceinit`.

| PDK | Load models with | Devices | spiceinit |
|---|---|---|---|
| asap7 | `.lib ".../asap7/ngspice/models/asap7.lib" tt` | `Nn1 d g s b nmos_rvt l=20n nfin=3` | loads the BSIM-CMG OSDI |
| asap5 | `.lib ".../asap5/ngspice/models/asap5.lib" tt` | `Nn1 d g s b nmos_rvt nfin=2` (one "fin" = 2 nanowires) | loads the BSIM-CMG OSDI |
| sky130 | `.lib ".../sky130/sky130A/libs.tech/ngspice/sky130.lib.spice" tt` | `X1 d g s b sky130_fd_pr__nfet_01v8 w=1 l=0.15` (µm) | `ngbehavior=hsa`, `ng_nomodcheck` |
| gf180mcu | `.include ".../design.ngspice"` then `.lib ".../sm141064.ngspice" typical` | `M1 d g s b nfet_03v3 w=1u l=0.28u` | none |
| ihp-* | `.lib ".../libs.tech/ngspice/models/cornerMOSlv.lib" mos_tt` (3.3 V: `cornerMOShv.lib`) | `X1 d g s b sg13_lv_nmos w=1u l=0.13u ng=1` | loads the PSP/R3/MOSVAR OSDI |
| tr1um | `.include ".../tr1um/TR-1um/libs.tech/spice/models/ip62_models"` | `X1 d g s b NMOS w=10u l=1u` | none |

## What `bootstrap.sh` does

1. Checks prerequisites, installing them where it can.
2. Fetches and verifies every pinned source:

   | Component | Pin | Verified by |
   |---|---|---|
   | ngspice | 47, source release | SHA-256 (`tools/versions.lock`) |
   | OpenVAF-reloaded | v24.0.2mob release binary | SHA-256 per platform |
   | BSIM-CMG Verilog-A (ASAP7, ASAP5) | 107.0.0, CedarEDA/CMC.jl @ `548cc7a` | SHA-256 per file |
   | each PDK | commit or release asset, see `pdks/<pdk>/README.md` | git commit id or SHA-256 |

3. Builds ngspice with OSDI support and compiles the Verilog-A models the
   PDK needs.
4. Applies the minimum adaptations. Every one is listed, with its reason, in
   [`ngspice/ADAPTATIONS.md`](ngspice/ADAPTATIONS.md). ASAP7 and ASAP5
   need a few, none of which changes a result; the others need none to
   PDK files.
5. Runs a smoke test and the sanity checks.

Directories it creates carry a stamp file. It refuses to overwrite a
directory it did not create.

## Sanity checks

`sanity/run.py --pdk NAME --prefix DIR` runs `sanity/<pdk>/`. Every check
cites its source and is labelled **published** (a printed value or
window), **bound** (a published limit) or **derived** (no published value;
a physics check). Where a source doesn't state its extraction method, the
definition used is documented next to the reference values.

- **ASAP7.** Compared with Clark et al. 2016, Tables 3–4, for all eight
  devices:
  - Idsat and Ieff within 0.04 %, Vt within 5 mV, SS within 0.4 mV/dec.
  - FO4 delay is checked as below the published post-layout values.
  - The VTC and an 11-stage ring oscillator are derived checks, because
    no published values exist.
  - The paper doesn't state its extraction methods. The definitions that
    reproduce its tables for every device at once are: Ioff is channel
    current, which excludes GIDL; Vt is taken at 10 nA per fin; SS is the
    10–100 nA decade. DIBL is printed for information only, because ours
    is a uniform 1.32× the paper's column.
- **ASAP5.** All eight nanowire FETs against Vashishtha and Clark 2022,
  Tables 8–9:
  - Idsat and Vtsat match every printed digit. Vtsat uses the paper's
    stated 50 nA criterion.
  - Ioff is within 5 %, and DIBL within 0.1 mV/V for seven devices.
  - SS reads 0.6–0.9 mV/dec low; the paper doesn't state its definition.
  - nmos_sram's DIBL (22.1 vs 20.06) is a known deviation. The paper
    says its SRAM models came from an earlier calibration.
- **SKY130.** Vt, Idsat and leakage of the 1.8 V FETs, against SkyWater's
  e-test MIN–MAX windows ("Device Details" tables):
  - The tables' TT column matches SkyWater's continuous ("combined")
    models, which ship in the same build but aren't the default.
    - Against those, Idsat is within 0.4 %, and this is checked.
    - The default binned models sit +4.7 % (n) and +7.7 % (p) above the
      column, which is printed for information.
  - One row is a **known deviation**, reported on every run: the narrow
    0.42/1 µm nFET's Vt (0.60 V) is above its window.
- **GF180MCU.** Idsat and Vth0 of five FETs against GF's typical EP
  targets. All match to printed precision (e.g. 510.0 vs 510 µA/µm,
  0.630 vs 0.63 V). Ioff and subthreshold slope are checked against the
  electrical-spec limits.
- **IHP SG13G2 / SG13CMOS5L.** Every MOS row of IHP's process
  specification, for both the 1.2 V and the 3.3 V devices: Vt at three
  geometries, Idsat, Ioff, DIBL and SS. Each uses the spec's own
  extraction definition and is checked within its MIN–MAX window.
  SG13G2 adds the npn13G2 HBT: β 722 (spec 650 typ), Ic 3.69 µA (3.8),
  fT 353 GHz (≥ 300).
- **TR-1um.** Drain current of the 5 V NMOS and PMOS at 17 bias points,
  against the simulated curves in Tokai Rika's reference manual (Table
  I-2-7).
  - The manual prints no numbers, so we digitised the figures and check
    within ±5 %.
  - NMOS matches within 2 %. PMOS runs 1–5 % low, and one point is a
    known deviation.
  - The silicon measurements in the same figure are printed for
    information.

### Corners

Where a PDK publishes corner values, the corners are checked too. How strong
each check is depends on what was published:

- **GF180MCU (published).** The ss and ff models land on GF's slow and fast
  EP targets for Idsat and Vth0, for all five FETs, within 2 % / 10 mV.
- **SKY130 (published, relative to TT).** Each corner's shift from TT
  matches the table's own shift: Idsat within 3 %, Vt within 15 mV.
  - FF and SS check out fully.
  - The table's FS and SF columns contradict each other. In the nFET Vt
    row and the pFET Idsat row they are swapped relative to the other row.
  - Those four entries are reported as known deviations, and each matches
    once FS and SF are swapped.
- **IHP (published limits).** The specification gives MIN–MAX windows, and
  the `mos_ss` and `mos_ff` corners are built on their edges.
  - Each ss/ff corner lands on its limit within 10 mV or 5 %, for the
    1.2 V and the 3.3 V devices.
  - The corners also order correctly. The LV pFET ss Idsat is 5 % under
    its limit and is reported as a known deviation.
- **ASAP7, ASAP5 (derived).** Their papers show corners only as plots, so
  the check is the ordering: SS < TT < FF (and the mixed corners in
  between) for every device.
- **TR-1um.** No public corners.

### Temperature

No PDK here publishes transistor data at temperatures other than nominal,
so temperature checks cover passive devices, whose temperature
coefficients the foundries do publish. Each is swept from −40 to 125 °C.

- **IHP SG13G2 / SG13CMOS5L (published).**
  - The resistors (Rsil, Rppd, Rhigh) are checked against the spec's own
    definitions, which state both the structures and the formula:
    - A.i: sheet resistance and line-width delta, from one W-wide stripe
      and N parallel W/N stripes.
    - A.af: R(T) = R(T0)·[1 + TC1·ΔT + TC2·ΔT²], T0 = 27 °C.
  - SG13G2's MIM capacitor is checked the same way (A.k, A.ad).
  - The fitted TCs land on IHP's targets: for example Rsil 3100 ppm/K vs
    3100, Rhigh −2300 vs −2300, MIM 3.60 vs 3.6.
  - The spec gives TCs as targets without limits, so TC1 is checked
    within 5 % and TC2 within 10 %.
  - Rhigh's line-width delta (−79.9 nm) sits 0.1 nm inside its −80 nm
    limit.
- **GF180MCU (published windows; method assumed).** The TCs of the
  high-resistance poly resistors, metals M1–M4 and top metals, and MIM
  capacitors are checked against GF's MIN–MAX windows, along with their
  sheet resistance or capacitance.
  - GF states no fit range or method. We use the linear coefficient of a
    quadratic fit over −40 to 125 °C, the models' extraction range.
  - GF's own 1.5 fF/µm² MIM model has TC1 = 40.6 ppm/K, outside GF's
    9.9–16.6 window. It is reported as a known deviation.
- **IHP SG13G2 transistors (measured silicon).** IHP-Open-PDK ships IC-CAP
  measurements of the 1.2 V n- and pFET (10/0.13 µm) at 233, 300, 343
  and 398 K.
  - The measured die sits 8–10 % below the spec's typical Idsat, so
    absolute values are printed for information only.
  - What is checked is each quantity's shift from 300 K, model against
    silicon:
    - Idsat ratio within 2 %;
    - Ioff within 0.2 decade;
    - Vtlin and Vtsat within 10 mV.
  - 18 of the 24 shifts match.
  - The other 6 are reported as known deviations, all at the
    temperature extremes:
    - At 233 K the model's leakage falls about 0.45 decade more than
      silicon's.
    - At 398 K the model's thresholds drop 11–18 mV more than silicon's.
  - This is one die, so it shows where the model's temperature
    behaviour departs from silicon, not a production spread.
- **Not checked.**
  - SKY130, ASAP7 and ASAP5 publish no temperature data.
  - TR-1um publishes R(T) and C(T) only as plots. Its models follow its
    plotted simulation, which differs from its plotted measurements.

### Related work and explanations

A web search (October 2026) found no earlier report of any of these known
deviations, and no other cross-PDK suite like this one. Related work:

- GF180MCU's model repository has its own regression suite. It compares
  ngspice with foundry measurements (`models/ngspice/testing/regression`,
  data in `180MCU_SPICE_DATA`). However, its "measured" MIM C(T) data
  reproduces the model's 40.6 ppm/K exactly, so it is model output, not
  independent silicon.
- IHP's `libs.tech/gnucap/tests` compares simulator outputs against
  stored golden outputs. It doesn't check against the spec or silicon.

The same search explained several deviations:

- **ASAP5.** The author's dissertation (Vashishtha, ASU 2019) confirms
  the DIBL method: 50 mV linear drain bias, Vt at 50 nA. Its earlier
  tables give different SRAM values, so the shipped nmos_sram card was
  revised after the paper's Table 8 was made.
- **IHP SG13CMOS5L vs SG13G2 v0.3.0.** Leakage differs between them
  because PSP's model code moved from 103.6 to 103.8.2 (IHP-Open-PDK
  PR #931). Their parameter files are identical.
- **Reported upstream** (October 2026):
  - [IHP-Open-PDK#1259](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1259):
    the LV pFET's Idsat is about 5 % low at all corners, and `mos_ss` is
    below the spec minimum.
  - [gf180mcu_fd_pr#46](https://github.com/fossi-foundation/globalfoundries-pdk-libs-gf180mcu_fd_pr/issues/46):
    the 1.5 fF/µm² MIM's TC1 is outside the spec.
  - [skywater-pdk#450](https://github.com/google/skywater-pdk/issues/450):
    the device tables' FS/SF columns contradict each other.
- **Still unexplained:**
  - SKY130's narrow-nFET Vt;
  - SkyWater's contradictory FS/SF columns;
  - ASAP7's DIBL column (one untested guess: normalising to a 0.9 V
    supply gives the 1.31× factor);
  - ASAP5's SS offset.

## Licences

This repository's own files are **MIT** ([LICENSE](LICENSE)). Each PDK's
upstream LICENSE and NOTICE files are kept verbatim in `pdks/<pdk>/`.
Nothing else upstream is committed here: bootstrap downloads it. Notices:
[NOTICE](NOTICE).

| Component | SPDX | Applies to | Redistribution terms |
|---|---|---|---|
| ASAP7 PDK r1p7 | `BSD-3-Clause` | the asap7_pdk_r1p7 repository | Permitted with the copyright notice and disclaimer; ASU's or the authors' names may not be used to endorse derived products. Its `docs/` include the journal paper, which is under the publisher's copyright; we don't redistribute it. Its Calibre decks are distributed separately by ASU and are not fetched. |
| SKY130: sky130_fd_pr and the open_pdks build | `Apache-2.0` | model files, ngspice library | Permitted with the licence and notices kept. No upstream NOTICE file. |
| GF180MCU: gf180mcu_fd_pr | `Apache-2.0` | model files | As above; `AUTHORS` kept. |
| IHP-Open-PDK, ihp-sg13cmos5l | `Apache-2.0` | model files, specs | As above. |
| ↳ PSP 103.6, JUNCAP 200 (SG13G2) | `ECL-2.0` | Verilog-A, compiled `.osdi` | Permitted under ECL-2.0. |
| ↳ PSP 103.8.2, JUNCAP 200 (SG13CMOS5L) | none (NXP / TU Delft / CEA terms) | Verilog-A, compiled `.osdi` | Modify, copy and redistribute; no charge for their code itself; acknowledge them in product documentation; keep the notice, disclaimer and conditions, including with binaries. |
| ↳ R3_CMC | `ECL-2.0` | Verilog-A, `.osdi` | `LICENSE.txt` and `NOTICE.txt` kept in `pdks/ihp-*/`. |
| ↳ MOSVAR | none (ASU / Si2 terms) | Verilog-A, `.osdi` | Terms in the file header; same four conditions as PSP 103.8.2. |
| ASAP5 r0p4 | `BSD-3-Clause` | the asap5 repository | As ASAP7. Only `LICENSE` and the model cards are fetched; its `docs/` also ship the journal paper. |
| TR-1um | `Apache-2.0` | model files, docs | Permitted with the licence and notices kept; `LICENSE` and `IP62-LICENSE.txt` are kept verbatim. Corner models are not public, and aren't shipped. |
| BSIM-CMG 107.0.0 (ASAP7, ASAP5) | none (`LicenseRef-BSIM-CMG`) | Verilog-A and `.osdi` | UC Berkeley grants the right to modify, copy and redistribute, on four conditions: no charge for the UC code itself; acknowledge UC Berkeley; obey US export rules; keep the copyright notice. The header is titled "NONDISCLOSURE STATEMENT", but its text grants these rights. We commit none of it; `prepare.sh` carries only the edits. |
| OpenVAF-reloaded v24.0.2mob | `GPL-3.0-only` | the compiler binary | Redistributing the binary requires offering the source. We don't redistribute it, and we don't publish compiled `.osdi` files. |
| ngspice 47 | `BSD-3-Clause` (core) plus `LGPL-2.0-or-later`, `MPL-2.0` (`src/osdi`), `GPL-2.0-or-later` (one XSPICE model) and public-domain parts | the simulator | Built locally from the pinned source; not redistributed. |

## Limitations

- **ASAP7 and ASAP5 are predictive, not foundry-accurate.** They are
  academic models of plausible 7 nm and 5 nm processes; no fab
  manufactures them. The other four are
  real processes, but their open models are what the foundries published,
  not a substitute for a foundry's sign-off flow.
- Device simulation only. No DRC, LVS or extraction, and no standard-cell
  libraries are fetched.
- Corner checks are only as strong as the published corner data (see
  "Corners"). Temperature checks cover passives only (see
  "Temperature"): no PDK here publishes transistor data at other
  temperatures. TR-1um has only a typical corner.
- Platforms: tested on macOS arm64 and Linux x86_64 (Ubuntu 24.04).
  macOS x86_64 should work, since OpenVAF-reloaded publishes a build, but
  it is untested. There is no Linux arm64 build of OpenVAF-reloaded, so the
  OSDI-based PDKs (`asap7`, `ihp-*`) can't run there.

## Considered and not included

We surveyed the open PDKs available in October 2026. These were left out:

| PDK | Why not |
|---|---|
| sky130B | Its ngspice library and device models are byte-identical to sky130A's in the pinned release; use `sky130`. |
| GF180MCU A–D variants | They differ only in metal stack and share the same device models. |
| FreePDK3 (NCSU) | Runs with one edit, but there are no published device values to check against, and the authors call the models a preliminary "first glimpse". |
| FreePDK45 / FreePDK15 (NCSU) | Download behind a registration wall. FreePDK15 is non-commercial and never shipped models. |
| PTM model cards (ASU / UMN) | No stated licence, Google Drive hosting, no reference values. |
| ICsprout55 | No SPICE models in the release. |
| SKY90-FD | Announced in 2022, archived without models. |
| MOSIS SCMOS | Design rules only; the model cards are no longer published. |
| Cadence GPDK, Synopsys SAED | Licence agreements required. |

## Repository layout

```
bootstrap.sh              one-command setup (core); per-PDK logic in pdks/<pdk>/setup.sh
tools/                    pinned toolchain (versions.lock, bsimcmg107.sha256)
pdks/<pdk>/               pins, checksums, upstream LICENSE/NOTICE files, README
ngspice/                  model-loading glue and ADAPTATIONS.md
sanity/                   run.py, shared helpers and decks; sanity/<pdk>/ per PDK
.github/workflows/ci.yml  Linux + macOS: bootstrap and sanity for every PDK
```

## Citing

If you publish results that use ASAP7, cite: L. T. Clark et al., "ASAP: A
7-nm finFET predictive process design kit," *Microelectronics Journal*
53 (2016) 105–115, doi:10.1016/j.mejo.2016.04.006. For ASAP5: V.
Vashishtha and L. T. Clark, "ASAP5: A predictive PDK for the 5 nm node,"
*Microelectronics Journal* 126 (2022) 105481,
doi:10.1016/j.mejo.2022.105481. BSIM-CMG is by the BSIM
Group, UC Berkeley. PSP and JUNCAP are by NXP Semiconductors, TU Delft and
CEA-Leti.
