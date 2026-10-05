# Open PDKs for ngspice

One command to set up open process design kits for analog and mixed-signal
simulation in [ngspice](https://ngspice.sourceforge.io), on a fresh macOS
or Linux host. Each upstream source is pinned by commit or SHA-256 and
fetched at setup, so the clone is small. The setup is reproducible, and
results are checked against published values.

| PDK | Status | What you get |
|---|---|---|
| **ASAP7** r1p7: 7 nm predictive FinFET (ASU / Arm) | supported | TT/FF/SS model cards for ngspice, BSIM-CMG 107 compiled to OSDI, sanity checks against the PDK paper |
| SKY130, GF180MCU, IHP SG13G2 | planned | not yet: same pattern to follow |

## Quick start

```sh
git clone https://github.com/2AMLogic/pdks && cd pdks
./bootstrap.sh --pdk asap7            # installs to ~/pdks; --prefix DIR to change
. ~/pdks/env.sh                       # puts the pinned ngspice on PATH
ngspice -b ~/pdks/asap7/ngspice/example.sp
```

The first run takes about 2–3 minutes: ngspice is built from source. A
re-run skips finished steps and takes a few seconds. You need the Xcode
Command Line Tools on macOS, or `build-essential bison flex curl git python3
libllvm18` on Debian/Ubuntu. On apt-based systems bootstrap installs those
itself (`--no-prereqs` to skip).

In your own deck:

```spice
* corner: tt, ff or ss
.lib "/home/you/pdks/asap7/ngspice/models/asap7.lib" tt
* OSDI devices take the N prefix
Nn1 out in 0   0   nmos_rvt l=20n nfin=3
Np1 out in vdd vdd pmos_rvt l=20n nfin=3
.control
* load BSIM-CMG first (or copy asap7/ngspice/spiceinit to ~/.spiceinit)
pre_osdi /home/you/pdks/tools/bsimcmg107/bsimcmg107.osdi
...
```

Devices: `{n,p}mos_{slvt,lvt,rvt,sram}`, gate length `l=20n` drawn, width
set by `nfin`.

## What `bootstrap.sh` does

1. Checks prerequisites (and installs them with apt-get where it can).
2. Fetches and verifies every pinned source, then builds the toolchain:

   | Component | Pin | Verified by |
   |---|---|---|
   | ngspice | 47, source release | SHA-256 (`tools/versions.lock`) |
   | OpenVAF-reloaded | v24.0.2mob release binary | SHA-256 per platform |
   | BSIM-CMG Verilog-A | 107.0.0, CedarEDA/CMC.jl @ `548cc7a` | SHA-256 per file (`tools/bsimcmg107.sha256`) |
   | ASAP7 PDK | asap7_pdk_r1p7 @ `58d72c9` | git commit + SHA-256 of cards (`pdks/asap7/`) |

3. Builds ngspice with OSDI support and compiles BSIM-CMG to `bsimcmg107.osdi`.
4. Adapts the model cards as little as possible. Every change is in
   [`ngspice/ADAPTATIONS.md`](ngspice/ADAPTATIONS.md): two edits to the
   Verilog-A and one header line per `.model` card. Outputs are checked
   against recorded hashes.
5. Runs a smoke test and the sanity checks below.

Directories it creates carry a stamp file. It refuses to overwrite a
directory it did not create.

## Sanity checks

`sanity/run.py` simulates the decks in `sanity/decks/` at TT, 25 °C, 0.7 V.
Each check is labelled with where its reference value comes from. Sources,
extraction definitions and tolerances are in
[`sanity/reference.py`](sanity/reference.py).

| Check | Reference | Result (current pins) |
|---|---|---|
| n/pFET Id–Vg and Id–Vd, all 8 devices: Idsat, Ieff, Ioff, Vtlin, Vtsat, SS | **Published**: Clark et al. 2016, Tables 3–4 (per fin) | Idsat and Ieff within 0.04 %, Vt within 5 mV, SS within 0.4 mV/dec, Ioff within printed rounding |
| FO4 delay, RVT / LVT / SLVT | **Bound**: Clark et al., MSE 2017 (8.1 / 6.8 / 6.0 ps *post-layout*) | 7.7 / 6.4 / 5.7 ps pre-layout: below the published values, as expected without wire RC |
| Inverter VTC (INVx1, RVT) | **Derived**: no published VTC | switching point 0.343 V, peak gain 35, full swing |
| 11-stage ring oscillator, 0.7 V (INVx1, RVT) | **Derived**: no published RO figure | 16.3 GHz; stage delay 2.8 ps = 0.36 × FO4 (logical effort predicts about 0.4) |

The paper doesn't state how it extracted Ioff, Vt or SS. We use the
definitions that reproduce its tables for every device at once:

- Ioff is channel current, which excludes GIDL.
- Vt is the gate voltage at a constant current of 10 nA per fin.
- SS is the gate swing across the decade from 10 to 100 nA.

DIBL is printed for information but not checked. Our Vtlin and Vtsat each
match the paper's, but our DIBL, (Vtlin − Vtsat) / 0.65 V, is a uniform
1.32× the paper's DIBL column for all eight devices. That points to a
different, unstated normalisation rather than a model difference.

## Licences

This repository's own files are **MIT** ([LICENSE](LICENSE)), except
`pdks/asap7/LICENSE`, which is upstream's verbatim. Nothing below is
committed here: bootstrap downloads each component from its upstream.
Third-party notices: [NOTICE](NOTICE).

| Component | SPDX | Applies to | Redistribution terms |
|---|---|---|---|
| ASAP7 PDK r1p7 | `BSD-3-Clause` | the asap7_pdk_r1p7 repository: model cards, tech files, docs | Permitted with the copyright notice and disclaimer; ASU's or the authors' names may not be used to endorse derived products. |
| ↳ `docs/mej_paper_asap7.pdf` | none (publisher's copyright) | the journal paper shipped inside the upstream repo | Fetched with the pinned checkout; we cite it but do not redistribute it. |
| ↳ Calibre DRC/LVS decks | none (ASU download terms) | physical verification decks | Distributed separately by ASU; not fetched or used. |
| BSIM-CMG 107.0.0 | none (`LicenseRef-BSIM-CMG`) | the Verilog-A model and the compiled `.osdi` | UC Berkeley grants the right to modify, copy and redistribute, on four conditions: no charge for the UC code itself; acknowledge UC Berkeley in product documentation; obey US export rules; reproduce the copyright notice. The header is titled "NONDISCLOSURE STATEMENT", but its text grants these rights. We fetch the source and commit none of it; `prepare.sh` carries only the edits. |
| CMC.jl packaging | upstream licence, or `MIT` | CedarEDA's repackaging changes | at the user's option |
| OpenVAF-reloaded v24.0.2mob | `GPL-3.0-only` | the compiler binary (bundled LLVM, z3, zstd under their own permissive licences) | Redistributing the binary requires offering the source. We don't redistribute it, and we don't publish compiled `.osdi` files. |
| ngspice 47 | `BSD-3-Clause` (core) plus `LGPL-2.0-or-later`, `MPL-2.0` (`src/osdi`), `GPL-2.0-or-later` (one XSPICE model) and public-domain parts, per its COPYING | the simulator | Built locally from the pinned source release; not redistributed. |

## Limitations

- **ASAP7 is predictive, not foundry-accurate.** It is an academic model
  of a plausible 7 nm process for research and teaching. No fab
  manufactures it, and results don't predict silicon.
- Device simulation only. No DRC, LVS or extraction: ASAP7's decks are
  Calibre-only and distributed separately. The standard-cell libraries are
  not fetched.
- BSIM-CMG is compiled with upstream's defaults: self-heating, NQS and
  gate-resistance models are compiled out. The ASAP7 cards turn them off
  anyway.
- The sanity checks cover TT only. FF and SS cards are installed but not
  checked against published values (the paper shows them as plots only).
- Platforms: tested on macOS arm64 and Linux x86_64 (Ubuntu 24.04).
  macOS x86_64 should work, since OpenVAF-reloaded publishes a build, but
  it is untested. There is no Linux arm64 build of OpenVAF-reloaded. On Linux, OpenVAF needs `libLLVM` 18
  (Ubuntu 24.04: `libllvm18`).

## Repository layout

```
bootstrap.sh              one-command setup
tools/                    pinned toolchain (versions.lock, bsimcmg107.sha256)
pdks/asap7/               pinned upstream: commit, checksums, LICENSE, citation
ngspice/                  model-loading glue and ADAPTATIONS.md
sanity/                   decks, reference values, checker
.github/workflows/ci.yml  Linux + macOS: bootstrap, sanity, cached .osdi
```

## Citing

If you publish results that use ASAP7, cite: L. T. Clark et al., "ASAP: A
7-nm finFET predictive process design kit," *Microelectronics Journal*
53 (2016) 105–115, doi:10.1016/j.mejo.2016.04.006. BSIM-CMG is by the BSIM
Group, UC Berkeley.
