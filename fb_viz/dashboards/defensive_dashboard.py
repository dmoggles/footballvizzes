import pandas as pd
from fb_viz.helpers.mplsoccer_helpers import make_grid
from fb_viz.helpers.pitch_helpers import (
    draw_defensive_event_legend,
    draw_defensive_events_on_axes,
    draw_convex_hull_without_outliers_on_axes,
)

from fb_viz.helpers.fonts import font_normal, font_bold
from footmav.data_definitions.whoscored.constants import EventType
import math
import json

from mplsoccer import add_image

from mplsoccer.pitch import Pitch


class DefensiveDashboard:
    def __init__(self, engine, image_grabber):
        self.engine = engine
        self.image_grabber = image_grabber

    def standard_header(self, data, ax, facecolor):
        formation = data["formation"].iloc[0]
        team_score = data["team_score"].iloc[0]
        opponent_score = data["opponent_score"].iloc[0]
        date = pd.Timestamp(data["match_date"].iloc[0]).strftime("%Y-%m-%d")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])
        ax.set_facecolor(facecolor)
        TITLE_TEXT = f"{self.team_display_name} vs {self.opponent_display_name} ({self.home_away.title()})"
        ax.text(
            0.5,
            0.7,
            TITLE_TEXT,
            color="#c7d5cc",
            va="center",
            ha="center",
            fontproperties=font_bold.prop,
            fontsize=25,
        )
        ax.text(
            0.5,
            0.25,
            f"Formation: {formation}.  Date: {date}. Result: {team_score}:{opponent_score} ",
            color="#c7d5cc",
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )

    def attach_positional_data(self, data):
        position_df = pd.read_sql(
            "SELECT * FROM football_data.whoscored_positions", self.engine
        )
        position_df["formation_name"] = position_df["formation_name"].apply(
            lambda x: x.replace("-", "")
        )
        data = pd.merge(
            data,
            position_df,
            left_on=["formation", "position"],
            right_on=["formation_name", "position"],
            suffixes=("", "_"),
            how="left",
        )
        return data

    def extract_names_sorted_by_position(self, data, exclude_positions=None):
        exclude_positions = exclude_positions or []
        subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]
        return (
            data.loc[
                (~data["player_name"].isna())
                & (~data["player_name"].isin(subs))
                & (~data["position"].isin(exclude_positions))
            ]
            .groupby("player_name")
            .first()
            .reset_index()
            .sort_values("team_player_formation")["player_name"]
            .tolist()
            + subs.tolist()
        )

    def get_data(self, team: str, date: str):

        query1 = f"""
        SELECT T1.matchId, T1.home, T1.away, 
            T2.team_name AS home_image_name, T2.decorated_name AS home_decorated_name, 
            T3.team_name AS away_image_name, T3.decorated_name AS away_decorated_name
        FROM football_data.whoscored_meta AS T1 
	        JOIN mclachbot_teams AS T2 
            ON T2.ws_team_name = T1.home
            JOIN mclachbot_teams AS T3
            ON T3.ws_team_name = T1.away        
        WHERE 
        match_date = '{date}' AND
        (home = '{team}' OR away = '{team}')
        """

        metadata_df = pd.read_sql(query1, self.engine)
        match_id = metadata_df["matchId"].iloc[0]
        home = metadata_df["home"].iloc[0]
        away = metadata_df["away"].iloc[0]
        if home == team:
            self.home_away = "Home"
            self.team = home
            self.team_image_name = metadata_df["home_image_name"].iloc[0]
            self.team_display_name = metadata_df["home_decorated_name"].iloc[0]
            self.opponent = away
            self.opponent_image_name = metadata_df["away_image_name"].iloc[0]
            self.opponent_display_name = metadata_df["away_decorated_name"].iloc[0]
        else:
            self.home_away = "Away"
            self.team = away
            self.team_image_name = metadata_df["away_image_name"].iloc[0]
            self.team_display_name = metadata_df["away_decorated_name"].iloc[0]
            self.opponent = home
            self.opponent_image_name = metadata_df["home_image_name"].iloc[0]
            self.opponent_display_name = metadata_df["home_decorated_name"].iloc[0]

        query2 = f"""
        SELECT W.*, L.formation, L.position, L.shirt_number, L.team_score, L.opponent_score FROM football_data.whoscored W
        JOIN derived.whoscored_mclachbot_legacy_data L
        ON W.id = L.id
        WHERE W.matchId = {match_id} AND W.team = '{team}'
        """

        data = pd.read_sql(query2, self.engine)
        data["qualifiers"] = data["qualifiers"].apply(json.loads)
        data["event_type"] = data["event_type"].apply(EventType)

        return self.attach_positional_data(data)

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
        if player_data.shape[0] > 0:
            position = position_array.iloc[0]
        else:
            position = ""
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

    def plot(
        self,
        data,
        pitch_color="#000011",
        line_color="#ffffff",
        marker_base_color="#bbbbbb",
        linewidth=1,
        grid_params=None,
    ):
        grid_params = grid_params or {}
        pitch = Pitch(
            pitch_type="opta",
            pitch_color=pitch_color,
            line_color=line_color,
            linewidth=linewidth,
        )
        fig, axes = make_grid(
            pitch,
            nrows=5,
            ncols=3,
            axis=False,
            **grid_params,
        )
        fig.set_facecolor(pitch_color)
        league = data["competition"].iloc[0]
        home_team_image = self.image_grabber(self.team_image_name, league)
        away_team_image = self.image_grabber(self.opponent_image_name, league)
        add_image(home_team_image, fig, left=0.05, bottom=0.89, width=0.05)
        add_image(away_team_image, fig, left=0.90, bottom=0.89, width=0.05)
        endnode = draw_defensive_event_legend(
            axes["endnote"],
            marker_base_color,
            line_color,
            7,
            split=3,
            framealpha=0,
            edgecolor=pitch_color,
            facecolor=pitch_color,
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
        self.standard_header(data, axes["title"], pitch_color)
        axes["endnote"].text(
            s="@McLachBot | www.mclachbot.com",
            x=0.99,
            y=0.01,
            ha="right",
            va="bottom",
            transform=axes["endnote"].transAxes,
            color=marker_base_color,
            fontproperties=font_normal.prop,
            fontsize=10,
        )
        return fig, axes
