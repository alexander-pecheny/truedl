#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import argparse

import requests

from .util import _open, parse_date


TOURNAMENTS_DIR = "tournaments"
RESULTS_DIR = "tournament_results"
API = "https://api.rating.chgk.net"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date-from", default="2022-01-01")
    parser.add_argument("--date-to", default="2022-10-29")
    args = parser.parse_args()

    if not os.path.isdir(TOURNAMENTS_DIR):
        os.mkdir(TOURNAMENTS_DIR)
    if not os.path.isdir(RESULTS_DIR):
        os.mkdir(RESULTS_DIR)
    for fn in os.listdir(TOURNAMENTS_DIR):
        if not fn.startswith("tournament") and fn.endswith(".json"):
            continue
        full_path = os.path.join(TOURNAMENTS_DIR, fn)
        with _open(full_path, "r") as f:
            info = json.loads(f.read())
        if not isinstance(info, dict):
            continue
        if info["type"]["name"] != "Синхрон":
            continue
        if (
            not parse_date(args.date_from)
            <= parse_date(info["dateStart"])
            <= parse_date(args.date_to)
        ):
            continue
        results_file_name = os.path.join(
            RESULTS_DIR, f"tournament-{info['id']}-results.json"
        )
        if os.path.isfile(results_file_name):
            continue
        print(f"downloading results from tournament {info['id']} {info['name']}...")
        req = requests.get(
            f"{API}/tournaments/{info['id']}/results.json?includeMasksAndControversials=1"
        ).json()
        with _open(results_file_name, "w") as f:
            f.write(json.dumps(req))


if __name__ == "__main__":
    main()
