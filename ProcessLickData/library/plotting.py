from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

from .data_reader import read_data_folder


def plot_licks_bouts_water(
    folder: Union[int, str, Path],
    data_root: str | Path = "data",
    renderer: Optional[str] = "browser",
    show_system_events: bool = True,
    save_html: bool = False,
    html_name: str = "licks_plot.html",
    extra_html_path: Optional[Union[str, Path]] = None,
):
    contents = read_data_folder(folder, data_root=data_root)
    if contents.licks is None:
        raise ValueError("No licks.dat found for the selected folder.")

    data = contents.licks
    if "time" not in data.columns:
        raise ValueError("licks.dat data must include a time column.")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Water Level", "Licks and Bouts"),
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]],
    )

    data_time = data["time"].dropna()
    if data_time.empty:
        raise ValueError("licks.dat time column contains no valid timestamps.")

    data_start = data_time.min()
    data_end = data_time.max()

    starts = []
    if contents.system_log is not None and "message" in contents.system_log.columns:
        starts = (
            contents.system_log[
                contents.system_log["message"].str.contains(
                    "System Log Started", na=False
                )
            ]["time"]
            .dropna()
            .sort_values()
            .unique()
            .tolist()
        )

    if starts:
        if starts[0] > data_start:
            starts = [data_start] + starts
    else:
        starts = [data_start]

    session_ranges = []
    for idx, start_time in enumerate(starts):
        end_time = starts[idx + 1] if idx + 1 < len(starts) else data_end
        if end_time < start_time:
            continue
        session_ranges.append((start_time, end_time))

    if not session_ranges:
        session_ranges = [(data_start, data_end)]

    data_segments = []
    for start_time, end_time in session_ranges:
        segment_start = max(start_time, data_start)
        segment_end = min(end_time, data_end)
        if segment_end < segment_start:
            continue
        data_segments.append((segment_start, segment_end))

    background_colors = ["rgba(200,200,200,0.6)", "rgba(180,210,255,0.6)"]
    for idx, (start_time, end_time) in enumerate(session_ranges):
        fill = background_colors[idx % len(background_colors)]
        for plot_row in (1, 2):
            fig.add_shape(
                type="rect",
                xref="x",
                yref="y domain",
                x0=start_time,
                x1=end_time,
                y0=0,
                y1=1,
                fillcolor=fill,
                line_width=0,
                layer="below",
                row=plot_row,
                col=1,
            )

    water_min = None
    water_max = None
    if "water" in data.columns:
        water_min = data["water"].min()
        water_max = data["water"].max()
        cat_colors = {}
        if "cat_name" in data.columns:
            cats = [name for name in data["cat_name"].dropna().unique() if name != ""]
            for idx, cat in enumerate(sorted(cats)):
                cat_colors[cat] = qualitative.Plotly[idx % len(qualitative.Plotly)]
        else:
            cat_colors["Water"] = "#1f77b4"

        legend_shown = set()
        for idx, (start_time, end_time) in enumerate(data_segments):
            if idx == len(data_segments) - 1:
                mask = (data["time"] >= start_time) & (data["time"] <= end_time)
            else:
                mask = (data["time"] >= start_time) & (data["time"] < end_time)
            segment = data.loc[mask]
            if segment.empty:
                continue

            if "cat_name" not in segment.columns:
                fig.add_trace(
                    go.Scatter(
                        x=segment["time"],
                        y=segment["water"],
                        name="Water",
                        mode="lines+markers",
                        line=dict(color="#1f77b4"),
                        showlegend="Water" not in legend_shown,
                    ),
                    row=1,
                    col=1,
                )
                legend_shown.add("Water")
                continue

            run_start = 0
            cat_series = (
                segment["cat_name"].fillna("unknown").astype(str).reset_index(drop=True)
            )
            for run_idx in range(1, len(segment) + 1):
                if run_idx == len(segment) or cat_series.iloc[run_idx] != cat_series.iloc[run_start]:
                    run = segment.iloc[run_start:run_idx]
                    cat = cat_series.iloc[run_start]
                    color = cat_colors.get(cat, "#1f77b4")
                    showlegend = cat not in legend_shown
                    fig.add_trace(
                        go.Scatter(
                            x=run["time"],
                            y=run["water"],
                            name=f"Water ({cat})",
                            mode="lines+markers",
                            line=dict(color=color),
                            showlegend=showlegend,
                        ),
                        row=1,
                        col=1,
                    )
                    legend_shown.add(cat)
                    run_start = run_idx

    lick_max = None
    if "lick" in data.columns:
        lick_max = data["lick"].max()
        showlegend = True
        for idx, (start_time, end_time) in enumerate(data_segments):
            if idx == len(data_segments) - 1:
                mask = (data["time"] >= start_time) & (data["time"] <= end_time)
            else:
                mask = (data["time"] >= start_time) & (data["time"] < end_time)
            segment = data.loc[mask]
            if segment.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=segment["time"],
                    y=segment["lick"],
                    name="Licks",
                    mode="lines+markers",
                    line=dict(color="#2ca02c"),
                    showlegend=showlegend,
                ),
                row=2,
                col=1,
                secondary_y=False,
            )
            showlegend = False

    bout_max = None
    if "bout" in data.columns:
        bout_max = data["bout"].max()
        showlegend = True
        for idx, (start_time, end_time) in enumerate(data_segments):
            if idx == len(data_segments) - 1:
                mask = (data["time"] >= start_time) & (data["time"] <= end_time)
            else:
                mask = (data["time"] >= start_time) & (data["time"] < end_time)
            segment = data.loc[mask]
            if segment.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=segment["time"],
                    y=segment["bout"],
                    name="Bouts",
                    mode="lines+markers",
                    line=dict(color="#d62728"),
                    showlegend=showlegend,
                ),
                row=2,
                col=1,
                secondary_y=True,
            )
            showlegend = False

    fig.update_layout(
        title_text=f"Licks and Water - {contents.name}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Water", row=1, col=1)
    fig.update_yaxes(title_text="Licks", row=2, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Bouts", row=2, col=1, secondary_y=True)

    if show_system_events and contents.system_log is not None:
        system_log = contents.system_log
        if "message" in system_log.columns and "time" in system_log.columns:
            starts = system_log[
                system_log["message"].str.contains("System Log Started", na=False)
            ]
            switches = system_log[
                system_log["message"].str.contains("Cat switched", na=False)
            ]
            if water_min is not None and water_max is not None:
                water_low, water_high = water_min, water_max
            else:
                water_low, water_high = 0, 1
            licks_high = max(
                [value for value in [lick_max, bout_max] if value is not None] or [1]
            )
            licks_low = 0
            start_times = [t for t in starts["time"].tolist() if pd.notna(t)]
            if start_times:
                fig.add_trace(
                    go.Scatter(
                        x=start_times,
                        y=[water_high] * len(start_times),
                        mode="markers",
                        marker=dict(
                            symbol="triangle-down",
                            size=10,
                            color="#9467bd",
                            line=dict(width=1, color="#5f4b8b"),
                        ),
                        hovertemplate=(
                            "%{x|%Y-%m-%d %H:%M:%S.%f}<br>"
                            "System Log Started"
                            "<extra></extra>"
                        ),
                        name="System Log Started",
                        showlegend=True,
                    ),
                    row=1,
                    col=1,
                )
            for _, row in switches.iterrows():
                if pd.isna(row["time"]):
                    continue
                message = row.get("message", "Cat switched")
                for plot_row, y0, y1 in (
                    (1, water_low, water_high),
                    (2, licks_low, licks_high),
                ):
                    fig.add_trace(
                        go.Scatter(
                            x=[row["time"], row["time"]],
                            y=[y0, y1],
                            mode="lines",
                            line=dict(color="#ff7f0e", width=1),
                            hovertemplate=(
                                "%{x|%Y-%m-%d %H:%M:%S.%f}<br>"
                                f"{message}"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                        ),
                        row=plot_row,
                        col=1,
                    )

    if renderer is not None:
        fig.show(renderer=renderer)
    if save_html:
        output_path = Path(contents.path) / html_name
        fig.write_html(output_path, include_plotlyjs="inline")
    if extra_html_path is not None:
        extra_path = Path(extra_html_path)
        if extra_path.is_dir() or str(extra_html_path).endswith(("/", "\\")):
            extra_path = extra_path / html_name
        fig.write_html(extra_path, include_plotlyjs="inline")
    return fig
