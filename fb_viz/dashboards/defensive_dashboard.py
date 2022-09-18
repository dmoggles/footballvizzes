import pandas as pd
from fb_viz.dashboards.dashboard import Dashboard, WithFormationDataMixin

from fb_viz.helpers.pitch_helpers import (
    draw_defensive_event_legend,
    draw_defensive_events_on_axes,
    draw_convex_hull_without_outliers_on_axes,
)

from fb_viz.helpers.fonts import font_normal, font_bold
from footmav.data_definitions.whoscored.constants import EventType
import math
import json


class DefensiveDashboard(WithFormationDataMixin, Dashboard):
    GRID_PARAMETERS = {
        "title_height": 0.06,
        "figheight": 12,
        "grid_height": 0.85,
        "endnote_height": 0.06,
    }

    GRID_NROWS = 5
    GRID_NCOLS = 3

    def player_name_and_info(self, ax, player_data, text_color):
        player_name = player_data["player_name"].iloc[0]

        sub_on = player_data.loc[player_data["event_type"] == EventType.SubstitutionOn]
        sub_off = player_data.loc[
            player_data["event_type"] == EventType.SubstitutionOff
        ]
        sub_str = ""
        if len(sub_on) > 0:
            sub_str = " ".join([sub_str, f"On: {sub_on['minute'].iloc[0]}"])
        if len(sub_off) > 0:
            sub_str = " ".join([sub_str, f"Off: {sub_off['minute'].iloc[0]}"])

        position_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])), "position"
        ]
        if position_array.shape[0] > 0:
            position = position_array.iloc[0]
        else:
            position = "Sub"
        number_array = player_data.loc[
            (~player_data["position"].isin(["Substitute", "Error"])),
            "shirt_number",
        ]
        if number_array.shape[0] > 0:
            number = number_array.iloc[0]
        else:
            number = ""

        player_name_display = (
            " ".join(
                [
                    f"{p[0]}." if i == 0 else p
                    for i, p in enumerate(player_name.split(" "))
                ]
            )
            if " " in player_name
            else player_name
        )
        ax.text(
            0.03,
            0.97,
            f"{position} | {number} | {player_name_display.title()} ",
            ha="left",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )
        ax.text(
            0.97,
            0.97,
            sub_str,
            ha="right",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )

    def _dashboard_plot_impl(
        self, fig, axes, pitch, data, pitch_color, line_color, marker_base_color
    ):
        endnode = draw_defensive_event_legend(
            axes["endnote"],
            marker_base_color,
            line_color,
            7,
            split=3,
            framealpha=0,
            edgecolor=pitch_color,
            facecolor=pitch_color,
            loc="upper left",
        )
        names = self.extract_names_sorted_by_position(data, exclude_positions=["GK"])
        for i, name in enumerate(names):
            r_i = int(math.floor(i / 3))
            r_j = i % 3

            if name:
                draw_defensive_events_on_axes(
                    axes["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    pitch,
                    25,
                    marker_base_color,
                    line_color,
                )
                draw_convex_hull_without_outliers_on_axes(
                    axes["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    pitch,
                    0.1,
                )
                self.player_name_and_info(
                    axes["pitch"][(r_i, r_j)],
                    data.loc[data["player_name"] == name],
                    line_color,
                )

        return fig, axes
