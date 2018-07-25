#!/usr/bin/env python

import json
import sys

from datetime import date, datetime

import requests

import config

def parse_date(inp):
    return datetime.strptime(inp, "%Y-%m-%d").date()


def add_for(d, minutes, txt):
    url = "https://{}.mite.yo.lk/time_entries.json".format(config.TEAM)
    headers = {
        "X-MiteApikey": config.API_KEY,
        "User-Agent": "mite (Python CLI: https://github.com/port-zero/mite) TEST",
        "Content-Type": "application/json",
    }
    data = {
        "time_entry": {
            "date_at": str(d),
            "minutes": int(minutes),
            "note": txt,
        }
    }
    res = requests.post(url, headers=headers, data=json.dumps(data))

    if res.status_code >= 300:
        print(res.content)
    else:
        print("Entry created for {}!".format(d))


def usage():
    print("Usage: mite [add|now]")
    print("  where:")
    print("    add <date:YYYY-MM-DD> <minutes:int> <text>: add entry 'text' for 'date' (for 'minutes' duration)")
    print("    <minutes:int> <text>: add entry 'text' for 'today")
    sys.exit(1)


def mite():
    if not len(sys.argv) > 2: usage()

    if sys.argv[1] == "add": add_for(parse_date(sys.argv[2]), *sys.argv[3:5])
    else: add_for(date.today(), *sys.argv[1:3])


if __name__ == '__main__':
    mite()
