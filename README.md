# profiling-catalog

The [scope-profiler](https://github.com/max-models/scope-profiler) results of the max-models
codes, in one place. This repository holds only data: each code's docs site fetches its folder and
turns it into a "Profiling" section with `scope-profiler site --section profiling`.

## Layout

```
<code>/<case>/<execution>/
```

- `<code>` is the repository name (`cunumpy`, `mpiarray`, ...).
- `<case>` is one benchmark, the `label` of its profiling job (`stack_strong`).
- `<execution>` is one set of runs of the case: one night, one commit, one cluster.

An execution is normally a folder that `scope-profiler jobs --upload` wrote:

```
cunumpy/stack_strong/20261117T220000Z-a1b2c3d4-stack_strong/
    case_metadata.json      # date, commit, branch, cluster, command, ...
    inputs/                 # the files the job ran
    run01/profiling_data.h5, run_metadata.json
    run02/...
```

The catalogue takes the date, commit, branch and cluster from `case_metadata.json` and names
each run by its ranks (`np4`). Runs put together by hand go into the same place, as `np1.h5`,
`np2.h5`, ... with an optional `meta.yml`:

```yaml
label: Nightly 17 Nov    # shown instead of the directory name
date: 2026-11-17         # orders the executions
info:                    # shown as the execution's metadata
  commit: a1b2c3d
  system: raven, 1 node
```

## Add runs

The case files live in the code's repository (`profiling/*.toml`), with

```toml
[store]
url = "git@github.com:max-models/profiling-catalog.git"
path = "cunumpy/{label}"
public = true      # leave host names and private paths out of the metadata
after_push = ["gh workflow run docs.yml -R max-models/cunumpy --ref devel"]
```

so that on a cluster

```bash
scope-profiler jobs run profiling/stack_strong.toml --upload
```

runs the case and pushes each finished run here. `public = true` makes the jobs replace host
names and the work, checkout, venv and home paths in the packaged metadata with `<host>`,
`<work_dir>`, `<repo>`, `<venv>` and `~`. `after_push` rebuilds the code's docs after every push,
so its Profiling section shows the new runs at once (it needs a logged-in `gh` on the machine
that pushes; without one the push still succeeds and the docs catch up on their next build). A case packaged without `--upload` is pushed
later with `scope-profiler jobs upload <folder> --repo <url> --path cunumpy/{label}`.

The code's manifest finds new executions by itself
(`executions: {path: "data/cunumpy/stack_strong/{execution}/run*/profiling_data.h5"}`), so new
runs need no change in the code's repository; its next docs build shows them.

## How a docs site uses it

The docs build fetches only its own code's folder:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/max-models/profiling-catalog profiling/data
git -C profiling/data sparse-checkout set cunumpy
```

## Rules

- Only public codes: no results of private codes (picnic) here.
- Everything here is public. Upload with `public = true` in the `[store]` table (see above), so
  that host names and private paths stay out of the metadata. The environment variables a job
  sets are recorded as they are: do not put secrets into the environment of a profiling job.
- Keep a file below 50 MB (GitHub refuses files above 100 MB). Thin out old executions when a
  folder grows large: `scope-profiler jobs prune . --keep 30` lists what would go, `--yes`
  removes it, then commit.
- `scope-profiler jobs check .` checks every packaged case folder (metadata, the runs and
  profiles it lists, that every `.h5` file opens, file sizes); CI runs it on every push.
