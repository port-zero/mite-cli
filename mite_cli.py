#!/usr/bin/env python

import json
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime

import yaml
from mite import Mite

MITE_DIR = os.path.expanduser("~/.mite")

def init_repository(team, api_key):
    os.makedirs(MITE_DIR, exist_ok=True)

    with open("{}/conf.yaml".format(MITE_DIR), "w+") as f:
        f.write(yaml.dump({"team": team, "api_key": api_key}))


def parse_date(inp):
    return datetime.strptime(inp, "%Y-%m-%d").date()


def get_config():
    with open("{}/conf.yaml".format(MITE_DIR)) as f:
        return yaml.load(f.read())


def edit_subprocess(editor):
    f, name = tempfile.mkstemp()
    # Can't use the file descriptor provided by tempfile.mkstemp in subprocess
    # Thus, we close it and create a NEW file descriptor for use in subprocess.
    os.close(f)
    rv = subprocess.check_call([editor, name])
    with open(name, 'r') as f:
        contents = f.read()
    os.remove(name)
    return contents


def edit():
    editor = os.environ.get("EDITOR", "vi")
    return edit_subprocess(editor)


def add_for(d, minutes, txt=None):
    if not txt:
        txt = edit()

    conf = get_config()
    mite = Mite(conf["team"], conf["api_key"])

    res = mite.create_entry(
        date_at=str(d),
        minutes=int(minutes),
        note=txt,
    )

    print("Entry created for {}!".format(d))


def usage():
    print("Usage: mite [add|now]")
    print("  where:")
    print("    init <team> <apie-key>: initialize local Mite repository")
    print("    pull: get state of remote Mite")
    print("    add <date:YYYY-MM-DD> <minutes:int> <text>: add entry 'text' for 'date' (for 'minutes' duration)")
    print("    add <minutes:int> <text>: add entry 'text' for today")
    sys.exit(1)


def mite():
    a = sys.argv
    la = len(a)
    if la == 4 and a[1] == "init": return init_repository(a[2], a[3])
    if la == 2 and a[1] == "pull": return pull_repository()
    if la == 6 and a[1] == "add": return add_for(parse_date(a[2]), *a[3:5])
    if la == 5 and a[1] == "add": return add_for(parse_date(a[2]), *a[3:4])
    if la == 4 and a[1] == "add": return add_for(date.today(), *a[2:4])
    if la == 3 and a[1] == "add": return add_for(date.today(), *a[2:3])

    usage()


if __name__ == '__main__':
    mite()
