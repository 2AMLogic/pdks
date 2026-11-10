"""Shared helpers for the per-PDK sanity checks (sanity/<pdk>/checks.py).

Python 3.8+, stdlib only.
"""

import math
import os
import re
import subprocess
import sys


def render(deck_path, out_dir, name, **subs):
    """Fill @KEY@ placeholders in a deck template and write it to out_dir/name.sp."""
    with open(deck_path) as f:
        text = f.read()
    for k, v in subs.items():
        text = text.replace("@%s@" % k, str(v))
    left = re.findall(r"@[A-Z_]+@", text)
    if left:
        raise SystemExit("unfilled placeholders in %s: %s" % (deck_path, sorted(set(left))))
    path = os.path.join(out_dir, name + ".sp")
    with open(path, "w") as f:
        f.write(text)
    return path


def ngspice(binary, deck, cwd=None, spiceinit=None):
    """Run a deck in batch mode. A user's ~/.spiceinit must never change the
    result: with no spiceinit, -n skips it; with one, it is written to the
    run directory, which ngspice reads instead of the home one."""
    if spiceinit is None:
        args = [binary, "-b", "-n", deck]
    else:
        cwd = cwd or os.path.dirname(os.path.abspath(deck))
        with open(os.path.join(cwd, ".spiceinit"), "w") as f:
            f.write(spiceinit)
        args = [binary, "-b", deck]
    p = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    log = p.stdout + p.stderr
    if p.returncode != 0 or re.search(r"^\s*Error", log, re.M):
        sys.stderr.write(log)
        raise SystemExit("ngspice failed on %s" % deck)
    return log


def results(log):
    """Values printed by decks as 'RESULT name value'."""
    return {m.group(1): float(m.group(2)) for m in re.finditer(r"^RESULT (\w+) (\S+)", log, re.M)}


def read_xy(path, pol=None):
    """Two-column wrdata output as (|x|, |y|) lists. With pol (+1 / -1) x is
    instead signed, pol * x, which gives device-terms voltages for a pFET."""
    xs, ys = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                xs.append(abs(float(parts[0])) if pol is None else pol * float(parts[0]))
                ys.append(abs(float(parts[1])))
    return xs, ys


def tc_fit(ts, ys, t0=27.0):
    """Least-squares TC1, TC2 (in ppm/K, ppm/K^2) of y(T) = y0 [1 + a dT + b dT^2]."""
    y0 = ys[ts.index(t0)]
    X = [(t - t0, (t - t0) ** 2) for t in ts]
    Z = [y / y0 - 1 for y in ys]
    sxx = sum(a * a for a, _ in X); sxy = sum(a * b for a, b in X); syy = sum(b * b for _, b in X)
    sxz = sum(a * z for (a, _), z in zip(X, Z)); syz = sum(b * z for (_, b), z in zip(X, Z))
    det = sxx * syy - sxy * sxy
    return (sxz * syy - syz * sxy) / det * 1e6, (syz * sxx - sxz * sxy) / det * 1e6


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


def vt_max_gm(vg, id_, vds):
    """Linear-extrapolation threshold: tangent at peak transconductance,
    intercept with Id = 0, minus Vds/2."""
    best, k = -1.0, 1
    for i in range(1, len(vg) - 1):
        g = (id_[i + 1] - id_[i - 1]) / (vg[i + 1] - vg[i - 1])
        if g > best:
            best, k = g, i
    return vg[k] - id_[k] / best - vds / 2


def ss_decade(vg, id_, i0):
    """Gate swing (mV) across the decade of drain current from i0 to 10*i0."""
    return 1000 * (vt_cc(vg, id_, 10 * i0) - vt_cc(vg, id_, i0))


class Report:
    def __init__(self):
        self.rows, self.failed = [], 0

    def info(self, name, value, unit, scale, note=""):
        print("%-4s %-38s %-9s %10s %-6s  %s" % ("--", name, "info", "%.4g" % (value * scale), unit, note))

    def check(self, name, kind, value, lo, hi, unit, scale, note=""):
        ok = lo <= value <= hi
        self.failed += not ok
        self.rows.append(dict(check=name, kind=kind, value=value, lo=lo, hi=hi, unit=unit, ok=ok))
        fmt = lambda x: "%.4g" % (x * scale)  # noqa: E731
        print("%-4s %-38s %-9s %10s %-6s  [%s, %s] %s" % (
            "ok" if ok else "FAIL", name, kind, fmt(value), unit, fmt(lo), fmt(hi), note))

    def known(self, name, value, lo, hi, unit, scale, reason):
        """A recorded upstream discrepancy: shown on every run (and in the
        README) but not counted as a failure. `reason` must say why."""
        fmt = lambda x: "%.4g" % (x * scale)  # noqa: E731
        ok = lo <= value <= hi
        self.rows.append(dict(check=name, kind="known-deviation", value=value, lo=lo, hi=hi,
                              unit=unit, ok=ok, reason=reason))
        print("%-4s %-38s %-9s %10s %-6s  [%s, %s] %s" % (
            "ok" if ok else "DEV", name, "known", fmt(value), unit, fmt(lo), fmt(hi), reason))

    def summary(self):
        checked = [r for r in self.rows if r["kind"] != "known-deviation"]
        known = len(self.rows) - len(checked)
        print("\n%d/%d checks passed%s" % (len(checked) - self.failed, len(checked),
              "; %d known deviation(s) reported" % known if known else ""))
        return 1 if self.failed else 0


def ss_min(vg, id_, ceiling, window=0.06):
    """Steepest subthreshold swing (mV/dec) below Id = ceiling, over gate
    windows of about `window` volts."""
    best = float("inf")
    step = vg[1] - vg[0]
    k = max(1, int(round(window / step)))
    for i in range(k, len(vg)):
        if id_[i] >= ceiling:
            break
        if id_[i - k] > 0:
            d = math.log10(id_[i]) - math.log10(id_[i - k])
            if d > 0:
                best = min(best, 1000 * (vg[i] - vg[i - k]) / d)
    return best


MOS_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "mos_iv.sp")


def mos_sweeps(ng, work, name, header, instance, pol, vdd, vlin, vaux, voff,
               temp, vstep=0.005, vgstart=0.0, imeas="i(vd)", pre="", spiceinit=None):
    """Run decks/mos_iv.sp for one device. Voltages are given in device
    terms (positive = on for either polarity); pol = -1 for a pFET.
    Returns {sweep: (V list in device terms, |I| list)}."""
    out = os.path.join(work, name)
    deck = render(MOS_DECK, work, name, HEADER=header, INSTANCE=instance, PRE=pre,
                  TEMP=temp, OUT=out, IMEAS=imeas, VDD=pol * vdd, VLIN=pol * vlin,
                  VAUX=pol * vaux, VOFF=pol * voff, VSTEP=pol * vstep, VGSTART=pol * vgstart)
    ngspice(ng, deck, cwd=work, spiceinit=spiceinit)
    return {s: read_xy("%s.%s" % (out, s), pol)
            for s in ("vg_lin", "vg_aux", "vg_sat", "vg_off", "vd_full")}


WIRE_DECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decks", "wire_elmore.sp")


def require_wire_w(ng, wire_inc, work):
    """wire.inc gives `w` no default: a ladder instance without it must stop
    ngspice. Aborts the run if one simulates instead. Not a Report row, so the
    per-PDK check counts are unchanged."""
    deck = os.path.join(work, "wire_no_w.sp")
    with open(deck, "w") as f:
        f.write(".include %s\nvin in 0 1\nX1 in 0 wire l=100u rsh=1 cpl=1e-10\n.op\n.end\n" % wire_inc)
    p = subprocess.run([ng, "-b", "-n", deck], capture_output=True, text=True, cwd=work)
    log = p.stdout + p.stderr
    if p.returncode == 0 and not re.search(r"^\s*Error|w_not_given", log, re.M):
        raise SystemExit("wire.inc accepted a ladder with no w; it must be a required parameter")


def elmore(ng, wire_inc, work, nseg, e, rsh, L, W, cpl, rs, cl):
    """Simulated and closed-form Elmore delay of the wire.inc ladder with nseg
    segments (sanity/decks/wire_elmore.sp). `e` holds the ngspice-notation
    strings (l, w, cpl, rs, cl, tstop); rsh, L, W, cpl, rs, cl are the same
    quantities as numbers, from the caller's reference constants. Closed form:
    rs (C + cl) + R (C / 2 + cl), R = rsh L / W, C = cpl L."""
    r = results(ngspice(ng, render(WIRE_DECK, work, "wire_elmore_%d" % nseg, WIRE_INC=wire_inc, N=nseg, L=e["l"],
                                   W=e["w"], RSH=rsh, CPL=e["cpl"], RS=e["rs"], CL=e["cl"], TSTOP=e["tstop"])))
    R = rsh * L / W
    C = cpl * L
    return r["elmore"], rs * (C + cl) + R * (C / 2 + cl)
