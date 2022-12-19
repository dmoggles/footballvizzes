from abc import ABC, abstractmethod
from fb_viz.helpers.fonts import font_normal, font_bold
import pandas as pd
from footmav.data_definitions.whoscored.constants import EventType
from fb_viz.helpers.mclachbot_helpers import get_mclachhead
from mplsoccer import add_image
from fb_viz.helpers.mplsoccer_helpers import make_grid
from mplsoccer.pitch import Pitch
import json


class Dashboard(ABC):
    GRID_PARAMETERS = {
        "title_height": 0.06,
        "figheight": 12,
        "grid_height": 0.85,
        "endnote_height": 0.06,
    }
    PITCH_COLOR = "#000011"
    GRID_NROWS = 1
    GRID_NCOLS = 1
    HOME_IMAGE_COORDS = (0.05, 0.95, 0.05)
    AWAY_IMAGE_COORDS = (0.95, 0.95, 0.05)
    MCLACHEAD_COORDS = (0.89, 0.00, 0.07, 0.07)
    WATERMARK_DICT = dict(
        s="@McLachBot | www.mclachbot.com",
        x=0.99,
        y=1.15,
        ha="right",
        va="top",
    )
    DEBUG = False

    def __init__(self, connection, image_grabber):
        self.connection = connection
        self.image_grabber = image_grabber

    def standard_header(self, data, fig, ax, facecolor):
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
        if len(TITLE_TEXT) > 30:
            size = 20
        else:
            size = 25
        ax.text(
            0.5,
            0.7,
            TITLE_TEXT,
            color="#c7d5cc",
            va="center",
            ha="center",
            fontproperties=font_bold.prop,
            fontsize=size,
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
        league = data["competition"].iloc[0]
        home_team_image = self.image_grabber(self.team_image_name, league)
        away_team_image = self.image_grabber(self.opponent_image_name, league)
        if home_team_image:
            add_image(
                home_team_image,
                fig,
                left=self.HOME_IMAGE_COORDS[0],
                bottom=self.HOME_IMAGE_COORDS[1],
                width=self.HOME_IMAGE_COORDS[2],
            )
        if away_team_image:
            add_image(
                away_team_image,
                fig,
                left=self.AWAY_IMAGE_COORDS[0],
                bottom=self.AWAY_IMAGE_COORDS[1],
                width=self.AWAY_IMAGE_COORDS[2],
            )

    def extract_names_sorted_by_position(self, data, exclude_positions=None):
        exclude_positions = exclude_positions or []
        subs = data.loc[data["event_type"] == EventType.SubstitutionOn, "player_name"]

        list_of_names = (
            data.loc[
                (~data["player_name"].isna())
                & (~data["player_name"].isin(subs))
                & (~data["position"].isin(exclude_positions))
            ]
            .groupby("player_name")
            .first()
            .reset_index()
            .sort_values("sort_id")["player_name"]
            .tolist()
            + subs.tolist()
        )
        if len(list_of_names) > 15:
            list_of_names = list_of_names[:15]
        return list_of_names

    def get_match_day_data(self, team: str, date: str) -> int:

        query1 = f"""
        SELECT T1.matchId, T1.home, T1.away, 
            T2.ws_team_name AS home_image_name, T2.decorated_name AS home_decorated_name, 
            T3.ws_team_name AS away_image_name, T3.decorated_name AS away_decorated_name
        FROM football_data.whoscored_meta AS T1 
	        JOIN mclachbot_teams AS T2 
            ON T2.ws_team_name = T1.home
            JOIN mclachbot_teams AS T3
            ON T3.ws_team_name = T1.away        
        WHERE 
        match_date = '{date}' AND
        (home = '{team}' OR away = '{team}')
        """

        metadata_df = self.connection.query(query1)
        match_id = metadata_df["matchId"].iloc[0]
        home = metadata_df["home"].iloc[0]
        away = metadata_df["away"].iloc[0]
        if home == team:
            self.home_away = "Home"
            self.team = home
            self.team_image_name = (
                metadata_df["home_image_name"].iloc[0].replace(".", "").lower()
            )
            self.team_display_name = metadata_df["home_decorated_name"].iloc[0]
            self.opponent = away
            self.opponent_image_name = (
                metadata_df["away_image_name"].iloc[0].replace(".", "").lower()
            )
            self.opponent_display_name = metadata_df["away_decorated_name"].iloc[0]
        else:
            self.home_away = "Away"
            self.team = away
            self.team_image_name = (
                metadata_df["away_image_name"].iloc[0].replace(".", "").lower()
            )
            self.team_display_name = metadata_df["away_decorated_name"].iloc[0]
            self.opponent = home
            self.opponent_image_name = (
                metadata_df["home_image_name"].iloc[0].replace(".", "").lower()
            )
            self.opponent_display_name = metadata_df["home_decorated_name"].iloc[0]
        return match_id

    @abstractmethod
    def get_data(self, team: str, date: str):
        pass

    def plot(
        self,
        data,
        pitch_color=None,
        line_color="#ffffff",
        marker_base_color="#bbbbbb",
        linewidth=1,
        grid_params=None,
    ):
        pitch_color = pitch_color or self.PITCH_COLOR
        grid_params = grid_params or self.GRID_PARAMETERS
        pitch = Pitch(
            pitch_type="opta",
            pitch_color=pitch_color,
            line_color=line_color,
            linewidth=linewidth,
        )

        fig, axes = make_grid(
            pitch,
            nrows=self.GRID_NROWS,
            ncols=self.GRID_NCOLS,
            axis=self.DEBUG,
            **grid_params,
        )
        if not self.DEBUG:
            fig.set_facecolor(pitch_color)

            add_image(
                get_mclachhead(),
                fig,
                left=self.MCLACHEAD_COORDS[0],
                bottom=self.MCLACHEAD_COORDS[1],
                width=self.MCLACHEAD_COORDS[2],
                height=self.MCLACHEAD_COORDS[3],
            )
            self.standard_header(data, fig, axes["title"], pitch_color)
            axes["endnote"].text(
                transform=axes["endnote"].transAxes,
                color=marker_base_color,
                fontproperties=font_normal.prop,
                fontsize=10,
                **self.WATERMARK_DICT,
            )
            axes["endnote"].set_facecolor(pitch_color)
        return self._dashboard_plot_impl(
            fig, axes, pitch, data, pitch_color, line_color, marker_base_color
        )

    @abstractmethod
    def _dashboard_plot_impl(
        self, fig, axes, pitch, data, pitch_color, line_color, marker_base_color
    ):
        pass


class WithFormationDataMixin:
    DATA_QUERY = """
        SELECT W.*, L.formation, L.position, L.shirt_number, 
        IF(W.is_home_team=True, M.home_score, M.away_score) AS team_score,
        IF(W.is_home_team=True, M.away_score, M.home_score) AS opponent_score
        FROM football_data.whoscored W
        JOIN derived.whoscored_extra_event_info L
        ON W.id = L.id
        JOIN football_data.whoscored_meta M
        ON W.matchId = M.matchId
        WHERE W.matchId = {} AND W.team = '{}'
        ORDER BY W.period, W.minute, W.second, W.eventId
        """

    def attach_positional_data(self, data):
        position_df = self.connection.query(
            "SELECT * FROM football_data.whoscored_positions"
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

    def get_data(self, team: str, date: str):

        match_id = self.get_match_day_data(team, date)

        query2 = self.DATA_QUERY.format(match_id, self.team)

        data = self.connection.wsquery(query2)

        return self.attach_positional_data(data)
