#!/usr/bin/env python3
"""Split a Maxwell Max Two multi-well recording into per-well .raw.h5 files."""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import h5py


METADATA_KEYS = (
    "assay",
    "bits",
    "environment",
    "hdf_version",
    "mxw_version",
    "notes",
    "version",
    "wellplate",
)


def fail(message: str) -> None:
    print(f"[split_maxtwo_by_well] {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize_rec_name(rec_basename: str) -> str:
    rec_name = rec_basename
    while rec_name.endswith(".raw.h5"):
        rec_name = rec_name[: -len(".raw.h5")]
    if rec_name.endswith(".h5"):
        rec_name = rec_name[:-3]
    elif "." in rec_name:
        rec_name = rec_name.rsplit(".", 1)[0]
    return rec_name


def parse_well_number(well: str) -> int | None:
    match = re.search(r"well(\d+)$", well or "")
    if not match:
        return None
    return int(match.group(1))


def infer_well_offset(wells: list[str]) -> int:
    nums = [n for n in (parse_well_number(well) for well in wells) if n is not None]
    if any(num == 0 for num in nums):
        return 1
    return 0


def output_well_name(source_well: str, *, offset: int) -> str:
    num = parse_well_number(source_well)
    if num is None:
        return source_well
    return f"well{num + offset:03d}"


def discover_wells(src: h5py.File) -> list[str]:
    if "wells" in src:
        wells = [key for key in src["wells"].keys() if key.startswith("well")]
        if wells:
            return sorted(wells)

    if "wellplate" in src:
        wells = [key for key in src["wellplate"].keys() if key.startswith("well")]
        if wells:
            return sorted(wells)

    wells: set[str] = set()
    if "recordings" in src:
        for rec_key in src["recordings"].keys():
            rec = src["recordings"][rec_key]
            wells.update(key for key in rec.keys() if key.startswith("well"))
    if wells:
        return sorted(wells)

    if "data_store" in src:
        for key in src["data_store"].keys():
            if key.startswith("data"):
                suffix = key.replace("data", "")
                if suffix.isdigit():
                    wells.add(f"well{int(suffix):03d}")

    return sorted(wells)


def build_data_store_link_map(src: h5py.File) -> dict[int, list[str]]:
    data_store_map: dict[int, list[str]] = {}
    if "data_store" not in src:
        return data_store_map

    for key in src["data_store"].keys():
        group = src["data_store"][key]
        data_store_map.setdefault(group.id.__hash__(), []).append(f"data_store/{key}")
    return data_store_map


def rewrite_well_path(path: str, source_well: str, destination_well: str) -> str:
    if source_well == destination_well:
        return path
    return "/".join(destination_well if part == source_well else part for part in path.split("/"))


def collect_well_branches(src: h5py.File, source_well: str) -> tuple[list[str], str | None]:
    branches: list[str] = []
    branch_set: set[str] = set()
    data_store_added = False
    raw_dataset_path: str | None = None

    def add_branch(path: str) -> None:
        if path not in branch_set:
            branches.append(path)
            branch_set.add(path)

    data_store_map = build_data_store_link_map(src)

    if "recordings" in src:
        for rec_key in src["recordings"].keys():
            rec = src["recordings"][rec_key]
            if source_well in rec:
                add_branch(f"recordings/{rec_key}/{source_well}")

                rec_well_id = rec[source_well].id.__hash__()
                for data_path in data_store_map.get(rec_well_id, []):
                    add_branch(data_path)
                    candidate_raw = f"{data_path}/groups/routed/raw"
                    if candidate_raw in src:
                        raw_dataset_path = f"/{candidate_raw}"
                    data_store_added = True

                for child_key in rec.keys():
                    if child_key.startswith("well"):
                        continue
                    meta_path = f"recordings/{rec_key}/{child_key}"
                    if meta_path in src:
                        add_branch(meta_path)

    if "data_store" in src and not data_store_added:
        well_num = parse_well_number(source_well)
        if well_num is not None:
            matches = []
            for key in src["data_store"].keys():
                if not key.startswith("data"):
                    continue
                suffix = key.replace("data", "")
                if suffix.isdigit() and int(suffix) == well_num:
                    matches.append(key)
            for data_key in sorted(matches, key=len):
                data_path = f"data_store/{data_key}"
                add_branch(data_path)
                candidate_raw = f"{data_path}/groups/routed/raw"
                if candidate_raw in src:
                    raw_dataset_path = f"/{candidate_raw}"

    if "wells" in src and source_well in src["wells"]:
        add_branch(f"wells/{source_well}")

    for key in METADATA_KEYS:
        if key in src:
            add_branch(key)

    return branches, raw_dataset_path


def discover_source_manifest(input_file: Path) -> dict[str, Any]:
    with h5py.File(input_file, "r") as src:
        wells = discover_wells(src)
        if not wells:
            fail("No Max Two wells were found in the source file.")
        # Orchestration-MEA: plates are often recorded with only some wells,
        # so accept any 1-24 wells instead of exactly 6 or 24.
        if not 1 <= len(wells) <= 24:
            fail(f"Expected 1 to 24 Max Two wells, found {len(wells)}: {wells}")

        offset = infer_well_offset(wells)
        well_entries = []
        for source_well in wells:
            destination_well = output_well_name(source_well, offset=offset)
            branches, raw_dataset_path = collect_well_branches(src, source_well)
            if not branches:
                fail(f"No HDF5 branches found for {source_well}.")
            if not raw_dataset_path:
                fail(f"No routed raw dataset found for {source_well}.")
            raw_dataset = src[raw_dataset_path]
            well_entries.append(
                {
                    "source_well": source_well,
                    "output_well": destination_well,
                    "branches": branches,
                    "raw_dataset_path": raw_dataset_path,
                    "raw_shape": [int(value) for value in raw_dataset.shape],
                    "raw_dtype": str(raw_dataset.dtype),
                }
            )

    return {
        "source_file": str(input_file),
        "source_basename": input_file.name,
        "recording_stem": normalize_rec_name(input_file.name),
        "source_well_count": len(well_entries),
        "well_offset": offset,
        "wells": well_entries,
    }


def create_hard_link(dst_parent: h5py.Group, name: str, target: str) -> None:
    dst_parent[name] = dst_parent.file[target]


def copy_tree(src: h5py.File, dst: h5py.File, src_path: str, dst_path: str, id_map: dict[int, str]) -> None:
    obj = src[src_path]
    obj_id = obj.id.__hash__()

    if isinstance(obj, h5py.Dataset):
        dst_group = dst.require_group(Path(dst_path).parent.as_posix())
        if obj_id in id_map:
            create_hard_link(dst_group, Path(dst_path).name, id_map[obj_id])
        else:
            src.copy(src_path, dst_group, name=Path(dst_path).name, shallow=False, expand_refs=True)
            id_map[obj_id] = dst_path
        return

    dst.require_group(dst_path)
    for child in obj:
        copy_tree(src, dst, f"{src_path}/{child}", f"{dst_path}/{child}", id_map)
    for key, value in obj.attrs.items():
        dst[dst_path].attrs[key] = value


def process_single_well(args: tuple[str, str, str, dict[str, Any], int, int]) -> dict[str, Any]:
    input_file, recording_stem, output_dir, well_entry, index, total = args
    output_dir_path = Path(output_dir)
    source_well = well_entry["source_well"]
    output_well = well_entry["output_well"]
    output_path = output_dir_path / f"{recording_stem}_{output_well}.raw.h5"

    start = time.perf_counter()
    logging.info("[%s/%s] Splitting %s as %s", index + 1, total, source_well, output_well)

    with h5py.File(input_file, "r") as src, h5py.File(output_path, "w") as dst:
        id_map: dict[int, str] = {}
        for branch in well_entry["branches"]:
            if branch not in src:
                logging.warning("Branch %s was listed but is missing in source", branch)
                continue
            destination_branch = rewrite_well_path(branch, source_well, output_well)
            copy_tree(src, dst, branch, destination_branch, id_map)

    size_bytes = output_path.stat().st_size
    elapsed = time.perf_counter() - start
    logging.info(
        "[%s/%s] Wrote %s (%.3f GiB) in %.1fs",
        index + 1,
        total,
        output_path.name,
        size_bytes / (1024**3),
        elapsed,
    )

    result = dict(well_entry)
    result.update(
        {
            "output_file": output_path.name,
            "local_path": str(output_path),
            "size_bytes": size_bytes,
        }
    )
    return result


def setup_logging(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "splitter.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file, mode="w"), logging.StreamHandler()],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-file", required=True, help="Path to staged Max Two .raw.h5 input.")
    parser.add_argument("--source-manifest", default="", help="Validated source manifest from validate_maxtwo_input.py.")
    parser.add_argument("--output-dir", required=True, help="Directory for per-well split files.")
    parser.add_argument("--output-manifest", required=True, help="Path to write split manifest JSON.")
    parser.add_argument("--well-source", default="", help="Optional source well name for single-well task mode.")
    parser.add_argument("--well-manifest", default="", help="Optional path to write single-well manifest JSON.")
    parser.add_argument("--workers", type=int, default=1, help="Parallel worker count.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)
    output_manifest = Path(args.output_manifest)

    if not input_file.exists():
        fail(f"Input file does not exist: {input_file}")
    if args.workers <= 0:
        fail("--workers must be > 0")

    setup_logging(output_dir)

    if args.source_manifest:
        with open(args.source_manifest, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    else:
        manifest = discover_source_manifest(input_file)

    wells = manifest["wells"]
    recording_stem = manifest["recording_stem"]

    if args.well_source:
        matching_wells = [well for well in wells if well["source_well"] == args.well_source]
        if not matching_wells:
            fail(f"Source manifest does not contain requested well: {args.well_source}")

        split_well = process_single_well(
            (str(input_file), recording_stem, str(output_dir), matching_wells[0], 0, 1)
        )
        manifest["split_wells"] = [split_well]
        manifest["split_file_count"] = 1
        manifest["total_size_bytes"] = int(split_well["size_bytes"])
        manifest["split_log"] = str(output_dir / "splitter.log")

        with open(output_manifest, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
            handle.write("\n")

        if args.well_manifest:
            with open(args.well_manifest, "w", encoding="utf-8") as handle:
                json.dump({"source_manifest": manifest, "well": split_well}, handle, indent=2)
                handle.write("\n")

        logging.info("Wrote single-well split manifest: %s", output_manifest)
        return

    worker_count = min(args.workers, len(wells), mp.cpu_count())

    logging.info("Splitting %s wells with %s worker(s)", len(wells), worker_count)
    process_args = [
        (str(input_file), recording_stem, str(output_dir), well_entry, index, len(wells))
        for index, well_entry in enumerate(wells)
    ]

    if worker_count == 1:
        split_wells = [process_single_well(item) for item in process_args]
    else:
        split_wells = []
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(process_single_well, item) for item in process_args]
            for future in as_completed(futures):
                split_wells.append(future.result())

    split_wells.sort(key=lambda item: item["output_well"])
    manifest["split_wells"] = split_wells
    manifest["split_file_count"] = len(split_wells)
    manifest["total_size_bytes"] = sum(int(item["size_bytes"]) for item in split_wells)
    manifest["split_log"] = str(output_dir / "splitter.log")

    with open(output_manifest, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    logging.info("Wrote split manifest: %s", output_manifest)


if __name__ == "__main__":
    main()
