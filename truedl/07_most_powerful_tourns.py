#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import Counter, defaultdict
import argparse
import datetime
import functools
import os
import sqlite3
import sys

import orjson

from truedl.util import parse_date, _open


CREATE_POWER_TABLES = """\
create table power_data(
    tournament_id integer,
    tournament_name text,
    tournament_year integer,
    teams_total integer,
    teams_from_top15 integer,
    teams_from_top100 integer,
    teams_from_top200 integer,
    teams_from_top500 integer,
    winner_b integer
);
"""

POSITIONS_QUERY_STUB = """\
select idteam, rating_position
from chgk_release_data_balanced
where idrelease = {idrelease}
order by rating_position, idteam;    
"""

ADD_POWER_DATA_STUB = """\
insert into power_data (
    tournament_id,
    tournament_name,
    tournament_year,
    teams_total,
    teams_from_top15,
    teams_from_top100,
    teams_from_top200,
    teams_from_top500,
    winner_b
)
values 
    {values};
"""

DELETE_TRUEDL_DATA_STUB = """\
delete from truedl_data
where tournament_id in {tournament_ids};
"""


def create_power_tables(conn):
    cur = conn.cursor()
    cur.execute(CREATE_POWER_TABLES)
    conn.commit()


def make_release_lookup(releases):
    prev_release = None
    result = {}
    for release in releases:
        if prev_release:
            curr_date = parse_date(release["date"])
            prev_date = parse_date(prev_release["date"])
            while prev_date < curr_date:
                result[prev_date] = prev_release
                prev_date += datetime.timedelta(days=1)
        prev_release = release
    return result


def get_category(position):
    if not position or position <= 0:
        return "???"
    if position <= 10:
        return "1-10"
    if position <= 25:
        return "11-25"
    if position <= 50:
        return "26-50"
    if position <= 100:
        return "51-100"
    if position <= 250:
        return "101-250"
    if position <= 500:
        return "251-500"
    if position <= 1000:
        return "501-1000"
    if position <= 2000:
        return "1001-2000"
    if position <= 3000:
        return "2001-3000"
    if position <= 4000:
        return "3001-5000"
    if position <= 5000:
        return "3001-5000"
    return "5001+"


@functools.cache
def _get_rating_positions(rdb_cur, release_id):
    return tuple(
        rdb_cur.execute(POSITIONS_QUERY_STUB.format(idrelease=release_id)).fetchall()
    )


def get_rating_positions(rdb_cur, release_id, team_ids):
    teamid_to_position = dict(_get_rating_positions(rdb_cur, release_id))
    return {x: teamid_to_position[x] for x in team_ids if x in teamid_to_position}


def add_to_db(conn, data_point):
    cur = conn.cursor()
    values = []
    values.append(
        "("
        + ",".join(
            [
                repr(data_point["tournament_id"]),
                repr(data_point["tournament_name"]),
                repr(data_point["tournament_year"]),
                repr(data_point["teams_total"]),
                repr(data_point["teams_from_top15"]),
                repr(data_point["teams_from_top100"]),
                repr(data_point["teams_from_top200"]),
                repr(data_point["teams_from_top500"]),
                repr(data_point["winner_b"]),
            ]
        )
        + ")"
    )
    values = ",   ".join(values)
    try:
        cur.execute(ADD_POWER_DATA_STUB.format(values=values))
    except Exception as e:
        print(e)
        import pdb

        pdb.set_trace()
    conn.commit()


def avg(list_):
    return sum(list_) / len(list_)


def is_in_rating(res):
    return (res.get("rating") or {}).get("inRating")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tournament_info_dir", default="tournaments")
    parser.add_argument("--tournament_results_dir", default="tournament_results")
    parser.add_argument("--rating_db", default="rating.db")
    parser.add_argument("--power_db", default="power.db")
    args = parser.parse_args()

    if not os.path.isfile(args.power_db):
        conn = sqlite3.connect(args.power_db)
        create_power_tables(conn)
    else:
        conn = sqlite3.connect(args.power_db)

    if not os.path.isfile(args.rating_db):
        sys.stderr.write(f"rating db not found at {args.rating_db}\n")
        sys.exit(1)
    rdb_conn = sqlite3.connect(args.rating_db)
    rdb_cur = rdb_conn.cursor()

    with _open("tournaments/releases.json") as f:
        releases = make_release_lookup(orjson.loads(f.read()))

    with _open("tournaments/tournaments.json") as f:
        t_infos = orjson.loads(f.read())

    for t_info in t_infos:
        if not t_info.get("tournamentInRatingBalanced"):
            continue
        date_start = parse_date(t_info["dateStart"])
        if date_start not in releases:
            continue
        release_id = releases[date_start]["id"]
        results_filepath = (
            "tournament_results/" f"tournament-{t_info['id']}-results.json"
        )
        if not os.path.isfile(results_filepath):
            continue
        with _open(results_filepath) as f:
            results = orjson.loads(f.read())
        if not results:
            continue
        if not results[0].get("mask"):
            continue
        mask = results[0]["mask"]
        total_questions = len(mask) - Counter(mask)["X"]
        if not total_questions:
            continue
        winner_b = None
        for res in results:
            if res["rating"] and res["rating"]["b"]:
                winner_b = res["rating"]["b"]
                break
        if winner_b is None:
            winner_b = -1
        print(f"processing tournament {t_info['id']} {t_info['name']}...")
        team_ids = {x["team"]["id"] for x in results if is_in_rating(x)}
        rating_positions = get_rating_positions(rdb_cur, release_id, team_ids)
        data_point = {
            "tournament_id": t_info["id"],
            "tournament_name": t_info["name"],
            "tournament_year": date_start.year,
            "teams_total": len(rating_positions),
            "teams_from_top15": len(
                [x for x in rating_positions if rating_positions[x] <= 15]
            ),
            "teams_from_top100": len(
                [x for x in rating_positions if rating_positions[x] <= 100]
            ),
            "teams_from_top200": len(
                [x for x in rating_positions if rating_positions[x] <= 200]
            ),
            "teams_from_top500": len(
                [x for x in rating_positions if rating_positions[x] <= 500]
            ),
            "winner_b": winner_b
        }
        add_to_db(conn, data_point)


if __name__ == "__main__":
    main()
