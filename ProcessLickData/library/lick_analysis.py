from __future__ import annotations

import pandas as pd


def compute_lick_durations_ms(
    licks: pd.DataFrame, max_duration_ms: float | None = None
) -> list[float]:
    if "time" not in licks.columns or "state" not in licks.columns:
        raise ValueError("licks.dat data must include time and state columns.")

    data = licks.dropna(subset=["time", "state"]).sort_values("time").reset_index(
        drop=True
    )
    if data.empty:
        return []

    if not pd.api.types.is_datetime64_any_dtype(data["time"]):
        data["time"] = pd.to_datetime(
            data["time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
        )
        data = data.dropna(subset=["time"])

    durations_ms: list[float] = []
    start_time = None
    for _, row in data.iterrows():
        state = row["state"]
        if state == 1 and start_time is None:
            start_time = row["time"]
        elif state == 0 and start_time is not None:
            duration_ms = (row["time"] - start_time).total_seconds() * 1000.0
            if duration_ms >= 0:
                if max_duration_ms is None or duration_ms <= max_duration_ms:
                    durations_ms.append(duration_ms)
            start_time = None
    return durations_ms
