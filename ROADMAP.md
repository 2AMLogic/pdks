# Roadmap

This repository sets up open process design kits for ngspice with one command
and checks each one against its foundry's or authors' published values.

Status as of 2026-11-13, `main` @ `c58e634`.

## Where it stands

Seven PDKs install and pass their sanity checks in CI on `ubuntu-24.04` and
`macos-15` (`ci` is green on `c58e634`). Counts are from the README table.

| PDK | Checks | Known deviations | Mismatch | Noise |
|---|---|---|---|---|
| `asap7` | 126/126 | 0 | not modelled (predictive) | derived checks |
| `asap5` | 116/116 | 1 | not modelled (predictive) | derived checks |
| `sky130` | 105/105 | 8 | nFET `nfet_01v8`, derived | derived checks |
| `gf180mcu` | 120/120 | 3 | `nfet_03v3`, derived and against GF's plotted lines | derived checks |
| `ihp-sg13g2` | 200/200 | 8 | 1.2 V and 3.3 V nMOS, derived | derived checks |
| `ihp-sg13cmos5l` | 153/153 | 2 | 1.2 V and 3.3 V nMOS, derived | derived checks |
| `tr1um` | 34/34 | 2 | none published (gap) | BSIM3v3 defaults |

What landed to get here, all merged:

- **Device, corner and temperature checks** for every PDK, each labelled
  published, bound or derived (`sanity/<pdk>/reference.py`,
  `sanity/ihp_spec.py`). SKY130's LVT and HVT 1.8 V FETs were added in #31.
- **Interconnect** for all seven: a per-layer `interconnect.csv` with each
  quantity marked published, derived or gap, a shared `ngspice/wire.inc` RC
  ladder and Elmore-delay checks (#33, #34; PRs #36, #46, #47, #48, #52).
- **Mismatch and noise** examples and checks for all seven, or a documented
  "not modelled" where the cards carry no statistics (#35, #37; PRs #38, #49,
  #50, #51).
- **Deduplication** of the helpers those efforts copied (#53, #54, #57, #60,
  #63).
- **Pins**: SKY130 and GF180MCU re-pinned to open_pdks `f6eeac7` (#16);
  OSDI models compile for a generic CPU target (PR #28).
- **Upstream reports** filed for three deviations, with the maintainers'
  replies recorded in the README ("Related work and explanations").

The tracker's open feature work is #68 to #71, the issues for Now 1 to 4
below; see also "Blocked and waiting".

## Now

Each item can start today and fits one pull request. Items 1 to 4 are filed as
#68 to #71; item 5 has no issue yet. Items 1 to 3 extend coverage the
repository's own files list as "not covered" or "not exercised"; every new
reference value is cited, never fitted.

1. **GF180MCU: `pfet_03v3` mismatch check** (#68). `pdks/gf180mcu/README.md`
   lists pFET mismatch as not covered, and GF's Model Reference Guide 9.4
   plots the 3.3 V PMOS lines next to the NMOS ones already used. Done when
   `sanity/gf180mcu` runs the area-scaling check on `pfet_03v3`, compares it
   with the digitised PMOS lines, and the README count and "Not covered" row
   are updated.
2. **IHP: pMOS mismatch and noise checks, 1.2 V and 3.3 V** (#69). The pMOS
   coefficients sit in lines 25-28 of `sg13g2_mos{lv,hv}_mismatch.lib`;
   `sanity/ihp_spec.py` lists pMOS as "not exercised". Done when both IHP
   PDKs run the same area-scaling, floor and noise checks on `sg13_lv_pmos`
   and `sg13_hv_pmos`, and that gap line is narrowed to the passives.
3. **SKY130: `pfet_01v8` mismatch check** (#70). `pfet_01v8` carries the
   mismatch switch (`pdks/sky130/README.md`), but only `nfet_01v8` is
   checked. Done when the pFET passes the area-scaling and `vth0_slope` floor
   checks, with the slope values cited by file and line, and the added run
   time is stated in the README.
4. **ASAP7: test the DIBL normalisation guess** (#71). The README records
   "one untested guess": that the paper's DIBL column is normalised to a
   0.9 V supply. Done when `sanity/asap7/reference.py` records the result for
   all eight devices, and DIBL either becomes a checked quantity with a
   stated tolerance or stays information-only with the guess marked as
   refuted.
5. **README "Repository layout" names a deleted file.** It lists
   `renovate.json`, which was removed in PR #15; `.github/dependabot.yml`
   replaced it. Done when the layout block matches `git ls-files` at the top
   level and names this roadmap.

## Next

- **Mismatch for the remaining MOS devices**: GF180MCU 5 V and 6 V FETs, and
  SKY130's LVT, HVT, 3.3 V and 5 V devices that carry the switch. Follows Now
  1 and 3, which set the pFET pattern. Done when each device listed in the
  PDK README's mismatch "Where" row has a check or a stated reason it has
  none. pMOS noise for both PDKs follows the pattern Now 2 sets for IHP.
- **Shorten the SKY130 Monte Carlo run.** The README says the loop re-reads
  the library for every sample and adds several minutes. Follows Now 3, which
  lengthens it. Done when the SKY130 CI leg's sanity time is lower than
  before with identical `sanity-results.json` values for the same seeds.
- **Mismatch of passives and the HBT** where the PDK ships a statistical
  model: IHP resistors, MIM, MOS and varactor capacitors and the SG13G2 HBT
  (`*_mod_mismatch.lib`), GF180MCU resistors, BJTs and MIM capacitors. Follows
  Now 1 and 2. Done when each has a derived check or a documented gap.

## Later

- **The four deviations the README lists as "still unexplained"** (SKY130
  narrow-nFET Vt, the FS/SF transposition, ASAP7's DIBL column, ASAP5's SS
  offset). Question first: is there a published source or maintainer reply
  that settles each one? Now 4 addresses the ASAP7 one; for FS/SF, the reply
  to skywater-pdk#450 leaves open which maintained repository owns the tables.
- **Pin refreshes** (ngspice, OpenVAF-reloaded, each PDK). Question first:
  does the newer release change any checked value? A pin change means a new
  checksum file and a full sanity re-run (`CLAUDE.md`).
- **Linux arm64 and macOS x86_64.** The README says there is no Linux arm64
  build of OpenVAF-reloaded and that macOS x86_64 is untested. Question first:
  has upstream published an arm64 build, and is there a runner to test on?
- **More PDKs.** "Considered and not included" in the README gives the reason
  for each one left out. Question first: has that reason changed, and does
  the PDK publish values to check against?

## Blocked and waiting

- **#24, intermittent "example deck failed" on the Ubuntu ASAP legs.** The
  diagnostic shipped in PR #26 and `ci` has been green since; the issue now
  waits on a maintainer to re-run the two jobs, compare
  `sanity-results.json`, and close it or file a root-cause follow-up. It is
  labelled `loom:operator`, so it is not agent work.
- **#66** is an automated digest, not a work item; it reports no held PRs.
- **Gaps that only an upstream publication can close**: capacitance per
  length on every PDK, sheet and via resistance for ASAP7, ASAP5 and TR-1um,
  noise levels and Pelgrom coefficients everywhere. They stay marked `gap` in
  `interconnect.csv` and the reference files until a source prints a value.

The one open pull request is #67, this roadmap. Now 1 to 4 have issues (#68 to
#71), so the tracker has feature work to pick up; Now 5 still needs one.

## Not planned

- **Estimating a value nobody published.** Gaps stay gaps; references are
  cited, not fitted (`CLAUDE.md`).
- **Committing upstream PDK files, Verilog-A sources or compiled `.osdi`
  files.** They are pinned and fetched at setup; only upstream LICENSE and
  NOTICE files are kept here.
- **DRC, LVS, extraction or standard-cell libraries.** The README's
  "Limitations" scopes this repository to device simulation; "Considered and
  not included" rules out PDKs behind a licence agreement or registration.
