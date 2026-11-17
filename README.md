# profiling-catalog

The [scope-profiler](https://github.com/max-models/scope-profiler) results of the max-models
codes, in one place. This repository holds only data: each code's docs site fetches its folder and
turns it into a "Profiling" section with `scope-profiler site`.

## Layout

```
<code>/<case>/<execution>/
    np1.h5, np2.h5, ...   # the runs of this execution (one file per run)
    meta.yml              # optional: label, date and info of the execution
shared/<case>/<execution>/  # runs that profile several codes at once
```

- `<code>` is the repository name (`cunumpy`, `mpiarray`, ...).
- `<case>` is one benchmark, named as in the code's manifest (`poisson-strong`).
- `<execution>` is one set of runs of the case, e.g. one night or one commit. Name it by date,
  `YYYY-MM-DD`, and add a suffix when there are several on one day (`2026-11-17_a1b2c3d`).
- Run files are named so that they sort naturally: `np1.h5`, `np2.h5`, ..., `np16.h5`.

`meta.yml` (all keys optional):

```yaml
label: Nightly 17 Nov    # shown instead of the directory name
date: 2026-11-17         # orders the executions
info:                    # shown as the execution's metadata
  commit: a1b2c3d
  system: raven, 1 node
```

## Add runs

```bash
git clone --depth 1 https://github.com/max-models/profiling-catalog
mkdir -p profiling-catalog/cunumpy/poisson-strong/2026-11-17
cp np*.h5 profiling-catalog/cunumpy/poisson-strong/2026-11-17/
# optionally write meta.yml next to them
cd profiling-catalog && uv run scripts/check.py && git add . && git commit -m "..." && git push
```

The code's manifest finds new executions by itself (`executions: {path: "<case>/{execution}/np*.h5"}`),
so adding runs needs no change in the code's repository; the next docs build shows them.

## How a docs site uses it

The case scripts and the manifest (`profiling/profiling.yaml`) live in the code's repository.
Its docs build fetches only its own folder (and `shared/` when it uses it):

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/max-models/profiling-catalog profiling/data
git -C profiling/data sparse-checkout set cunumpy shared
```

## Rules

- Only public codes: no results of private codes (picnic) here.
- Profiles record metadata such as host and user names; the generated pages show only what
  identifies a run unless a case sets `metadata: all`.
- Keep a file below 50 MB (GitHub refuses files above 100 MB). Thin out old nightly executions
  when a folder grows large.
- `uv run scripts/check.py` checks the layout, the `meta.yml` files and that every `.h5` file
  opens; CI runs it on every push.
