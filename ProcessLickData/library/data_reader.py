from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd


@dataclass(frozen=True)
class DataFolderStatus:
    name: str
    path: Path
    has_licks: bool
    has_system_log: bool


def list_data_folders(data_root: str | Path = "data") -> List[DataFolderStatus]:
    data_root = Path(data_root)
    if not data_root.exists():
        return []

    statuses: List[DataFolderStatus] = []
    for folder in sorted(p for p in data_root.iterdir() if p.is_dir()):
        has_licks = (folder / "licks.dat").is_file()
        has_system_log = (folder / "system.log").is_file()
        statuses.append(
            DataFolderStatus(
                name=folder.name,
                path=folder,
                has_licks=has_licks,
                has_system_log=has_system_log,
            )
        )
    return statuses


def print_data_folders_table(data_root: str | Path = "data") -> None:
    rows = list_data_folders(data_root)
    print(f"{'Index':>5}  {'Folder':<30}  Licks  System Log")
    print("-" * 55)
    for idx, row in enumerate(rows):
        licks = "yes" if row.has_licks else "no"
        system = "yes" if row.has_system_log else "no"
        print(f"{idx:>5}  {row.name:<30}  {licks:<5}  {system}")


@dataclass(frozen=True)
class DataFolderContents:
    name: str
    path: Path
    licks: Optional[pd.DataFrame]
    system_log: Optional[pd.DataFrame]


def read_licks_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    data = pd.read_csv(path)
    if "time" in data.columns:
        data["time"] = pd.to_datetime(
            data["time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
    return data


def read_system_log(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 3)
            if len(parts) < 4:
                continue
            timestamp, ticks, level, remainder = parts
            source = None
            message = remainder
            if remainder.startswith("[") and "]" in remainder:
                end = remainder.find("]")
                source = remainder[1:end]
                message = remainder[end + 1 :].strip()
            rows.append(
                {
                    "time": timestamp,
                    "ticks": ticks,
                    "level": level,
                    "source": source,
                    "message": message,
                }
            )
    data = pd.DataFrame(rows)
    if not data.empty:
        data["time"] = pd.to_datetime(
            data["time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
        data["ticks"] = pd.to_numeric(data["ticks"], errors="coerce")
    return data


def _resolve_data_folder(
    folder: Union[str, Path, int], data_root: str | Path
) -> Optional[Path]:
    if isinstance(folder, int):
        rows = list_data_folders(data_root)
        if folder < 0 or folder >= len(rows):
            return None
        return rows[folder].path
    return Path(folder)


def read_data_folder(
    folder: Union[str, Path, int], data_root: str | Path = "data"
) -> DataFolderContents:
    folder_path = _resolve_data_folder(folder, data_root)
    if folder_path is None:
        raise IndexError("data folder index out of range")
    licks_path = folder_path / "licks.dat"
    system_log_path = folder_path / "system.log"
    licks = read_licks_file(licks_path) if licks_path.is_file() else None
    system_log = read_system_log(system_log_path) if system_log_path.is_file() else None
    return DataFolderContents(
        name=folder_path.name,
        path=folder_path,
        licks=licks,
        system_log=system_log,
    )
