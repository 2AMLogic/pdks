"""TR-1um sanity checks: drain current of the 5 V NMOS and PMOS at the
Table I-2-7 bias points against Tokai Rika's published simulation curves.
Sources and caveats: reference.py. Run via sanity/run.py --pdk tr1um.
"""

import glob
import os
import re
import tempfile

import reference as ref
from common import Report, at, ngspice, read_xy, render, results

DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "iv_points.sp")
NOISE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ngspice", "tr1um", "noise.sp.in")


def noise_deck(ng, work, models, name, bias):
    deck = render(NOISE_DECK, work, name, MODELS_DIR=models, NGSPICE=ng,
                  VGLO=bias["VG"] - 0.002, VGHI=bias["VG"] + 0.002, **bias)
    return results(ngspice(ng, deck, cwd=work))


def model_scan(models):
    """(statistical tokens in the model libraries, files scanned, MOS models,
    MOS models setting any noise parameter)."""
    hits = files = 0
    for f in sorted(glob.glob(os.path.join(models, "models_IP62_*.lib"))):
        files += 1
        text = open(f).read().lower()
        hits += sum(len(re.findall(re.escape(k), text)) for k in ref.MISMATCH_TOKENS)
    text = open(os.path.join(models, "models_IP62_mos_v2.lib")).read()
    mos = noisy = 0
    for b in re.split(r"(?im)^\.model\s+", text)[1:]:
        mos += 1
        noisy += any(re.search(r"(?im)\b%s\s*=" % k, b) for k in ref.NOISE_PARAMS)
    return hits, files, mos, noisy


def mismatch_and_noise(rep, data, models, ng, work):
    print("\nMismatch: no model (Tokai Rika Table I-1-2 \"Matching\": none). Scan of the model libraries:\n")
    hits, files, mos, noisy = model_scan(models)
    rep.check("mismatch scan: statistical terms in models", "derived", float(hits), 0, 0, "", 1,
              "(%d files; agauss/gauss/unif/mc_/mismatch)" % files)
    rep.check("mismatch scan: files scanned", "derived", float(files), ref.MISMATCH_SCAN_FILES, ref.MISMATCH_SCAN_FILES, "", 1)
    print("\nNoise, 5 V NMOS %(W)g/%(L)g um, Vg %(VG)g V, Vd %(VD)g V (ngspice .noise, 27 C); BSIM3v3 defaults, no published level\n" % ref.NOISE_BIAS)
    rep.check("noise scan: MOS models", "derived", float(mos), ref.MOS_MODELS, ref.MOS_MODELS, "", 1)
    rep.check("noise scan: MOS models setting a noise parameter", "derived", float(noisy), 0, 0, "", 1,
              "(defaults apply: noimod=1, kf=0)")
    r = noise_deck(ng, work, models, "noise_long", ref.NOISE_BIAS)
    data["noise long"] = r
    lo, hi = ref.GAMMA_LONG
    rep.check("thermal gamma (4kT*gamma*gm) 30/10", "derived", r["gamma_thermal"], lo, hi, "", 1, "(long-channel theory 2/3 .. 1)")
    lo, hi = ref.NYQUIST
    rep.known("Nyquist S_id/(4kT*gds) at Vds=0", r["nyquist_ratio"], lo, hi, "", 1, ref.NOISE_KNOWN["nyquist"])
    rep.check("flicker level at 1 Hz = 0 (kf default 0)", "derived", r["sv_flicker_1Hz_V2"], 0, 0, "V2/Hz", 1)
    short = noise_deck(ng, work, models, "noise_short", ref.NOISE_BIAS_SHORT)
    data["noise short"] = short
    rep.info("thermal gamma 30/1", short["gamma_thermal"], "", 1, "(information; no long-channel claim)")
    print("\nGaps (not estimated):")
    for g in ref.GAPS:
        print("  - " + g)


def run(prefix, ng):
    models = os.path.join(prefix, "tr1um", "TR-1um", "libs.tech", "spice", "models")
    if not os.path.exists(os.path.join(models, "ip62_models")):
        raise SystemExit("TR-1um models not found under %s (run bootstrap.sh --pdk tr1um)" % models)
    rep, data = Report(), {}
    print("TR-1um typical, %d C, W/L = 30/1 um. Sources and caveats: sanity/tr1um/reference.py\n" % ref.TEMP)
    with tempfile.TemporaryDirectory(prefix="tr1um-sanity-") as work:
        curves = {}
        for dev in ("NMOS", "PMOS"):
            pol = -1 if dev == "PMOS" else 1
            out = os.path.join(work, dev)
            subs = dict(MODELS=models, DEVICE=dev, OUT=out, VDS5=pol * 5, VD7=pol * 7, VSTEP=pol * 0.01)
            subs.update({"VG%d" % v: pol * v for v in (2, 3, 4, 5, 6)})
            ngspice(ng, render(DECK, work, dev, **subs))
            curves[dev] = dict(idvg=read_xy(out + ".idvg", pol),
                               **{"idvd%d" % v: read_xy(out + ".idvd%d" % v, pol) for v in (2, 3, 4, 5, 6)})
        for dev, curve, vgs, vds, sim, meas in ref.POINTS:
            c = curves[dev]
            i = at(*c["idvg"], vgs) if curve == "Id-Vg" else at(*c["idvd%d" % vgs], vds)
            data["%s %s Vgs=%g Vds=%g" % (dev, curve, vgs, vds)] = i
            name = "%s %s |Vgs|=%g |Vds|=%g" % (dev, curve, vgs, vds)
            lo, hi = sim * (1 - ref.TOL), sim * (1 + ref.TOL)
            note = "(sim %.3g mA, %+.1f %%; measured %.3g mA)" % (sim * 1e3, 100 * (i / sim - 1), meas * 1e3)
            if (dev, curve, vgs) in ref.KNOWN_DEVIATIONS:
                rep.known(name, i, lo, hi, "mA", 1e3, ref.KNOWN_DEVIATIONS[(dev, curve, vgs)])
            else:
                rep.check(name, "published", i, lo, hi, "mA", 1e3, note)
        mismatch_and_noise(rep, data, models, ng, work)
    return rep.summary(), data, rep.rows
