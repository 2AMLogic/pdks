# pdks

Public repo: one-command ngspice setup for open PDKs (README.md).

- **Public, generic material only.** No proprietary or foundry-NDA content,
  ever. Never commit upstream PDK files, Verilog-A sources or binaries;
  pin them (commit or SHA-256) and let `bootstrap.sh` fetch them. The one
  exception is upstream LICENSE/NOTICE files under `pdks/<name>/`, verbatim.
- **Pin everything.** No "latest", no floating tags (Actions pinned by SHA).
  Changing a pin means updating its checksum file and re-running the
  sanity checks.
- **Every change to upstream material** goes in `ngspice/ADAPTATIONS.md`
  with its reason, and its output hash is recorded (`adapted.sha256`,
  `prepare.sh`).
- **Sanity references are cited, not fitted.** `sanity/reference.py`
  labels each check published / bound / derived and documents every
  extraction definition.
- Test with `./bootstrap.sh --pdk <name>[,...] --prefix <scratch dir>`. On the
  operator's machine `~/pdks` already holds a separate hand-made install,
  and bootstrap will (correctly) refuse to write there.

<!-- BEGIN REPO-SKILLS -->
This repository has [Repo Skills](https://github.com/rjwalters/repo) v0.19.8 installed —
general repository hygiene and environment commands invoked as `/repo:<command>`. Run
`/repo:help` for the command list, or see `.claude/skills/repo/SKILL.md` for the full
guide. Hygiene commands apply safe, reversible fixes by default and report each
change; run with `--ask` to review first, and `--prune` to allow irreversible
removals. Managed by `install.sh` — edit outside the markers only.
<!-- END REPO-SKILLS -->
