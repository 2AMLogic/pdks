#!/usr/bin/env python3
"""Run a PDK's sanity checks against its cited reference values.

    sanity/run.py --pdk asap7 --prefix ~/pdks [--json results.json]

Each PDK's decks, reference values (with sources) and checks live in
sanity/<pdk>/. Exit status 0 when every check passes, 1 otherwise.
"""

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load(pdk):
    path = os.path.join(HERE, pdk, "checks.py")
    if not os.path.exists(path):
        raise SystemExit("no sanity checks for %s (expected %s)" % (pdk, path))
    spec = importlib.util.spec_from_file_location("checks_" + pdk.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdk", required=True)
    ap.add_argument("--prefix", required=True, help="bootstrap.sh --prefix")
    ap.add_argument("--json", help="also write results here")
    a = ap.parse_args()
    prefix = os.path.abspath(os.path.expanduser(a.prefix))
    ngspice = os.path.join(prefix, "tools", "ngspice", "bin", "ngspice")
    if not os.path.exists(ngspice):
        raise SystemExit("not found: %s (run bootstrap.sh first)" % ngspice)
    status, data, rows = load(a.pdk).run(prefix, ngspice)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(dict(pdk=a.pdk, results=data, checks=rows), f, indent=1)
    return status


if __name__ == "__main__":
    sys.exit(main())
