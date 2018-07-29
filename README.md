# mite-cli

A CLI interface for time-tracking in Mite. Currently only adding entries and
listing projects and services is supported.

## Installation

You can install `mite` through pip:

```
pip install mite-cli
```

## Usage

There are four subcommands, `init`, `add`, `projects`, and `services`.

`init` adds your profile configuration, so you don’t have to enter it every
time. Call it once after installing `mite` like so:

```
mite init --team <your mite team name, e.g. portzero> --api-key <your api key>
```

Learn how to obtain a personalized API key [here](https://mite.yo.lk/en/api/index.html#authentication).

After setting `mite` up, you can then use the `add` command. Right now, this
verb seems a little redundant, but there are more subcommands to come, promise!

If you just call `mite add`, it will do the following:

- Assume that you want to add an entry for today (change by providing the
  `--date` argument)
- Assume that you want to add an entry for 480 minutes, i.e. 8 hours (change
  by providing the `--minutes` argument)
- Open your favorite editor as determined by the `EDITOR` system variable so you
  can type in a note (you can also skip this if you provide a `--note` argument)
- Fetch all of your active projects and lets you choose from them (skip this by
  providing a `--project-id` argument)
- Fetch all of your active service and lets you choose from them (skip this by
  providing a `--service-id` argument)
- Tell mite to add that entry and, if you chose a project or service
  interactively, show you those IDs so you can add them via arguments next time.

If you forget those IDs again, simply type `mite projects` or `mite services` to
fetch and display a list of projects and services and their IDs.

And that’s it!

<hr/>

Have fun!
