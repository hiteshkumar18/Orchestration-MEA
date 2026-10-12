# Vendored conversion scripts

Copied from the Braingeneers workflows repository (`workflows-main`, local copy at
`/mnt/Vol20tb1/user_workspaces/hitesh/workflows-main`, not a git checkout) on 2026-10-08:

| File | Source |
|---|---|
| `split_maxtwo_by_well.py` | `workflow-sources/max2-splitter/scripts/` |
| `convert_maxone_to_nwb.py` | `workflow-sources/maxwell-to-nwb-conversion/scripts/` |
| `maxwell_h5_utils.py` | `workflow-sources/maxwell-to-nwb-conversion/scripts/` |

Changes, each marked `Orchestration-MEA:` in the code:

1. **Splitter** accepts any 1–24 wells (upstream requires exactly 6 or 24; this lab
   often records only some wells of a plate).
2. **Converter** `--compression gzip|maxwell`, default `gzip`: standard compression
   any NWB reader and DANDI can open without MaxWell's HDF5 plugin. Upstream always
   keeps MaxWell's filter 401.
3. **Converter** writes electrode positions as `rel_x` / `rel_y` (µm, with column
   descriptions); upstream leaves every electrode location as `unknown`.
4. **`maxwell_h5_utils.py`** finds a split well's real name from the file instead of
   assuming data block N is well N (true only for full plates; on a partial plate
   `data0001` can be `well003`, and upstream then fails with "'wells' doesn't exist").

Everything else is upstream code. When updating from upstream, re-apply these four
changes and re-run the end-to-end check in `docs/NWB.md`.
