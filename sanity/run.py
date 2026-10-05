#!/usr/bin/env python3
"""Run the ASAP7 ngspice sanity decks and check them against sanity/reference.py.

    sanity/run.py --prefix ~/pdks            # after ./bootstrap.sh --pdk asap7
    sanity/run.py --models M.pm --osdi B.osdi --ngspice /path/to/ngspice

Exit status 0 when every check passes, 1 otherwise. Python 3.8+, stdlib only.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reference as ref  # noqa: E402

DECKS = os.path.join(HERE, "decks")


def render(deck, out_dir, name, **subs):
    with open(os.path.join(DECKS, deck)) as f:
        text = f.read()
    for k, v in subs.items():
        text = text.replace("@%s@" % k, str(v))
    left = re.findall(r"@[A-Z_]+@", text)
    if left:
        raise SystemExit("unfilled placeholders in %s: %s" % (deck, sorted(set(left))))
    path = os.path.join(out_dir, name + ".sp")
    with open(path, "w") as f:
        f.write(text)
    return path


def ngspice(binary, deck):
    # -n: ignore any ~/.spiceinit, so a user's compatibility mode or other
    # settings cannot change the result.
    p = subprocess.run([binary, "-b", "-n", deck], capture_output=True, text=True)
    log = p.stdout + p.stderr
    if p.returncode != 0 or re.search(r"^\s*Error", log, re.M):
        sys.stderr.write(log)
        raise SystemExit("ngspice failed on %s" % deck)
    return log


def results(log):
    out = {}
    for m in re.finditer(r"^RESULT (\w+) (\S+)", log, re.M):
        out[m.group(1)] = float(m.group(2))
    return out


def read_xy(path):
    xs, ys = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                xs.append(abs(float(parts[0])))
                ys.append(abs(float(parts[1])))
    return xs, ys


def at(xs, ys, x):
    """Linear interpolation of ys at xs == x (xs ascending)."""
    for i in range(1, len(xs)):
        if xs[i] >= x - 1e-12:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


def vt_cc(vg, id_, icc):
    """Gate voltage at which Id crosses icc, interpolated in log(Id)."""
    for i in range(1, len(vg)):
        if id_[i - 1] < icc <= id_[i]:
            a, b = math.log10(id_[i - 1]), math.log10(id_[i])
            return vg[i - 1] + (math.log10(icc) - a) / (b - a) * (vg[i] - vg[i - 1])
    return float("nan")


def ss_decade(vg, id_, i0):
    """Gate swing (mV) across the decade of drain current from i0 to 10*i0."""
    return 1000 * (vt_cc(vg, id_, 10 * i0) - vt_cc(vg, id_, i0))


def characterise(ng, models, osdi, work, device):
    pol = -1 if device.startswith("pmos") else 1
    out = os.path.join(work, device)
    deck = render("device_iv.sp", work, device, MODELS=models, OSDI=osdi, DEVICE=device,
                  OUT=out, VDD=pol * ref.VDD, VHALF=pol * ref.VDD / 2,
                  VLIN=pol * 0.05, VSTEP=pol * 0.005)
    ngspice(ng, deck)
    lin = read_xy(out + ".vg_lin")
    sat = read_xy(out + ".vg_sat")
    vd_full = read_xy(out + ".vd_full")
    vdd, h = ref.VDD, ref.VDD / 2
    idsat = at(*sat, vdd)
    vtlin, vtsat = vt_cc(*lin, ref.ICC), vt_cc(*sat, ref.ICC)
    return dict(
        idsat=idsat,
        ieff=(at(*vd_full, h) + at(*sat, h)) / 2,
        ioff=at(*sat, 0.0),
        vtlin=vtlin,
        vtsat=vtsat,
        ss=ss_decade(*sat, ref.ICC),
        dibl=1000 * (vtlin - vtsat) / (vdd - 0.05),
        idsat_over_idlin=at(*vd_full, vdd) / at(*vd_full, 0.05),
        # the Id-Vg and Id-Vd sweeps must agree where they meet, (VDD, VDD)
        sweep_mismatch=abs(at(*vd_full, vdd) - idsat) / idsat,
    )


def vtc(ng, models, osdi, work, vt):
    out = os.path.join(work, "vtc_" + vt)
    ngspice(ng, render("inverter_vtc.sp", work, "vtc_" + vt, MODELS=models, OSDI=osdi,
                       VT=vt, VDD=ref.VDD, OUT=out))
    vin, vout = read_xy(out + ".vtc")
    vm = next(vin[i] for i in range(len(vin)) if vout[i] <= vin[i])
    gain = max(abs((vout[i + 1] - vout[i]) / (vin[i + 1] - vin[i])) for i in range(len(vin) - 1))
    return dict(vm=vm, gain=gain, voh=vout[0], vol=vout[-1])


def fo4(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render("fo4.sp", work, "fo4_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    return dict(tphl=r["tphl"], tplh=r["tplh"], fo4=(r["tphl"] + r["tplh"]) / 2)


def ring(ng, models, osdi, work, vt):
    r = results(ngspice(ng, render("ring11.sp", work, "ring11_" + vt, MODELS=models, OSDI=osdi,
                                   VT=vt, VDD=ref.VDD, VMID=ref.VDD / 2)))
    period = r["five_periods"] / 5
    return dict(period=period, freq=1 / period, stage=period / (2 * ref.RO_STAGES))


class Report:
    def __init__(self):
        self.rows, self.failed = [], 0

    def info(self, name, value, unit, scale, note=""):
        print("%-4s %-34s %-9s %10s %-6s  %s" % ("--", name, "info", "%.4g" % (value * scale), unit, note))

    def check(self, name, kind, value, lo, hi, unit, scale, note=""):
        ok = lo <= value <= hi
        self.failed += not ok
        self.rows.append(dict(check=name, kind=kind, value=value, lo=lo, hi=hi, unit=unit, ok=ok))
        fmt = lambda x: "%.4g" % (x * scale)  # noqa: E731
        print("%-4s %-34s %-9s %10s %-6s  [%s, %s] %s" % (
            "ok" if ok else "FAIL", name, kind, fmt(value), unit, fmt(lo), fmt(hi), note))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prefix", help="bootstrap prefix; derives the three paths below")
    ap.add_argument("--models", help="ngspice-adapted ASAP7 TT model card")
    ap.add_argument("--osdi", help="compiled BSIM-CMG 107 .osdi")
    ap.add_argument("--ngspice", help="ngspice binary")
    ap.add_argument("--json", help="also write results here")
    a = ap.parse_args()
    if a.prefix:
        p = os.path.abspath(os.path.expanduser(a.prefix))
        a.models = a.models or os.path.join(p, "asap7", "ngspice", "models", "7nm_TT.pm")
        a.osdi = a.osdi or os.path.join(p, "tools", "bsimcmg107", "bsimcmg107.osdi")
        a.ngspice = a.ngspice or os.path.join(p, "tools", "ngspice", "bin", "ngspice")
    if not (a.models and a.osdi and a.ngspice):
        ap.error("give --prefix, or all of --models, --osdi and --ngspice")
    for f in (a.models, a.osdi, a.ngspice):
        if not os.path.exists(f):
            raise SystemExit("not found: %s" % f)

    rep = Report()
    data = {}
    with tempfile.TemporaryDirectory(prefix="asap7-sanity-") as work:
        print("ASAP7 TT, 25 C, VDD %.2f V. Sources and tolerances: sanity/reference.py\n" % ref.VDD)
        for dev, pub in ref.DEVICES.items():
            m = characterise(a.ngspice, a.models, a.osdi, work, dev)
            data[dev] = m
            t = ref.TOL
            rep.check(dev + " Idsat", "published", m["idsat"], pub["idsat"] * (1 - t["idsat"]), pub["idsat"] * (1 + t["idsat"]), "uA", 1e6)
            rep.check(dev + " Ieff", "published", m["ieff"], pub["ieff"] * (1 - t["ieff"]), pub["ieff"] * (1 + t["ieff"]), "uA", 1e6)
            rep.check(dev + " Ioff", "published", m["ioff"], pub["ioff"] / 10 ** t["ioff_dec"], pub["ioff"] * 10 ** t["ioff_dec"], "nA", 1e9)
            rep.check(dev + " Vtlin", "published", m["vtlin"], pub["vtlin"] - t["vt"], pub["vtlin"] + t["vt"], "V", 1)
            rep.check(dev + " Vtsat", "published", m["vtsat"], pub["vtsat"] - t["vt"], pub["vtsat"] + t["vt"], "V", 1)
            rep.check(dev + " SS", "published", m["ss"], pub["ss"] - t["ss"], pub["ss"] + t["ss"], "mV/dec", 1)
            rep.check(dev + " Id-Vg/Id-Vd agree", "derived", m["sweep_mismatch"], 0, 1e-3, "", 1)
            rep.info(dev + " DIBL", m["dibl"], "mV/V", 1, "(paper prints %.2f; see reference.py)" % pub["dibl"])
            rep.info(dev + " Idsat/Idlin", m["idsat_over_idlin"], "", 1, "(paper's design target ~%.1f)" % ref.IDSAT_OVER_IDLIN)
            print()

        v = vtc(a.ngspice, a.models, a.osdi, work, "rvt")
        data["vtc_rvt"] = v
        rep.check("INVx1 RVT VTC switching point", "derived", v["vm"], ref.VDD / 2 - ref.VTC_VM_TOL, ref.VDD / 2 + ref.VTC_VM_TOL, "V", 1)
        rep.check("INVx1 RVT VTC peak gain", "derived", v["gain"], ref.VTC_MIN_GAIN, float("inf"), "", 1)
        rep.check("INVx1 RVT VTC VOH", "derived", v["voh"], ref.VDD - ref.VTC_RAIL_TOL, ref.VDD, "V", 1)
        rep.check("INVx1 RVT VTC VOL", "derived", v["vol"], 0, ref.VTC_RAIL_TOL, "V", 1)
        print()

        fo4s = {}
        for vt, pub in ref.FO4_POSTLAYOUT.items():
            f = fo4(a.ngspice, a.models, a.osdi, work, vt)
            data["fo4_" + vt] = f
            fo4s[vt] = f["fo4"]
            rep.check("FO4 delay %s (pre-layout)" % vt.upper(), "bound", f["fo4"], pub * ref.FO4_LOWER_FRACTION, pub, "ps", 1e12)
        rep.check("FO4 ordering RVT > LVT > SLVT", "derived", float(fo4s["rvt"] > fo4s["lvt"] > fo4s["slvt"]), 1, 1, "", 1)
        print()

        r = ring(a.ngspice, a.models, a.osdi, work, "rvt")
        data["ring11_rvt"] = r
        lo, hi = ref.RO_FO1_OVER_FO4
        rep.check("11-stage RO RVT stage delay / FO4", "derived", r["stage"] / fo4s["rvt"], lo, hi, "", 1,
                  "(f = %.2f GHz, stage %.2f ps)" % (r["freq"] / 1e9, r["stage"] * 1e12))

    total = len(rep.rows)
    print("\n%d/%d checks passed" % (total - rep.failed, total))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(dict(results=data, checks=rep.rows), f, indent=1)
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
