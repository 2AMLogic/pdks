"""GF180MCU sanity checks: Idsat and Vth0 against GF's EP targets, Ioff and
subthreshold slope against the electrical spec limits. Sources, extraction
definitions and tolerances: reference.py. Run via sanity/run.py --pdk gf180mcu.
"""

import os
import tempfile

import reference as ref
from common import Report, at, mos_sweeps, ss_min, vt_max_gm


def run(prefix, ng):
    models = os.path.join(prefix, "gf180mcu", "gf180mcu_fd_pr", "models", "ngspice")
    if not os.path.exists(os.path.join(models, "sm141064.ngspice")):
        raise SystemExit("GF180MCU models not found under %s (run bootstrap.sh --pdk gf180mcu)" % models)
    header = '.include "%s/design.ngspice"\n.lib "%s/sm141064.ngspice" typical' % (models, models)
    rep, data = Report(), {}
    print("GF180MCU typical, %d C, W = 10 um. Sources and tolerances: sanity/gf180mcu/reference.py\n" % ref.TEMP)
    with tempfile.TemporaryDirectory(prefix="gf180-sanity-") as work:
        for dev, p in ref.DEVICES.items():
            pol = -1 if dev.startswith("p") else 1
            inst = "M1 d g s 0 %s w=%gu l=%gu" % (dev, p["w"], p["l"])
            sw = mos_sweeps(ng, work, dev, header, inst, pol, p["vdd"], p["vlin"], p["vlin"],
                            p["voff"], ref.TEMP, vgstart=-0.5 if p["vth0"] < 0 else 0.0)
            w_um = p["w"]
            idsat = at(*sw["vg_sat"], p["vdd"]) / w_um * 1e6            # uA/um
            vg, il = sw["vg_lin"]
            vth0 = vt_max_gm(vg, il, p["vlin"])
            ioff = at(*sw["vg_off"], 0.0) / w_um * 1e12                   # pA/um at Vgs = 0
            ss = ss_min(vg, il, 1e-7 * p["w"] / p["l"])
            data[dev] = dict(idsat_uA_um=idsat, vth0=vth0, ioff_pA_um=ioff, ss=ss)
            t = ref.TOL
            rep.check(dev + " Idsat", "published", idsat, p["idsat"] * (1 - t["idsat"]), p["idsat"] * (1 + t["idsat"]), "uA/um", 1)
            rep.check(dev + " Vth0", "published", vth0, p["vth0"] - t["vth0"], p["vth0"] + t["vth0"], "V", 1)
            if p["ioff_max"] is not None:
                rep.check(dev + " Ioff", "bound", ioff, 0, p["ioff_max"], "pA/um", 1)
                rep.check(dev + " SS", "bound", ss, 0, ref.SS_MAX, "mV/dec", 1)
            print()
    return rep.summary(), data, rep.rows
