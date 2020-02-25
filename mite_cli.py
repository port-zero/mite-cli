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
from mite import Mite, errors

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
        return yaml.safe_load(f.read())


def edit_subprocess(editor, txt):
    f, name = tempfile.mkstemp()
    os.write(f, bytes(txt, "ascii"))
    # Can't use the file descriptor provided by tempfile.mkstemp in subprocess
    # Thus, we close it and create a NEW file descriptor for use in subprocess.
    os.close(f)
    rv = subprocess.check_call([editor, name])
    with open(name, 'r') as f:
        contents = f.read()
    os.remove(name)
    return contents


def editor(txt=""):
    editor = os.environ.get("EDITOR", "vi")
    return edit_subprocess(editor, txt)


def choose_from_list(lst, key):
    chosen = ""
    max_idx = len(lst)+1
    while not chosen.isnumeric() or not (0 < int(chosen) <= max_idx):
        chosen = input("> ")

    return lst[int(chosen)-1][key]["id"]


def get_project(mite):
    projects = mite.list_projects()
    customers = mite.list_customers()
    print(customers)
    # this is an ugly hack
    print("Choose a project to add the entry to:")
    for idx, thng in enumerate(projects):
        project = thng["project"]
        customer_name = ""
        cs = [c for c in customers
              if c["customer"]["id"] == project["customer_id"]]
        if cs:
            customer_name = cs[0]["customer"]["name"]
        print("[{}] {} ({})".format(idx+1, project["name"], customer_name))

    return choose_from_list(projects, "project")


def get_service(mite):
    services = mite.list_services()
    print("Choose a service to add the entry to:")
    for idx, thng in enumerate(services):
        print("[{}] {}".format(idx+1, thng["service"]["name"]))
    return choose_from_list(services, "service")


def get_entry(mite):
    print("Choose an entry:")
    entries = list(reversed(mite.list_entries(sort="date")))
    for idx, thng in enumerate(entries):
        thng = thng["time_entry"]
        print("[{}] {}".format(idx+1, thng["date_at"]))
        print("\n".join("    {}".format(l) for l in thng["note"].split("\n")))

    chosen = ""
    while not chosen.isnumeric() or not (0 < int(chosen) <= idx+1):
        chosen = input("> ")

    return entries[int(chosen)-1]["time_entry"]["id"]


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
@click.pass_obj
def entries(mite):
    for entry in reversed(mite.list_entries(sort="date")):
        entry = entry["time_entry"]
        print("{}: {}".format(entry["id"], entry["date_at"]))
        print("\n".join("   {}".format(l) for l in entry["note"].split("\n")))


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
        note = editor()

    if not project_id:
        given_pid = False
        project_id = get_project(mite)

    if not service_id:
        given_sid = False
        service_id = get_service(mite)
        print(project_id)

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


@cli.command()
@click.option("--id", default=0, help="The entry ID.")
@click.option("--date", default=None, help="The date in YYYY-MM-DD format.")
@click.option("--minutes", default=480, help="The number of minutes.")
@click.option("--project-id", default=None,
              help="Project ID {}.".format(INTERACTIVE_MSG))
@click.option("--service-id", default=None,
              help="Service ID {}.".format(INTERACTIVE_MSG))
@click.option("--note", default=None,
              help="Body message {}.".format(INTERACTIVE_MSG))
@click.pass_obj
def edit(mite, id, date, minutes, project_id, service_id, note):
    if not id:
        id = get_entry(mite)

    entry = mite.get_entry(id)["time_entry"]

    if not note:
        note = editor(entry["note"])

    if not project_id:
        project_id = entry["project_id"]

    if not service_id:
        service_id = entry["service_id"]

    date = parse_date(date or entry["date_at"])

    res = mite.edit_entry(
        id,
        date_at=str(date),
        minutes=minutes,
        note=note,
        project_id=project_id,
        service_id=service_id,
    )

    print("Entry edited for {}!".format(date))


if __name__ == "__main__":
    cli()
