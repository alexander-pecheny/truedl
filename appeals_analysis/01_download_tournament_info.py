#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import time

import requests

from .util import _open

API = "https://api.rating.chgk.net"
SLEEP = 1


def main():

    if not os.path.isdir("tournaments"):
        os.mkdir("tournaments")

    if os.path.isfile("tournaments/tournaments.json"):
        with _open("tournaments/tournaments.json", "r") as f:
            tournaments = json.loads(f.read())
    else:
        tournaments = []
        page = 1
        req = requests.get(f"{API}/tournaments.json?itemsPerPage=100&page={page}")
        res = req.json()
        time.sleep(SLEEP)
        tournaments.extend(res)
        while len(res) == 100:
            page += 1
            print(f"processing page {page}...")
            req = requests.get(f"{API}/tournaments.json?itemsPerPage=100&page={page}")
            res = req.json()
            time.sleep(SLEEP)
            tournaments.extend(res)
        with _open("tournaments/tournaments.json", "w") as f:
            f.write(json.dumps(tournaments))

    for t in tournaments:
        dest_file_name = f"tournaments/tournament-{t['id']}.json"
        if os.path.isfile(dest_file_name):
            continue
        else:
            print(f"downloading tournament {t['id']} {t['name']}...")
            req = requests.get(f"{API}/tournaments/{t['id']}.json")
            res = req.json()
            with _open(dest_file_name, "w") as f:
                f.write(json.dumps(res))


if __name__ == "__main__":
    main()
