from footmav.data_definitions.whoscored.constants import EventType, PassType
from footmav.utils import whoscored_funcs as WF
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer.pitch import Pitch
from fb_viz.definitions.events import (
    EventDefinition,
    defensive_events,
    get_touch_events,
)
from sklearn.ensemble import IsolationForest
from matplotlib.lines import Line2D
import numpy as np
from math import ceil
from fb_viz.helpers.fonts import font_normal
from fb_viz.helpers.team_colour_helpers import team_colours
from matplotlib.colors import to_rgba
from footmav.utils import whoscored_funcs as wf
import matplotlib.patheffects as path_effects


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


def draw_passes_on_axes(
    ax: plt.Axes,
    data: pd.DataFrame,
    pitch: Pitch,
    linewidth: float = 3,
):
    data["passtypes"] = wf.classify_passes(data)
    passes = data.loc[
        (data["event_type"] == EventType.Pass)
        & (~wf.col_has_qualifier(data, qualifier_code=107))
    ]
    regular_pass_complete = passes.loc[
        (passes["outcomeType"] == 1) & (passes["passtypes"] == 0)
    ]
    regular_pass_incomplete = passes.loc[
        (passes["outcomeType"] == 0) & (passes["passtypes"] == 0)
    ]
    progressive_pass_complete = passes.loc[
        (passes["outcomeType"] == 1) & (passes["passtypes"] == 2)
    ]
    progressive_pass_incomplete = passes.loc[
        (passes["outcomeType"] == 0) & (passes["passtypes"] == 2)
    ]
    cutbacks_complete = passes.loc[
        (passes["outcomeType"] == 1) & (passes["passtypes"] % 2 == 1)
    ]
    cutbacks_incomplete = passes.loc[
        (passes["outcomeType"] == 0) & (passes["passtypes"] % 2 == 1)
    ]
    if regular_pass_complete.shape[0] > 0:
        pitch.lines(
            regular_pass_complete["x"],
            regular_pass_complete["y"],
            regular_pass_complete["endX"],
            regular_pass_complete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="completed passes",
            capstyle="round",
            color="lightcoral",
            ax=ax,
            zorder=3,
        )
    if regular_pass_incomplete.shape[0] > 0:
        pitch.lines(
            regular_pass_incomplete["x"],
            regular_pass_incomplete["y"],
            regular_pass_incomplete["endX"],
            regular_pass_incomplete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="incomplete passes",
            capstyle="round",
            color="darkred",
            ax=ax,
            alpha=0.6,
        )
    if progressive_pass_complete.shape[0] > 0:
        pitch.lines(
            progressive_pass_complete["x"],
            progressive_pass_complete["y"],
            progressive_pass_complete["endX"],
            progressive_pass_complete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="completed progressive passes",
            capstyle="round",
            color="lightblue",
            ax=ax,
            zorder=3,
        )
    if progressive_pass_incomplete.shape[0] > 0:
        pitch.lines(
            progressive_pass_incomplete["x"],
            progressive_pass_incomplete["y"],
            progressive_pass_incomplete["endX"],
            progressive_pass_incomplete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="incomplete progressive passes",
            capstyle="round",
            color="blue",
            ax=ax,
            alpha=0.6,
        )
    if cutbacks_complete.shape[0] > 0:
        pitch.lines(
            cutbacks_complete["x"],
            cutbacks_complete["y"],
            cutbacks_complete["endX"],
            cutbacks_complete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="completed cutbacks",
            capstyle="round",
            color="lightgreen",
            ax=ax,
            zorder=3,
        )
    if cutbacks_incomplete.shape[0] > 0:
        pitch.lines(
            cutbacks_incomplete["x"],
            cutbacks_incomplete["y"],
            cutbacks_incomplete["endX"],
            cutbacks_incomplete["endY"],
            lw=linewidth,
            transparent=True,
            comet=True,
            label="incomplete progressive passes",
            capstyle="round",
            color="green",
            ax=ax,
            alpha=0.6,
        )


def draw_pass_legend_on_axes(
    ax: plt.Axes, base_color: str, base_edge_color: str, loc: str = "lower left"
):
    legend_elements = [
        Line2D(
            [0],
            [0],
            color="lightcoral",
            marker="o",
            label="Complete Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="darkred",
            marker="o",
            label="Incomplete Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="lightblue",
            marker="o",
            label="Complete Progressive Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="blue",
            marker="o",
            label="Incomplete Progressive Pass",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="lightgreen",
            marker="o",
            label="Complete Cutback",
            markersize=5,
            linewidth=0,
        ),
        Line2D(
            [0],
            [0],
            color="green",
            marker="o",
            label="Incomplete Cutback",
            markersize=5,
            linewidth=0,
        ),
    ]
    ax.legend(
        ncol=3,
        handles=legend_elements,
        loc=loc,
        # bbox_to_anchor=(0.0, 0.0),
        facecolor=base_color,
        edgecolor=base_edge_color,
        labelcolor=base_edge_color,
        framealpha=1,
        labelspacing=0.5,
        fancybox=True,
        borderpad=0.25,
        handletextpad=0.1,
        prop=font_normal.prop,
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
    total_touches = get_touch_events(data)
    if total_touches.shape[0] <= 4:
        return None
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


def get_starter_locations(data, label_column):
    subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]

    starter_actions = get_touch_events(data.loc[~data["player_name"].isin(subs)])
    by_player = starter_actions.groupby(list(set(["player_name", label_column]))).agg(
        {"x": ["count", "mean"], "y": ["mean"]}
    )
    by_player.columns = ["count", "x", "y"]
    by_player = by_player.reset_index()
    return by_player


def get_locations_by_starting_formation(data, label_column):

    actions = get_touch_events(data.loc[data["formation"] == data["formation"].iloc[0]])
    py_position = actions.groupby(list(set(["position", label_column]))).agg(
        {"x": ["count", "mean"], "y": ["mean"]}
    )
    py_position.columns = ["count", "x", "y"]
    py_position = py_position.reset_index()
    return py_position


def plot_average_position_on_pitch_by_player_for_starters(
    ax, pitch, data, min_size=15, max_size=40, max_count=120
):
    label_column = "shirt_number"
    team = data["team"].iloc[0]
    league = data["competition"].iloc[0]
    by_player = get_starter_locations(data, label_column)
    by_player["s"] = min_size + by_player["count"] / max_count * (max_size - min_size)
    colours = team_colours(team, league)
    pitch.scatter(
        by_player["x"],
        by_player["y"],
        s=by_player["s"] ** 2,
        ax=ax,
        zorder=4,
        c=colours[0],
    )
    for i, row in by_player.iterrows():
        pitch.annotate(
            row[label_column],
            xy=(row.x, row.y),
            va="center",
            ha="center",
            zorder=5,
            ax=ax,
            c=colours[1],
        )


def plot_average_position_on_pitch_by_position_for_starting_formation(
    ax, pitch, data, min_size=15, max_size=40, max_count=120
):
    label_column = "position"
    team = data["team"].iloc[0]
    league = data["competition"].iloc[0]
    by_player = get_locations_by_starting_formation(data, label_column)
    by_player["s"] = min_size + by_player["count"] / max_count * (max_size - min_size)
    colours = team_colours(team, league)
    pitch.scatter(
        by_player["x"],
        by_player["y"],
        s=by_player["s"] ** 2,
        ax=ax,
        zorder=4,
        c=colours[0],
    )
    for i, row in by_player.iterrows():
        pitch.annotate(
            row[label_column],
            xy=(row.x, row.y),
            va="center",
            ha="center",
            zorder=5,
            ax=ax,
            c=colours[1],
        )


def get_starter_pass_network_by_name(data, min_combinations):
    subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]

    player_passes = data.loc[
        (data["event_type"] == EventType.Pass)
        & (data["outcomeType"] == 1)
        & (~data["player_name"].isin(subs))
        & (~data["pass_receiver"].isin(subs))
        & (data["pass_receiver"].notnull())
    ].copy()
    player_passes["pair"] = player_passes.apply(
        lambda r: "_".join(
            sorted([r["player_name"], r["pass_receiver"] if r["pass_receiver"] else ""])
        ),
        axis=1,
    )

    player_passes["progressive_pass"] = player_passes["passtypes"].apply(
        lambda x: x & (1 << (PassType.PROGRESSIVE.value - 1)) > 0
    )
    pass_groupings = player_passes.groupby("pair").agg(
        {
            "x": "count",
            "player_name": "first",
            "pass_receiver": "first",
            "progressive_pass": "sum",
        }
    )
    pass_groupings = pass_groupings[pass_groupings["pass_receiver"].notnull()]
    pass_groupings.columns = ["count", "player", "receiver", "progressive_count"]
    pass_groupings = pass_groupings.loc[pass_groupings["count"] >= min_combinations]
    return pass_groupings


def get_starter_pass_network_by_position(data, min_combinations):
    subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]

    player_passes = data.loc[
        (data["event_type"] == EventType.Pass)
        & (data["outcomeType"] == 1)
        & (data["formation"] == data["formation"].iloc[0])
        & (data["pass_receiver_position"].notnull())
        & (data["position"].notnull())
    ].copy()
    player_passes["pair"] = player_passes.apply(
        lambda r: "_".join(
            sorted(
                [
                    r["position"],
                    r["pass_receiver_position"] if r["pass_receiver_position"] else "",
                ]
            )
        ),
        axis=1,
    )

    player_passes["progressive_pass"] = player_passes["passtypes"].apply(
        lambda x: x & (1 << (PassType.PROGRESSIVE.value - 1)) > 0
    )
    pass_groupings = player_passes.groupby("pair").agg(
        {
            "x": "count",
            "position": "first",
            "pass_receiver_position": "first",
            "progressive_pass": "sum",
        }
    )
    pass_groupings = pass_groupings[pass_groupings["pass_receiver_position"].notnull()]
    pass_groupings.columns = ["count", "player", "receiver", "progressive_count"]
    pass_groupings = pass_groupings.loc[pass_groupings["count"] >= min_combinations]
    return pass_groupings


def plot_pass_network_on_pitch_by_player_for_starters(
    ax,
    pitch,
    data,
    max_combinations=20,
    min_width=1,
    max_width=20,
    min_transparency=0.3,
    min_combinations=3,
):
    pass_groupings = get_starter_pass_network_by_name(data, min_combinations)
    average_positions = get_starter_locations(data, "shirt_number")
    pass_groupings = pd.merge(
        pass_groupings,
        average_positions[["player_name", "x", "y"]],
        left_on="player",
        right_on="player_name",
        how="left",
    ).rename(columns={"x": "start_x", "y": "start_y"})
    pass_groupings = pd.merge(
        pass_groupings,
        average_positions[["player_name", "x", "y"]],
        left_on="receiver",
        right_on="player_name",
        how="left",
    ).rename(columns={"x": "end_x", "y": "end_y"})

    total_max = max(pass_groupings["count"].max(), max_combinations)
    pass_groupings["width"] = min_width + (
        pass_groupings["count"] - min_combinations
    ) / total_max * (max_width - min_width)
    pass_groupings["pp_width"] = min_width + (
        pass_groupings["progressive_count"] - min_combinations
    ) / total_max * (max_width - min_width)

    pass_groupings_pp = pass_groupings.loc[
        pass_groupings["progressive_count"] > min_combinations
    ]
    color = np.array(to_rgba("white"))
    color = np.tile(color, (len(pass_groupings), 1))
    c_transparency = min_transparency + (
        pass_groupings["count"] - min_combinations
    ) / total_max * (1 - min_transparency)
    color[:, 3] = c_transparency
    pitch.lines(
        pass_groupings["start_x"],
        pass_groupings["start_y"],
        pass_groupings["end_x"],
        pass_groupings["end_y"],
        ax=ax,
        color=color,
        lw=pass_groupings["width"],
        zorder=2,
    )
    pitch.lines(
        pass_groupings_pp["start_x"],
        pass_groupings_pp["start_y"],
        pass_groupings_pp["end_x"],
        pass_groupings_pp["end_y"],
        ax=ax,
        color="red",
        lw=pass_groupings_pp["pp_width"],
        zorder=3,
    )
    return pass_groupings


def plot_pass_network_on_pitch_by_position_for_starting_formation(
    ax,
    pitch,
    data,
    max_combinations=20,
    min_width=1,
    max_width=20,
    min_transparency=0.3,
    min_combinations=3,
):
    pass_groupings = get_starter_pass_network_by_position(data, min_combinations)
    average_positions = get_locations_by_starting_formation(data, "position")
    pass_groupings = pd.merge(
        pass_groupings,
        average_positions[["position", "x", "y"]],
        left_on="player",
        right_on="position",
        how="left",
    ).rename(columns={"x": "start_x", "y": "start_y"})
    pass_groupings = pd.merge(
        pass_groupings,
        average_positions[["position", "x", "y"]],
        left_on="receiver",
        right_on="position",
        how="left",
    ).rename(columns={"x": "end_x", "y": "end_y"})

    total_max = max(pass_groupings["count"].max(), max_combinations)
    pass_groupings["width"] = min_width + (
        pass_groupings["count"] - min_combinations
    ) / total_max * (max_width - min_width)
    pass_groupings["pp_width"] = min_width + (
        pass_groupings["progressive_count"] - min_combinations
    ) / total_max * (max_width - min_width)

    pass_groupings_pp = pass_groupings.loc[
        pass_groupings["progressive_count"] > min_combinations
    ]
    color = np.array(to_rgba("white"))
    color = np.tile(color, (len(pass_groupings), 1))
    c_transparency = min_transparency + (
        pass_groupings["count"] - min_combinations
    ) / total_max * (1 - min_transparency)
    color[:, 3] = c_transparency
    pitch.lines(
        pass_groupings["start_x"],
        pass_groupings["start_y"],
        pass_groupings["end_x"],
        pass_groupings["end_y"],
        ax=ax,
        color=color,
        lw=pass_groupings["width"],
        zorder=2,
    )
    pitch.lines(
        pass_groupings_pp["start_x"],
        pass_groupings_pp["start_y"],
        pass_groupings_pp["end_x"],
        pass_groupings_pp["end_y"],
        ax=ax,
        color="red",
        lw=pass_groupings_pp["pp_width"],
        zorder=3,
    )
    return pass_groupings


def plot_positional_heatmap_on_pitch(
    ax,
    pitch,
    data,
    base_edge_color: str = "#ffffff",
    scatter_color: str = "blue",
    cmap="hot",
):
    passes_mask = (data["event_type"] == EventType.Pass) & (
        ~wf.col_has_qualifier(data, qualifier_code=107)
    )

    path_eff = [
        path_effects.Stroke(linewidth=3, foreground="black"),
        path_effects.Normal(),
    ]

    bin_statistic = pitch.bin_statistic_positional(
        data.loc[passes_mask].x,
        data.loc[passes_mask].y,
        statistic="count",
        positional="full",
        normalize=True,
    )
    pitch.heatmap_positional(
        bin_statistic, ax=ax, cmap=cmap, edgecolors=base_edge_color
    )
    pitch.scatter(
        data.loc[passes_mask].x,
        data.loc[passes_mask].y,
        c=scatter_color,
        s=2,
        ax=ax,
    )
    pitch.label_heatmap(
        bin_statistic,
        color=base_edge_color,
        fontsize=11,
        ax=ax,
        ha="center",
        va="center",
        str_format="{:.0%}",
        path_effects=path_eff,
        zorder=20,
    )
