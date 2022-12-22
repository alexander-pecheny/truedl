#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
from collections import Counter

import orjson as json

from .util import _open, parse_date

RESULTS_DIR = "tournament_results"
INFO_DIR = "tournaments"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--top-n", type=int, default=100)
    args = parser.parse_args()

    args.date_from = parse_date(args.date_from)
    args.date_to = parse_date(args.date_to)

    counter = Counter()
    for fn in os.listdir(RESULTS_DIR):
        if not fn.endswith(".json"):
            continue
        full_path = os.path.join(RESULTS_DIR, fn)
        tourn_id = int(fn.split("-")[1])
        info_path = os.path.join(INFO_DIR, f"tournament-{tourn_id}.json")
        with _open(full_path, "r") as f:
            res = json.loads(f.read())
        with _open(info_path, "r") as f:
            info = json.loads(f.read())
        if not (
            args.date_from <= parse_date(info["dateStart"]) <= args.date_to
        ):
            continue
        counter[f"{tourn_id} {info['name']}"] = len(res)
    for i, tup in enumerate(counter.most_common(args.top_n)):
        print(f"{i + 1}. {tup[0]} - {tup[1]} команд")


if __name__ == "__main__":
    main()
