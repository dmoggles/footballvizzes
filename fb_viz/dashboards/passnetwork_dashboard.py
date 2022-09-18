from fb_viz.dashboards.dashboard import Dashboard, WithFormationDataMixin
from fb_viz.helpers.pitch_helpers import (
    plot_average_position_on_pitch_by_position_for_starting_formation,
    plot_pass_network_on_pitch_by_position_for_starting_formation,
)
from fb_viz.helpers.fonts import font_normal
from mplsoccer.pitch import Pitch
from footmav.data_definitions.whoscored.constants import EventType, PassType
from fb_viz.helpers.data_helpers import convert_player_name_for_display, lineup_card


class PassNetworkDashboard(WithFormationDataMixin, Dashboard):
    DATA_QUERY = """
        SELECT W.*, L.formation, L.position, L.shirt_number, L.pass_receiver, L.pass_receiver_position, L.pass_receiver_shirt_number, P.passtypes,
        IF(W.is_home_team=True, M.home_score, M.away_score) AS team_score,
        IF(W.is_home_team=True, M.away_score, M.home_score) AS opponent_score

        FROM football_data.whoscored W
        JOIN derived.whoscored_extra_event_info L
        ON W.id = L.id
        JOIN derived.whoscored_pass_types P 
        ON W.id = P.id
        JOIN whoscored_meta M 
        ON W.matchId = M.matchId
        WHERE W.matchId = {} AND W.team = '{}'
        """

    GRID_PARAMETERS = dict(
        left=0.15,
        grid_width=0.85,
        figheight=10,
        title_height=0.05,
        endnote_space=0,
        title_space=0,
        grid_height=0.85,
        endnote_height=0.02,
    )
    WATERMARK_DICT = dict(
        s="@McLachBot | www.mclachbot.com",
        x=0.01,
        y=3.5,
        ha="left",
        va="top",
    )
    HOME_IMAGE_COORDS = (0.18, 0.9, 0.07)
    AWAY_IMAGE_COORDS = (0.9, 0.9, 0.07)
    MCLACHEAD_COORDS = (0.17, 0.13, 0.07, 0.07)
    PASS_MININUM = 3
    DEBUG = False

    def populate_sidepanel(self, data, ax, pitch_color, text_color):
        data = data.copy()
        ax.set_facecolor(pitch_color)
        ax.axis("off")
        result_sets = {}
        result_sets["Passes Attempted"] = (
            data.loc[data["event_type"] == EventType.Pass]
            .groupby(["shirt_number", "player_name"])
            .agg({"x": "count"})
            .reset_index()
            .rename(columns={"x": "passes_attempted"})
            .sort_values("passes_attempted", ascending=False)
        )
        result_sets["Passes Completed"] = (
            data.loc[data["event_type"] == EventType.Pass]
            .groupby(["shirt_number", "player_name"])
            .agg({"outcomeType": "sum"})
            .reset_index()
            .rename(columns={"outcomeType": "passes_completed"})
            .sort_values("passes_completed", ascending=False)
        )
        pct_passes_completed = result_sets["Passes Completed"].merge(
            result_sets["Passes Attempted"], on=["shirt_number", "player_name"]
        )
        pct_passes_completed["pct_passes_completed"] = (
            pct_passes_completed["passes_completed"]
            / pct_passes_completed["passes_attempted"]
        )
        pct_passes_completed = pct_passes_completed.loc[
            pct_passes_completed["passes_attempted"] > 20
        ]
        pct_passes_completed = pct_passes_completed.sort_values(
            "pct_passes_completed", ascending=False
        )
        pct_passes_completed = pct_passes_completed[
            ["shirt_number", "player_name", "pct_passes_completed"]
        ]
        pct_passes_completed["pct_passes_completed"] = pct_passes_completed[
            "pct_passes_completed"
        ].apply(lambda x: f"{x*100:.0f}%")
        result_sets["Pct Passes Completed"] = pct_passes_completed
        data["progressive"] = data["passtypes"].apply(
            lambda x: x & (1 << (PassType.PROGRESSIVE.value - 1)) > 0
        )
        progressive_passes_attempted = (
            data.loc[data["event_type"] == EventType.Pass]
            .groupby(["shirt_number", "player_name"])
            .agg({"progressive": "sum"})
            .reset_index()
            .rename(columns={"progressive": "progressive_passes_attempted"})
            .sort_values("progressive_passes_attempted", ascending=False)
        )
        result_sets["Prog. Passes Attempted"] = progressive_passes_attempted
        progressive_passes_completed = (
            data.loc[(data["event_type"] == EventType.Pass) & (data["progressive"])]
            .groupby(["shirt_number", "player_name"])
            .agg({"outcomeType": "sum"})
            .reset_index()
            .rename(columns={"outcomeType": "progressive_passes_completed"})
            .sort_values("progressive_passes_completed", ascending=False)
        )
        result_sets["Prog. Passes Completed"] = progressive_passes_completed
        progressive_passes_received = (
            data.loc[(data["event_type"] == EventType.Pass) & (data["progressive"])]
            .groupby(["pass_receiver_shirt_number", "pass_receiver"])
            .agg({"x": "count"})
            .reset_index()
            .rename(
                columns={
                    "x": "progressive_passes_received",
                    "pass_receiver": "player_name",
                    "pass_receiver_shirt_number": "shirt_number",
                }
            )
            .sort_values("progressive_passes_received", ascending=False)
        )
        progressive_passes_received["shirt_number"] = progressive_passes_received[
            "shirt_number"
        ].astype(int)
        result_sets["Prog. Passes Received"] = progressive_passes_received
        for i, (k, v) in enumerate(result_sets.items()):
            v["player_name"] = v["player_name"].apply(convert_player_name_for_display)
            txt = f"\n{k}"
            txt += "\n--------------------------"

            for j, row in v[0:3].iterrows():
                txt += f"\n{row.values[0]:<3}{row.values[1]:<20}{row.values[2]:<3}"
            txt += "\n"
            ax.text(
                0.02,
                1.13 - i * 0.12,
                txt,
                family="monospace",
                transform=ax.transAxes,
                va="top",
                ha="left",
                color=text_color,
            )

    def _dashboard_plot_impl(
        self, fig, axes, pitch: Pitch, data, pitch_color, line_color, marker_base_color
    ):

        plot_average_position_on_pitch_by_position_for_starting_formation(
            axes["pitch"], pitch, data
        )
        plot_pass_network_on_pitch_by_position_for_starting_formation(
            axes["pitch"], pitch, data, min_combinations=self.PASS_MININUM
        )
        axes["sidepanel"] = fig.add_axes([0.0, 0.05, 0.15, 0.82])
        self.populate_sidepanel(data, axes["sidepanel"], pitch_color, line_color)

        starters, subs = lineup_card(data)

        axes["sidepanel"].text(
            transform=axes["sidepanel"].transAxes,
            color=line_color,
            family="monospace",
            fontsize=8,
            s=starters,
            x=0.02,
            y=0.4,
            ha="left",
            va="top",
        )
        axes["sidepanel"].text(
            transform=axes["sidepanel"].transAxes,
            color=line_color,
            family="monospace",
            fontsize=8,
            s=subs,
            x=0.02,
            y=0.17,
            ha="left",
            va="top",
        )
        axes["pitch"].text(
            transform=axes["pitch"].transAxes,
            color=line_color,
            fontproperties=font_normal.prop,
            fontsize=10,
            s=f"Red lines are progressive passes made between players.\n Minimum of {self.PASS_MININUM} passes to be shown.",
            x=0.975,
            y=0.04,
            ha="right",
            va="bottom",
        )
        return fig, axes
