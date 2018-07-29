#!/usr/bin/env python

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from datetime import date as d

import click
import yaml
from mite import Mite

if sys.version_info < (3,):
    input = raw_input


MITE_DIR = os.path.expanduser("~/.mite")
INTERACTIVE_MSG = "(will be added interactively if it is not specified)"


def parse_date(inp):
    return datetime.strptime(inp, "%Y-%m-%d").date()


def has_config():
    return os.path.exists("{}/conf.yaml".format(MITE_DIR))


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


def choose_from(name, lst):
    # this is an ugly hack
    print("Choose a {} to add the entry to:".format(name))
    for idx, thng in enumerate(lst):
        print("[{}] {}".format(idx+1, thng[name]["name"]))

    chosen = ""
    while not chosen.isnumeric() or not (0 < int(chosen) < idx+1):
        chosen = input("> ")

    return lst[int(chosen)][name]["id"]


def get_project(mite):
    projects = mite.list_projects()
    return choose_from("project", projects)


def get_service(mite):
    services = mite.list_services()
    return choose_from("service", services)


@click.group()
@click.version_option("0.0.1")
@click.pass_context
def cli(ctx):
    ctx.obj = None
    if has_config():
        conf = get_config()
        ctx.obj = Mite(conf["team"], conf["api_key"])


@cli.command()
@click.pass_obj
def projects(mite):
    for proj in mite.list_projects():
        proj = proj["project"]
        print("{}: {}".format(proj["id"], proj["name"]))


@cli.command()
@click.pass_obj
def services(mite):
    for serv in mite.list_services():
        serv = serv["service"]
        print("{}: {}".format(serv["id"], serv["name"]))


@cli.command()
@click.option("--team", required=True,
              help="The team name on mite (corresponds to your subdomain).")
@click.option("--api-key", required=True,
              help="Your API key (you can generate it in your settings).")
def init(team, api_key):
    os.makedirs(MITE_DIR, exist_ok=True)

    with open("{}/conf.yaml".format(MITE_DIR), "w+") as f:
        f.write(yaml.dump({"team": team, "api_key": api_key}))


@cli.command()
@click.option("--date", default=None, help="The date in YYYY-MM-DD format.")
@click.option("--minutes", default=480, help="The number of minutes.")
@click.option("--project-id", default=None,
              help="Project ID {}.".format(INTERACTIVE_MSG))
@click.option("--service-id", default=None,
              help="Service ID {}.".format(INTERACTIVE_MSG))
@click.option("--note", default=None,
              help="Body message {}.".format(INTERACTIVE_MSG))
@click.pass_obj
def add(mite, date, minutes, project_id, service_id, note):
    given_pid = True
    given_sid = True

    if not note:
        note = edit()

    if not project_id:
        given_pid = False
        project_id = get_project(mite)

    if not service_id:
        given_sid = False
        service_id = get_service(mite)

    if date:
        date = parse_date(date)
    else:
        date = d.today()

    res = mite.create_entry(
        date_at=str(date),
        minutes=minutes,
        note=note,
        project_id=project_id,
        service_id=service_id,
    )

    print("Entry created for {}!".format(date))

    if not given_pid:
        print("  Project ID: {}".format(project_id))
    if not given_sid:
        print("  Service ID: {}".format(service_id))


if __name__ == "__main__":
    cli()
