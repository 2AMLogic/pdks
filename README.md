# Open PDKs for ngspice

One command to set up open process design kits for analog and mixed-signal
simulation in [ngspice](https://ngspice.sourceforge.io), on a fresh macOS
or Linux host. Each upstream source is pinned by commit or SHA-256 and
fetched at setup, so the clone is small. The setup is reproducible, and
results are checked against each foundry's or author's published values.

| `--pdk` | Process | Models | Fetched | Sanity checks |
|---|---|---|---|---|
| `asap7` | ASAP7 r1p7: 7 nm predictive FinFET (ASU / Arm) | BSIM-CMG 107, compiled to OSDI | 9 MB | 65/65 against the PDK paper |
| `sky130` | SkyWater SKY130 (`sky130A`) | BSIM4, built in | 21 MB | 11/11 against SkyWater's e-test windows, plus 1 known deviation |
| `gf180mcu` | GlobalFoundries GF180MCU | BSIM4, built in | 1.4 MB | 18/18 against GF's EP targets and spec limits |
| `ihp-sg13g2` | IHP SG13G2 SiGe BiCMOS | PSP 103 (OSDI), VBIC HBT | 2.5 MB | 17/17 against IHP's process spec, including the HBT |
| `ihp-sg13cmos5l` | IHP SG13CMOS5L CMOS | PSP 103 (OSDI) | 5 MB | 14/14 against IHP's process spec |

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
| sky130 | `.lib ".../sky130/sky130A/libs.tech/ngspice/sky130.lib.spice" tt` | `X1 d g s b sky130_fd_pr__nfet_01v8 w=1 l=0.15` (µm) | `ngbehavior=hsa`, `ng_nomodcheck` |
| gf180mcu | `.include ".../design.ngspice"` then `.lib ".../sm141064.ngspice" typical` | `M1 d g s b nfet_03v3 w=1u l=0.28u` | none |
| ihp-* | `.lib ".../libs.tech/ngspice/models/cornerMOSlv.lib" mos_tt` | `X1 d g s b sg13_lv_nmos w=1u l=0.13u ng=1` | loads the PSP/R3/MOSVAR OSDI |

## What `bootstrap.sh` does

1. Checks prerequisites, installing them where it can.
2. Fetches and verifies every pinned source:

   | Component | Pin | Verified by |
   |---|---|---|
   | ngspice | 47, source release | SHA-256 (`tools/versions.lock`) |
   | OpenVAF-reloaded | v24.0.2mob release binary | SHA-256 per platform |
   | BSIM-CMG Verilog-A (ASAP7) | 107.0.0, CedarEDA/CMC.jl @ `548cc7a` | SHA-256 per file |
   | each PDK | commit or release asset, see `pdks/<pdk>/README.md` | git commit id or SHA-256 |

3. Builds ngspice with OSDI support and compiles the Verilog-A models the
   PDK needs.
4. Applies the minimum adaptations. Every one is listed, with its reason, in
   [`ngspice/ADAPTATIONS.md`](ngspice/ADAPTATIONS.md). ASAP7 needs three;
   the others need none to PDK files.
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
- **SKY130.** Vt, Idsat and leakage of the 1.8 V FETs, against SkyWater's
  e-test MIN–MAX windows ("Device Details" tables):
  - The tables' own TT-model column doesn't match the released models.
    Idsat is +4.7 % (n) and +7.7 % (p) above it; this is printed for
    information.
  - One row is a **known deviation**, reported on every run: the narrow
    0.42/1 µm nFET's Vt (0.60 V) is above its window.
- **GF180MCU.** Idsat and Vth0 of five FETs against GF's typical EP
  targets. All match to printed precision (e.g. 510.0 vs 510 µA/µm,
  0.630 vs 0.63 V). Ioff and subthreshold slope are checked against the
  electrical-spec limits.
- **IHP SG13G2 / SG13CMOS5L.** Every LV MOS row of IHP's process
  specification (Vt at three geometries, Idsat, Ioff, DIBL, SS), using
  the spec's own extraction definitions, within its MIN–MAX windows.
  SG13G2 adds the npn13G2 HBT: β 722 (spec 650 typ), Ic 3.69 µA (3.8),
  fT 353 GHz (≥ 300).

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
| BSIM-CMG 107.0.0 (ASAP7) | none (`LicenseRef-BSIM-CMG`) | Verilog-A and `.osdi` | UC Berkeley grants the right to modify, copy and redistribute, on four conditions: no charge for the UC code itself; acknowledge UC Berkeley; obey US export rules; keep the copyright notice. The header is titled "NONDISCLOSURE STATEMENT", but its text grants these rights. We commit none of it; `prepare.sh` carries only the edits. |
| OpenVAF-reloaded v24.0.2mob | `GPL-3.0-only` | the compiler binary | Redistributing the binary requires offering the source. We don't redistribute it, and we don't publish compiled `.osdi` files. |
| ngspice 47 | `BSD-3-Clause` (core) plus `LGPL-2.0-or-later`, `MPL-2.0` (`src/osdi`), `GPL-2.0-or-later` (one XSPICE model) and public-domain parts | the simulator | Built locally from the pinned source; not redistributed. |

## Limitations

- **ASAP7 is predictive, not foundry-accurate.** It is an academic model
  of a plausible 7 nm process; no fab manufactures it. The other four are
  real processes, but their open models are what the foundries published,
  not a substitute for a foundry's sign-off flow.
- Device simulation only. No DRC, LVS or extraction, and no standard-cell
  libraries are fetched.
- Sanity checks cover the typical corner. Other corners are installed but
  not checked.
- Platforms: tested on macOS arm64 and Linux x86_64 (Ubuntu 24.04).
  macOS x86_64 should work, since OpenVAF-reloaded publishes a build, but
  it is untested. There is no Linux arm64 build of OpenVAF-reloaded, so the
  OSDI-based PDKs (`asap7`, `ihp-*`) can't run there.

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
53 (2016) 105–115, doi:10.1016/j.mejo.2016.04.006. BSIM-CMG is by the BSIM
Group, UC Berkeley. PSP and JUNCAP are by NXP Semiconductors, TU Delft and
CEA-Leti.
