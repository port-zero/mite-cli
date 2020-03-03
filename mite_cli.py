#!/usr/bin/env python

import os
import subprocess
import sys
import tempfile

from iterfzf import iterfzf
import click
import yaml
import dateparser
from mite import Mite

if sys.version_info < (3,):
    input = raw_input  # noqa: F821


MITE_DIR = os.path.expanduser("~/.mite")
INTERACTIVE_MSG = "(will be added interactively if it is not specified)"


def parse_date(inp):
    """parse date using dateparsing and return a string in format mite API
    expects (YYYY-MM-DD)

    parse order is not locale specific. Explicit YMD order in case
    of ambigous input
    """
    pd = dateparser.parse(inp, settings={"DATE_ORDER": "YMD"})
    if not pd:
        raise Exception("invalid date: {}".format(inp))
    return pd.date().strftime("%Y-%m-%d")


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
    subprocess.check_call([editor, name])
    with open(name, "r") as f:
        contents = f.read()
    os.remove(name)
    return contents


def editor(txt=""):
    editor = os.environ.get("EDITOR", "vi")
    return edit_subprocess(editor, txt)


# choices are of form {(selector) -> id}. Only selector gets displayed
# to the user.
# function returns the corresponding ID.
def choose_with_fzf(choices):
    chs = iterfzf(choices.keys())
    return choices[chs]


def get_project(mite):
    projects = mite.list_projects()
    customers = mite.list_customers()

    # build {cust id -> name}
    cust = {c["customer"]["id"]: c["customer"]["name"] for c in customers}

    choices = {}
    for p in map(lambda x: x["project"], projects):
        cust_name = cust.get(p["customer_id"])
        full_name = "{} ({})".format(p["name"], cust_name)
        choices[full_name] = p["id"]

    print("Choose a project to add the entry to:")
    return choose_with_fzf(choices)


def get_service(mite):
    services = mite.list_services()
    sv_choices = {s["service"]["name"]: s["service"]["id"] for s in services}

    print("Choose a service to add the entry to:")
    return choose_with_fzf(sv_choices)


def get_entry(mite):
    print("Choose an entry:")

    entries = list(reversed(mite.list_entries(sort="date")))
    for idx, thng in enumerate(entries):
        thng = thng["time_entry"]
        print("[{}] {}".format(idx + 1, thng["date_at"]))
        print("\n".join("    {}".format(l) for l in thng["note"].split("\n")))

    chosen = ""
    while not chosen.isnumeric() or not (0 < int(chosen) <= idx + 1):
        chosen = input("> ")

    return entries[int(chosen) - 1]["time_entry"]["id"]


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
    """lists all projects."""
    for proj in mite.list_projects():
        proj = proj["project"]
        print("{}: {}".format(proj["id"], proj["name"]))


@cli.command()
@click.pass_obj
def services(mite):
    """lists all services."""
    for serv in mite.list_services():
        serv = serv["service"]
        print("{}: {}".format(serv["id"], serv["name"]))


@cli.command()
@click.pass_obj
def entries(mite):
    """lists all entries."""
    for entry in reversed(mite.list_entries(sort="date")):
        entry = entry["time_entry"]
        print("{}: {}".format(entry["id"], entry["date_at"]))
        print("\n".join("   {}".format(l) for l in entry["note"].split("\n")))


@cli.command()
@click.option(
    "--team",
    required=True,
    help="The team name on mite (corresponds to your subdomain).",
)
@click.option(
    "--api-key",
    required=True,
    help="Your API key (you can generate it in your settings).",
)
def init(team, api_key):
    """initializes mite for a given team and API key."""
    os.makedirs(MITE_DIR, exist_ok=True)

    with open("{}/conf.yaml".format(MITE_DIR), "w+") as f:
        f.write(yaml.dump({"team": team, "api_key": api_key}))


@cli.command()
@click.option("--date", default="today", help="The date in YYYY-MM-DD format.")
@click.option("--minutes", default=480, help="The number of minutes.")
@click.option(
    "--project-id", default=None, help="Project ID {}.".format(INTERACTIVE_MSG)
)
@click.option(
    "--service-id", default=None, help="Service ID {}.".format(INTERACTIVE_MSG)
)
@click.option("--note", default=None, help="Body message {}.".format(INTERACTIVE_MSG))
@click.pass_obj
def add(mite, date, minutes, project_id, service_id, note):
    """adds entry for a day (defaulting to today)."""
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

    date = parse_date(date)

    mite.create_entry(
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
@click.option(
    "--project-id", default=None, help="Project ID {}.".format(INTERACTIVE_MSG)
)
@click.option(
    "--service-id", default=None, help="Service ID {}.".format(INTERACTIVE_MSG)
)
@click.option("--note", default=None, help="Body message {}.".format(INTERACTIVE_MSG))
@click.pass_obj
def edit(mite, id, date, minutes, project_id, service_id, note):
    """edits an entry."""
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

    mite.edit_entry(
        id,
        date_at=str(date),
        minutes=minutes,
        note=note,
        project_id=project_id,
        service_id=service_id,
    )

    print("Entry edited for {}!".format(date))


# from-date and to-date are strings, so I think its okay to support
# special keys such as yesterday and today.
@cli.command()
@click.option(
    "--from-date", default="yesterday", help="From date" " (default is yesterday)"
)
@click.option("--to-date", default="today", help="To date" " (default is today)")
@click.pass_obj
def replicate(mite, from_date, to_date):
    """replicates entries from a day to another.

    Date parameters accept date either in YYYY-MM-DD format or one of
    the special keywords (yesterday, today, tomorrow)
    """
    f_dt = parse_date(from_date)
    t_dt = parse_date(to_date)

    print("Replicating entries from {} to {}".format(f_dt, t_dt))

    # from=f_dt obviously won't fly, but is there a better way to pass
    # this?
    entries = mite.list_entries(**{"from": f_dt, "to": f_dt})
    for ent in entries:
        time_entry = ent["time_entry"]

        mite.create_entry(
            date_at=t_dt,
            minutes=time_entry["minutes"],
            note=time_entry["note"],
            project_id=time_entry["project_id"],
            service_id=time_entry["service_id"],
        )
        print(
            "created entry: {} — ({}:{})\n{}\n".format(
                time_entry["minutes"],
                time_entry["customer_name"],
                time_entry["project_name"],
                time_entry["note"],
            )
        )


if __name__ == "__main__":
    cli()
