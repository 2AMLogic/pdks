"""Mismatch and noise checks shared by the two predictive BSIM-CMG PDKs
(ASAP7, ASAP5). Each PDK's reference.py supplies the constants, their sources
and the gap list; see sanity/asap7/reference.py and sanity/asap5/reference.py.

Python 3.8+, stdlib only.
"""

import glob
import os
import re

from common import ngspice, render, results

# Parameters a card could use to describe variability (statistical functions
# and Monte Carlo hooks of HSPICE/Spectre/ngspice decks).
STATISTICAL = r"\b(agauss|gauss|aunif|unif|mc_\w+|mismatch\w*|monte\w*|sigma\w*|vary|lot|dev)\b\s*[=(/]"
NOISE_PARAMS = ("noia", "noib", "noic", "ntnoi", "ef", "em", "kf", "af", "lintnoi", "tnoimod")


def scan_cards(files):
    """(models, models with a noise parameter set, statistical hits) over the
    pinned upstream cards. Comment lines (leading '*') are ignored."""
    models = noisy = stat = 0
    for f in files:
        with open(f, errors="replace") as fh:
            text = "\n".join(l for l in fh.read().splitlines() if not l.lstrip().startswith("*"))
        blocks = re.split(r"(?im)^\s*\.model\s+", text)[1:]
        models += len(blocks)
        for b in blocks:
            noisy += any(re.search(r"(?i)\b%s\s*=" % k, b) for k in NOISE_PARAMS)
        stat += len(re.findall("(?i)" + STATISTICAL, text))
    return models, noisy, stat


def run_noise(ng, ngdir, work, name, deck_in, osdi, nfin, vg, vd):
    """Render the deck template ngspice/<pdk>/noise.sp.in and run it."""
    path = render(deck_in, work, name, NGSPICE=ng, MODELS_DIR=os.path.join(ngdir, "models"), OSDI=osdi,
                  NFIN=nfin, VG=vg, VD=vd, VGLO=round(vg - 0.002, 6), VGHI=round(vg + 0.002, 6))
    return results(ngspice(ng, path, cwd=work))


def checks(rep, data, ref, card_files, ngdir, deck_in, osdi, ng, work):
    print("\nMismatch and noise (predictive PDK: no measured statistics; reference.py)\n")
    models, noisy, stat = scan_cards(card_files)
    data["card_scan"] = dict(files=len(card_files), models=models, with_noise_params=noisy, statistical=stat)
    rep.check("cards: statistical/mismatch parameters", "derived", stat, 0, 0, "", 1,
              "(%d models in %d files; none, so no Monte Carlo deck)" % (models, len(card_files)))
    rep.check("cards: models setting a noise parameter", "derived", noisy, 0, 0, "", 1,
              "(%s default to BSIM-CMG 107's own values)" % "/".join(NOISE_PARAMS[:6]))
    rep.check("cards: model count", "derived", models, ref.CARD_MODELS, ref.CARD_MODELS, "", 1)

    b = ref.NOISE_BIAS
    r = run_noise(ng, ngdir, work, "noise", deck_in, osdi, b["nfin"], b["vg"], b["vd"])
    data["noise"] = r
    lo, hi = ref.NYQUIST
    rep.check("Nyquist S_id/(4kT*gds) at Vds=0", "derived", r["nyquist_ratio"], lo, hi, "", 1,
              "(nmos_rvt nfin=%d, Vg %.2f V)" % (b["nfin"], b["vg"]))
    rep.check("flicker slope 1..100 Hz = -ef", "derived", r["flicker_slope"], -ref.EF - ref.FLICKER_SLOPE_TOL,
              -ref.EF + ref.FLICKER_SLOPE_TOL, "", 1, "(BSIM-CMG default ef %.1f; cards set none)" % ref.EF)
    rep.info("thermal gamma (total, 4kT*gamma*gm)", r["gamma_total"], "", 1,
             "(information; includes S/D resistor and gate-current shot noise)")
    rep.info("flicker level at 1 Hz (input, V^2/Hz)", r["sv_input_1Hz_V2"], "V2/Hz", 1,
             "(BSIM-CMG default noia/noib/noic, not extracted: gap)")
    print("\nGaps (not estimated):")
    for g in ref.GAPS:
        print("  - " + g)
