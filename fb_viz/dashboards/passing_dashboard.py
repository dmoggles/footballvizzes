from multiprocessing import Event
from footmav.data_definitions.whoscored.constants import EventType
from fb_viz.helpers.pitch_helpers import (
    draw_pass_legend_on_axes,
    draw_passes_on_axes,
    plot_positional_heatmap_on_pitch,
)
from footmav.utils import whoscored_funcs as wf
import cmasher as cmr
from fb_viz.dashboards.dashboard import Dashboard, WithFormationDataMixin
from fb_viz.helpers.fonts import font_normal
import math


class PassingDashboard(WithFormationDataMixin, Dashboard):
    DATA_QUERY = """
        SELECT W.*, L.formation, L.position, L.shirt_number, L.pass_receiver, L.pass_receiver_position, L.pass_receiver_shirt_number, 
        IF(W.is_home_team=True, M.home_score, M.away_score) AS team_score,
        IF(W.is_home_team=True, M.away_score, M.home_score) AS opponent_score

        FROM football_data.whoscored W
        JOIN derived.whoscored_extra_event_info L
        ON W.id = L.id
        JOIN whoscored_meta M 
        ON W.matchId = M.matchId
        WHERE W.matchId = {} AND W.team = '{}'
        """
    GRID_PARAMETERS = {
        "title_height": 0.06,
        "figheight": 12,
        "grid_height": 0.85,
        "endnote_height": 0.06,
    }

    GRID_NROWS = 6
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
        passes = player_data.loc[
            (player_data["event_type"] == EventType.Pass)
            & (~wf.col_has_qualifier(player_data, qualifier_code=107))
        ]
        n_tot = len(passes)
        completed_mask = passes["outcomeType"] == 1
        n_comp = len(passes[completed_mask])
        ax.text(
            0.03,
            0.97,
            f"{position} | {number} | {player_name_display.title()} | {n_comp}/{n_tot} ({n_comp/n_tot * 100 if n_tot > 0 else 0:.0f}%)",
            ha="left",
            va="bottom",
            fontsize=10,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )
        ax.text(
            0.03,
            0.04,
            sub_str,
            ha="left",
            va="bottom",
            fontsize=8,
            color=text_color,
            fontproperties=font_normal.prop,
            transform=ax.transAxes,
        )

    def _dashboard_plot_impl(
        self, fig, axes, pitch, data, pitch_color, line_color, marker_base_color
    ):
        data = data.sort_values(["period", "minute", "second", "eventId"])
        names = self.extract_names_sorted_by_position(data)
        for i, name in enumerate(names):
            r_i = int(math.floor(i / 3))
            r_j = i % 3
            player_data = data[data["player_name"] == name].copy()
            draw_passes_on_axes(
                axes["pitch"][(r_i, r_j)], player_data, pitch, linewidth=3
            )
            self.player_name_and_info(
                axes["pitch"][(r_i, r_j)], player_data, line_color
            )

        plot_positional_heatmap_on_pitch(
            axes["pitch"][5][1], pitch, data, base_edge_color=line_color
        )
        axes["pitch"][5][1].text(
            0,
            107,
            f"Positional Pass Distribution",
            ha="left",
            va="center",
            fontsize=12,
            color=line_color,
            fontproperties=font_normal.prop,
        )
        successful_pass_mask = (
            (data["event_type"] == EventType.Pass)
            & (data["outcomeType"] == 1)
            & (~wf.col_has_qualifier(data, qualifier_code=107))
        )
        pitch.kdeplot(
            data.loc[successful_pass_mask]["endX"],
            data.loc[successful_pass_mask]["endY"],
            ax=axes["pitch"][5][2],
            levels=50,
            shade=True,
            cmap=cmr.amber,
            thresh=0.1,
            alpha=0.8,
            zorder=0,
        )
        axes["pitch"][5][2].text(
            0,
            107,
            f"Passes Received Locations",
            ha="left",
            va="center",
            fontsize=12,
            color=line_color,
            fontproperties=font_normal.prop,
        )
        draw_pass_legend_on_axes(axes["endnote"], pitch_color, line_color)
        return fig, axes
