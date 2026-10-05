# Adaptations for ngspice

Every change made to upstream material so ngspice can simulate it, and why.
Upstream files are never edited in place: bootstrap writes adapted copies
and checks them against recorded SHA-256 sums, so every host gets identical
bytes.

## ASAP7 model cards (`asap7/adapt-models.sh`)

Input: `models/hspice/7nm_{TT,FF,SS}_160803.pm` from asap7_pdk_r1p7 at the
pinned commit. Output: `asap7/ngspice/models/7nm_{TT,FF,SS}.pm`.
Hashes: `asap7/adapted.sha256`.

| # | Change | Lines | Reason |
|---|---|---|---|
| A1 | `.model <name> nmos level = 72` → `.model <name> bsimcmg devtype=1`<br>`.model <name> pmos level = 72` → `.model <name> bsimcmg devtype=0` | the 8 `.model` lines per corner | ngspice has no built-in BSIM-CMG. An OSDI model is selected by its Verilog-A module name (`bsimcmg`), not by `level`. Polarity moves from the `nmos`/`pmos` keyword to BSIM-CMG's own `DEVTYPE` parameter (1 = n, 0 = p). |

Nothing else changes. Every parameter value is upstream's. One upstream
parameter has no effect in ngspice: `version = 107`. It is an HSPICE
model-selection key, and BSIM-CMG 107 has no `VERSION` parameter, so
ngspice prints `unrecognized parameter (version) - ignored` once per model.
That warning is expected. We leave the line alone rather than edit cards
for cosmetics.

Because devices are OSDI instances, netlists use the `N` prefix instead of
`M`: `Nn1 d g s b nmos_rvt l=20n nfin=3`.

## BSIM-CMG 107.0.0 Verilog-A (`bsimcmg107/prepare.sh`)

Input: the 12 pristine files from CedarEDA/CMC.jl at the pinned commit
(`tools/bsimcmg107.sha256`). Only `bsimcmg_body.include` changes. The
script checks the result against a recorded SHA-256 and carries only the
edits, none of the Berkeley source.

| # | Change | Reason |
|---|---|---|
| B1 | Prefix 26 parameters with `(*type="instance"*)`: `L D TFIN FPITCH NF NFIN NGCON ASEO ADEO PSEO PDEO ASEJ ADEJ PSEJ PDEJ COVS COVD CGSP CGDP CDSP NRS NRD LRSD DTEMP DELVTRAND U0MULT`. | OpenVAF makes a parameter an OSDI instance parameter only when it carries this attribute; untagged parameters are model-only. BSIM-CMG 107 predates the convention (110+ tag them through `IPRxx` macros), so without it `l=` and `nfin=` could not be set per device. The list is the set Xyce marks as instance parameters in its BSIM-CMG 107 port, plus NF (finger count) and DTEMP (device temperature offset), which are per-device by nature. Values and ranges are unchanged. |
| B2 | `EOTACC` lower bound `[0.1n:inf)` → `[1e-10:inf)`. | OpenVAF evaluates `0.1n` as `0.1 × 1e-9 = 1.0000000000000002e-10`, one ulp above `1e-10`. The ASAP7 cards set `eotacc = 1e-10`, which the bound allows. Without this edit, ngspice rejects it ("Parameter EOTACC is out of bounds") and aborts model setup. Writing the bound as the exact literal restores the intended inclusive limit. Fixing it here rather than nudging the card keeps the ASAP7 values untouched. (EOTACC is only used when `CAPMOD ≠ 0`; the ASAP7 cards use `capmod = 0`.) |

## macOS: OpenVAF-reloaded signature

The macOS release binaries of OpenVAF-reloaded v24.0.2mob carry
linker-only code signatures, and macOS kills the process on launch
(exit 137). Bootstrap re-signs `bin/openvaf-r` and `lib/*.dylib` ad hoc
(`codesign --force --sign -`) after verifying the tarball's SHA-256. This
changes the signature only, not the code.

## ngspice build options

ngspice 47 is built from its source release with `--enable-osdi
--with-x=no --with-readline=no --disable-openmp --disable-debug`.
OpenMP is off because Apple clang ships no `omp.h`, and it is off on
Linux too so both platforms build the same way. The sanity decks run
`ngspice -b -n`, which ignores any `~/.spiceinit`, so a user's
compatibility mode (for example `ngbehavior=hsa`) cannot change results.

## SKY130 (`pdks/sky130/setup.sh`)

No changes to PDK files. The library needs two ngspice settings, the same
ones the PDK's own `libs.tech/ngspice/spinit` makes: `set ngbehavior=hsa`
(HSPICE-compatible parsing for its model files) and `set ng_nomodcheck`.
Bootstrap writes them to `sky130/ngspice/spiceinit` and to a `.spiceinit` beside
`example.sp`.

## GF180MCU (`pdks/gf180mcu/setup.sh`)

No changes. The cards are ngspice-native BSIM4 and need no settings.

## IHP SG13G2 and SG13CMOS5L (`pdks/ihp-common.sh`)

No changes to PDK files. Two differences from the PDKs' own setup:

| # | What | Reason |
|---|---|---|
| I1 | OSDI models are compiled into `<pdk>/ngspice/osdi/` with the flags of the PDK's `openvaf-compile-va.sh` (`-D__NGSPICE__`), instead of running that script. | The script writes into the PDK's tracked tree. For SG13CMOS5L that tree holds prebuilt `cap_cmom*.osdi`, which are Linux x86-64 binaries and would be overwritten (and don't load on macOS). |
| I2 | Our spiceinit loads each `.osdi` by absolute path; the PDKs' `.spiceinit` uses `$PDK_ROOT/$PDK`. | Works without setting environment variables, and from any directory. |

For SG13CMOS5L, the SG13CMOS5L checkout sits inside an IHP-Open-PDK dev
checkout. That is the layout its README requires, because its MOS models
and Verilog-A are symlinks into `../ihp-sg13g2`.
