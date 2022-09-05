from footmav.data_definitions.whoscored.constants import EventType
from footmav.utils import whoscored_funcs as WF
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch
from fb_viz.definitions.events import EventDefinition, defensive_events
from sklearn.ensemble import IsolationForest
from matplotlib.lines import Line2D
import numpy as np
from math import ceil
from fb_viz.helpers.fonts import font_normal


def apply_event_plot(
    pitch: Pitch,
    ax,
    data,
    event_definition: EventDefinition,
    size: int,
    base_color: str,
    base_edge_color: str,
):
    """Apply the event plot to the axes"""

    sub_data = data.loc[
        (data["event_type"] == event_definition.event_type)
        & (data["outcomeType"] == event_definition.outcome_type)
    ]

    pitch.scatter(
        sub_data["x"],
        sub_data["y"],
        marker=event_definition.marker,
        color=event_definition.color if event_definition.color else base_color,
        edgecolors=[event_definition.edge_color] * sub_data.shape[0]
        if event_definition.edge_color
        else [base_edge_color] * sub_data.shape[0],
        ax=ax,
        s=size * event_definition.size_mult,
        alpha=0.7,
        linewidth=1,
        zorder=10,
    )


def draw_defensive_events_on_axes(
    ax: plt.Axes,
    data: pd.DataFrame,
    pitch: Pitch,
    base_size: float,
    base_color: str,
    base_edge_color: str,
):
    """Draw defensive events on the axes"""
    for event_type in defensive_events:
        apply_event_plot(
            pitch, ax, data, event_type, base_size, base_color, base_edge_color
        )


def draw_defensive_event_legend(
    ax,
    base_color,
    base_edge_color,
    base_size,
    horizontal=True,
    split=1,
    loc="upper center",
    facecolor="white",
    **kwargs
):
    """Draw the defensive event legend"""

    ax.set_facecolor(facecolor)
    kwargs["facecolor"] = facecolor
    dict_of_events = {
        event.label: event for event in sorted(defensive_events, key=lambda x: x.label)
    }
    legend_artists = [
        Line2D(
            [0],
            [0],
            marker=event.marker,
            label=event.label,
            markerfacecolor=event.color if event.color else base_color,
            markeredgecolor=event.edge_color if event.edge_color else base_edge_color,
            linewidth=0,
            markersize=base_size * event.size_mult,
        )
        for event in dict_of_events.values()
    ]
    bbox_coords = (
        0 if "left" in loc else 1 if "right" in loc else 0.5,
        1 if "upper" in loc else 0 if "lower" in loc else 0.5,
    )

    ncol = ceil(len(dict_of_events) / split) if horizontal else split
    total_elements_to_add = ncol * split - len(dict_of_events)

    array_legends = np.array(
        legend_artists
        + [Line2D([0], [0], linewidth=0, label="")] * total_elements_to_add
    )

    array_legends = np.resize(array_legends, (split, ncol))
    array_legends = [v for v in array_legends.T.flatten().tolist() if v != 0]
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    ax.legend(
        handles=array_legends,
        loc=loc,
        bbox_to_anchor=bbox_coords,
        ncol=ncol,
        labelcolor=base_color,
        prop=font_normal.prop,
        **kwargs,
    )
    return ax


def draw_convex_hull_without_outliers_on_axes(
    ax: plt.Axes,
    data: pd.DataFrame,
    pitch: Pitch,
    outlier_ratio: float = 0.1,
    color: str = "cornflowerblue",
):
    """Draw the convex hull without outliers on the axes"""
    model = IsolationForest(contamination=outlier_ratio, random_state=0)
    touch_events = [
        2,
        3,
        7,
        8,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        41,
        42,
        44,
        45,
        49,
        50,
        54,
        61,
        74,
    ]
    touch_events = [EventType(e) for e in touch_events]

    total_touches = data.loc[
        (data["event_type"].isin(touch_events))
        | ((data["event_type"] == EventType.Foul) & (data["outcomeType"] == 1))
        | (
            (data["event_type"] == EventType.Pass)
            & ~WF.col_has_qualifier(data, qualifier_code=6)
        )  # excludes corners
    ].copy()
    total_touches["include"] = model.fit_predict(total_touches[["x", "y"]])
    included = total_touches.loc[total_touches["include"] == 1]
    if included.shape[0] >= 4:
        hull = pitch.convexhull(
            included["x"],
            included["y"],
        )
        poly = pitch.polygon(
            hull, ax=ax, edgecolor=color, facecolor=color, alpha=0.3, zorder=3
        )
        return poly
    else:
        return None
