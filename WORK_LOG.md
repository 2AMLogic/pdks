# Work Log

Chronological record of merged pull requests and closed issues, newest first.
Maintained by the Guide role's document-maintenance phase; entries are appended
from the tracker, never rewritten. The tracker remains authoritative for
anything still open — see WORK_PLAN.md for current state.

### 2026-11-17

- **PR #103**: docs: list every top-level file in README's Repository layout block
- **Issue #102** (closed): README "Repository layout" block does not list WORK_LOG.md and WORK_PLAN.md

### 2026-11-15

- **PR #100**: docs(gf180mcu): state PUB_TOL's real window terms, not a sum that misses it
- **PR #101**: refactor(sanity): share the mismatch area-scaling and same-seed check emitters
- **Issue #91** (closed): Dedupe the triplicated mismatch area-scaling and same-seed checks into sanity/common.py
- **Issue #99** (closed): gf180mcu PUB_TOL comment: the sampling term names 100 pairs (7 %), but the window gates a 200-device sigma (5.0 %)

### 2026-11-14

- **PR #98**: docs: give the gf180mcu mismatch notes their sampling-error terms
- **PR #97**: refactor: take the IHP mismatch supply and tag from CLASSES
- **PR #96**: chore: make root package.json scripts honest — point at bootstrap.sh, exit 1
- **PR #92**: docs: record that both gf180mcu 3.3 V par_vth sit ~20 % below their plotted line
- **PR #87**: refactor(sanity): share mc_tol and noise_deck from sanity/common.py
- **PR #82**: fix: fail bootstrap's render() on unfilled @KEY@ placeholders
- **PR #67**: docs: roadmap as of 2026-11-13
- **Issue #94** (closed): gf180mcu mismatch note: the ~7 % Vtlin swing is pooled, the verdict is one area's sample
- **Issue #90** (closed): Remove or make honest the Loom-scaffold package.json: four npm scripts that exit 0 saying this repo has no tests
- **Issue #89** (closed): Fold MM_CLASSES's duplicated vdd and derivable tag into CLASSES, finishing PR #75's dedup
- **Issue #85** (closed): gf180mcu mismatch: record that both 3.3 V par_vth sit ~20 % below their plotted fit line
- **Issue #84** (closed): Dedupe two shared sanity helpers: three identical mc_tol copies and a one-token-apart noise_deck pair
- **Issue #79** (closed): bootstrap.sh's render() ships unfilled @KEY@ placeholders silently, unlike sanity/common.py's
- **PR #86**: refactor: read SKY130's installed spiceinit instead of a hardcoded copy
- **PR #83**: refactor: call the num accessor in tr1um and predictive interconnect checks
- **PR #77**: feat(sky130): check pfet_01v8 mismatch, parameterising the deck by device
- **PR #76**: feat(gf180mcu): check pfet_03v3 mismatch against GF's plotted PMOS lines
- **PR #75**: feat: extend IHP mismatch and noise checks to the pMOS devices
- **PR #74**: refactor(sanity): share the interconnect table load, gap check and Elmore loop
- **PR #73**: feat(asap7): check DIBL against a recovered 0.85 V normalisation
- **Issue #81** (closed): Use the num accessor load_interconnect already returns: tr1um and predictive still inline float(val[...]["value"])
- **Issue #80** (closed): Remove the hardcoded SPICEINIT literal in sanity/sky130/checks.py: read the installed spiceinit, as IHP already does
- **Issue #72** (closed): Dedupe the interconnect sanity boilerplate: five copies of the table load, gap check and Elmore loop
- **Issue #71** (closed): ASAP7 sanity: test whether the paper's DIBL column is normalised to a 0.9 V supply
- **Issue #70** (closed): SKY130 sanity: add a pfet_01v8 mismatch check
- **Issue #69** (closed): IHP sanity: add pMOS mismatch and noise checks for the 1.2 V and 3.3 V devices
- **Issue #68** (closed): GF180MCU sanity: add a pfet_03v3 mismatch check against GF's plotted PMOS lines

### 2026-11-12

- **PR #65**: Bump Repo Skills 0.25.10 -> 0.26.1

### 2026-11-10

- **PR #64**: refactor(bootstrap): share one interconnect.inc generator across all PDKs
- **PR #62**: refactor(ngspice): share one BSIM-CMG noise deck across ASAP7 and ASAP5
- **PR #61**: refactor(sanity): use common.elmore in sky130 and gf180mcu, drop duplicate decks
- **PR #59**: docs(ngspice): cite shared wire.inc in ADAPTATIONS.md
- **PR #56**: refactor(ngspice): share one wire.inc across PDKs, make w required
- **PR #55**: refactor(sanity): share Elmore helper, wire deck and ASAP interconnect checks
- **PR #52**: feat: add SKY130 and GF180MCU interconnect tables, wire ladders and Elmore checks
- **PR #51**: feat(ihp): add nMOS mismatch and noise examples with derived sanity checks
- **PR #50**: feat(asap): add noise decks and derived checks; document no mismatch model
- **PR #49**: feat(gf180mcu,tr1um): add mismatch and noise examples with derived sanity checks
- **PR #48**: feat(ihp): add interconnect table, shared wire ladder and Elmore checks for SG13G2 and SG13CMOS5L
- **PR #47**: feat(asap5): add interconnect layer table, RC wire ladder and Elmore sanity checks
- **PR #46**: feat(tr1um): add M1/M2/V1 interconnect table, wire include and Elmore sanity checks
- **PR #38**: feat(sky130): add mismatch and noise examples with derived sanity checks
- **PR #36**: feat(asap7): interconnect layer table, RC wire ladder and Elmore checks
- **Issue #63** (closed): Dedupe interconnect.inc generator: five setup.sh copy the awk that ihp_interconnect already shares
- **Issue #60** (closed): Dedupe ASAP5/ASAP7 noise.sp.in into one shared template
- **Issue #58** (closed): ADAPTATIONS.md names deleted per-PDK wire.inc paths
- **Issue #57** (closed): Remove duplicate Elmore helper and wire decks in sky130/gf180mcu sanity checks
- **Issue #54** (closed): Share one wire.inc ladder across PDKs (follow-up to #53)
- **Issue #53** (closed): Dedupe ASAP5/ASAP7 interconnect and Elmore sanity checks into one shared helper
- **Issue #45** (closed): Mismatch and noise models and checks: ASAP7 and ASAP5 (predictive) (part of #37)
- **Issue #44** (closed): Mismatch and noise models and checks: IHP SG13G2 and SG13CMOS5L (part of #37)
- **Issue #43** (closed): Mismatch and noise models and checks: gf180mcu and tr1um (part of #37)
- **Issue #42** (closed): Interconnect parasitics table and checks for tr1um (part of #34)
- **Issue #41** (closed): Interconnect parasitics table and checks for ihp-sg13g2 and ihp-sg13cmos5l (part of #34)
- **Issue #40** (closed): Interconnect parasitics table and checks for sky130 and gf180mcu (part of #34)
- **Issue #39** (closed): Interconnect parasitics table and checks for ASAP5 (part of #34)
- **Issue #37** (closed): Mismatch and noise models and checks for the PDKs other than SKY130 (follow-up to #35)
- **Issue #35** (closed): Mismatch (Monte Carlo) and noise models per PDK, with examples and published-value checks
- **Issue #34** (closed): Interconnect parasitics tables and checks for the PDKs other than ASAP7 (follow-up to #33)
- **Issue #33** (closed): Interconnect parasitics per metal layer for each PDK, with an RC-ladder include and published-value checks (ASAP7 first)

### 2026-11-07

- **PR #32**: Bump Repo Skills 0.19.9 -> 0.25.10

### 2026-11-06

- **PR #31**: feat(sanity): check SKY130 LVT nFET and LVT/HVT pFET against e-test windows
- **PR #26**: fix(bootstrap): print full ngspice output when the smoke test fails
- **Issue #30** (closed): SKY130 sanity: check the 1.8 V LVT and HVT FETs against SkyWater's e-test windows

### 2026-11-05

- **PR #29**: refactor(sanity): share wrdata parser, tc_fit and render across PDK checks
- **PR #28**: fix(bootstrap): compile OSDI for a generic CPU target
- **PR #23**: refactor(sanity): run ASAP7 device sweeps through shared mos_sweeps
- **Issue #27** (closed): Compile OSDI models for a portable CPU target so cached .osdi files don't SIGILL
- **Issue #25** (closed): Consolidate duplicated sanity helpers (tc_fit, wrdata parser, render wrapper)
- **Issue #22** (closed): Remove ASAP7 private sweep deck: duplicate of shared mos_iv.sp

### 2026-11-04

- **PR #21**: chore(pdks): re-pin sky130 and gf180mcu to open_pdks f6eeac7
- **PR #20**: ci: move macOS matrix leg from retired macos-14 to macos-15
- **PR #19**: chore(loom): Install Loom 0.19.1262
- **PR #17**: Build(deps): bump actions/upload-artifact from 7.0.1 to 7.0.2 in the github-actions group across 1 directory
- **Issue #18** (closed): CI: move macos-14 runner pins to macos-15 before the 2026-11-02 image retirement
- **Issue #16** (closed): Re-pin open_pdks to f6eeac7 (ciel) — fleet retires volare c6d73a3

### 2026-10-13

- **PR #15**: Remove Renovate config: Dependabot takes over
- **PR #14**: Dependabot: render dependabot.yml from the org policy

### 2026-10-11

- **Issue #12** (closed): Dependency Dashboard

### 2026-10-10

- **PR #13**: renovate: move onto the 2AMLogic org preset

### 2026-10-06

- **PR #11**: Add Renovate config for the pinned GitHub Actions
- **PR #10**: Docs: fix three statements that no longer match the scripts
- **PR #9**: Docs: fix four stale README statements; update Repo Skills to 0.19.9
- **PR #8**: Record the maintainers' replies to the three upstream reports
- **PR #7**: Docs: fix three references left stale by recent changes
- **PR #6**: Check IHP measured silicon over temperature and SKY130 continuous models; link upstream reports

### 2026-10-05

- **PR #5**: Check passive devices and their published temperature coefficients
- **PR #4**: Check process corners wherever the PDK publishes corner data
- **PR #3**: Add TR-1um and IHP 3.3 V checks; record PDKs left out
- **PR #2**: Add ASAP5; pin SG13CMOS5L to one IHP-Open-PDK commit
- **PR #1**: Add SKY130, GF180MCU, IHP SG13G2 and SG13CMOS5L

