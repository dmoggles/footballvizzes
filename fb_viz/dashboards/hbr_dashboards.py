from mplsoccer.pitch import Line2D
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from fb_viz.helpers.fonts import font_normal, font_mono, font_bold, font_italic
from fb_viz.helpers.mclachbot_helpers import sportsdb_image_grabber
from matplotlib.patches import FancyBboxPatch
from footmav.data_definitions.whoscored.constants import EventType
from mplsoccer import add_image
from abc import ABC, abstractmethod
from fb_viz.helpers.mclachbot_helpers import get_twitter_image, get_insta_image
from fb_viz.helpers import aggregators


class HorizontalBarRanking(ABC):
    def __init__(self, conn, facecolor="#333333", primary_text_color="ivory", secondary_text_color="grey") -> None:
        self._connection = conn
        self._facecolor = facecolor
        self._primary_text_color = primary_text_color
        self._secondary_text_color = secondary_text_color

    @staticmethod
    def name_format(name):
        name = name.split(" ")
        if len(name) == 1:
            return name[0].title()
        if len(name) == 2:
            return name[0][0].title() + ". " + name[1].title()
        else:
            return "".join([n[0].title() for n in name])

    @staticmethod
    def format_position(position):
        if position == "LB" or position == "RB":
            return "FB"
        if position in ["CDM", "CAM"] or (len(position) == 3 and position[0] in ["L", "R"]):
            return position[1:]
        if position == "RCDM" or position == "LCDM":
            return "DM"
        if position == "RCAM" or position == "LCAM":
            return "AM"
        return position

    @staticmethod
    def get_position_color(position):
        if position in ["GK"]:
            return "purple"
        if position in ["CB", "FB", "WB"]:
            return "blue"
        if position in ["LM", "RM", "CM", "DM", "AM"]:
            return "darkorange"
        else:
            return "red"

    def get_data(self, match_id: int) -> dict:
        query = f"""
        SELECT W.*,
        E.shirt_number, E.formation, E.position, E.pass_receiver, E.pass_receiver_shirt_number, E.pass_receiver_position,
        G.game_state,
        P.passtypes,
        X.value as xT,
        XGT.xg AS xG,
        TEAM.decorated_name,
        LEAGUE.decorated_name as league_decorated_name,
        META.home_score, META.away_score
        FROM whoscored W 
        LEFT JOIN derived.whoscored_extra_event_info E
        ON W.id=E.id
        LEFT JOIN derived.whoscored_game_state G
        ON W.id=G.id
        LEFT JOIN derived.whoscored_pass_types P
        ON W.id=P.id
        LEFT JOIN derived.whoscored_xthreat X
        on W.id=X.id
        LEFT JOIN derived.whoscored_shot_data XGT
        on W.id=XGT.id
        
        LEFT JOIN football_data.mclachbot_teams TEAM ON W.team = TEAM.ws_team_name
        LEFT JOIN football_data.mclachbot_leagues LEAGUE ON W.competition = LEAGUE.ws_league_name
        LEFT JOIN football_data.whoscored_meta META ON W.matchId = META.matchId
        WHERE W.matchId={match_id}
        """
        query2 = f"""
        SELECT eventId,minute,second,x,y,qualifiers,period,event_type,outcomeType,endX,endY,matchId,season,competition,player_name,match_seconds,team,opponent,is_home_team,sub_id, carryId FROM derived.whoscored_implied_carries 
        WHERE matchId={match_id}
        """

        data1 = self._connection.wsquery(query)
        data1["sub_id"] = 1
        data2 = self._connection.wsquery(query2)

        data = pd.concat([data1, data2])
        data["sub_id"] = data["sub_id"].fillna(1)
        data = data.sort_values(["period", "minute", "second", "eventId", "sub_id"])
        return data

    @abstractmethod
    def _prep_dataframe(self, data) -> pd.DataFrame:
        pass

    def draw(self, data):
        prepped_df = self._prep_dataframe(data)
        fig = Figure(
            figsize=(7, 10),
            dpi=100,
            facecolor=self._facecolor,
            edgecolor=self._primary_text_color,
            constrained_layout=True,
        )
        axes = fig.subplot_mosaic(
            mosaic=[["header"], ["main"], ["footer"]], gridspec_kw=dict(height_ratios=[0.1, 0.8, 0.1])
        )
        self.draw_main(axes["main"], prepped_df)
        self._draw_top(data, fig, axes["header"])
        self._draw_bottom(data, fig, axes["footer"])
        add_image(get_insta_image(), fig, left=0.915, bottom=0.01, width=0.03, height=0.03)
        add_image(get_twitter_image(), fig, left=0.95, bottom=0.01, width=0.03, height=0.03)

        return fig

    def _draw_bottom(self, data, fig, ax):
        ax.set_facecolor(self._facecolor)
        ax.set_axis_off()
        ax.add_patch(
            FancyBboxPatch(
                (-0.05, 0),
                1.1,
                1,
                boxstyle="round,rounding_size=0.02,pad=0.",
                facecolor=self._facecolor,
                edgecolor=self._primary_text_color,
                linewidth=2,
                clip_on=False,
                mutation_aspect=10,
            )
        )
        custom_lines = [Line2D([0], [0], color=c, lw=4) for c in self.BAR_COLORS] + [
            Line2D([0], [0], color=self.UNDERBAR_COLOR, lw=2)
        ]
        ax.legend(
            custom_lines,
            [c.replace("_", " ").title() for c in self.BAR_COLUMNS] + [self.UNDERBAR_COLUMN.replace("_", " ").title()],
            facecolor=self._facecolor,
            edgecolor=self._facecolor,
            labelcolor=self._primary_text_color,
            loc="center left",
        )
        ax.text(
            0.95,
            0.2,
            "@mclachbot",
            va="center",
            ha="right",
            size=10,
            color=self._secondary_text_color,
            fontproperties=font_italic.prop,
        )
        if self.EXPLAIN_TEXT:
            ax.text(
                1.04,
                0.95,
                self.EXPLAIN_TEXT,
                va="top",
                ha="right",
                size=10,
                color=self._primary_text_color,
                fontproperties=font_normal.prop,
            )

    def _format_total(self, n: float):
        return f"{n:.0f}"

    def _draw_top(self, data, fig, ax):
        ax.set_facecolor(self._facecolor)
        ax.set_axis_off()
        date = data["match_date"].iloc[0]
        home_score = data["home_score"].iloc[0]
        away_score = data["away_score"].iloc[0]
        home_team = data.loc[
            (data["is_home_team"] == True) & (data["event_type"] != EventType.Carry), "decorated_name"
        ].iloc[0]
        away_team = data.loc[
            (data["is_home_team"] == False) & (data["event_type"] != EventType.Carry), "decorated_name"
        ].iloc[0]
        league = data["competition"].iloc[0]
        ax.add_patch(
            FancyBboxPatch(
                (-0.05, 0),
                1.1,
                1,
                boxstyle="round,rounding_size=0.02,pad=0.",
                facecolor=self._facecolor,
                edgecolor=self._primary_text_color,
                linewidth=2,
                clip_on=False,
                mutation_aspect=10,
            )
        )
        ax.text(
            0.5,
            0.80,
            f'{date.strftime("%A, %B %d %Y")}',
            color=self._secondary_text_color,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        ax.text(
            0.5,
            0.5,
            f"{home_score:.0f} - {away_score:.0f}",
            color=self._primary_text_color,
            va="center",
            ha="center",
            fontproperties=font_mono.prop,
            fontsize=20,
        )
        ax.text(
            0.15,
            0.5,
            f"{home_team}",
            color=self._primary_text_color,
            va="center",
            ha="left",
            fontproperties=font_normal.prop,
            fontsize=18,
        )
        ax.text(
            0.85,
            0.5,
            f"{away_team}",
            color=self._primary_text_color,
            va="center",
            ha="right",
            fontproperties=font_normal.prop,
            fontsize=18,
        )
        ax.text(
            0.5,
            0.20,
            f"{data['league_decorated_name'].iloc[0]}",
            color=self._secondary_text_color,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        home_img = sportsdb_image_grabber(data.loc[data["is_home_team"] == True, "team"].iloc[0], league)
        away_img = sportsdb_image_grabber(data.loc[data["is_home_team"] == False, "team"].iloc[0], league)
        ax.text(
            0.5,
            -0.3,
            self.TITLE,
            color=self._primary_text_color,
            va="center",
            ha="center",
            fontproperties=font_bold.prop,
            fontsize=16,
        )
        ax2 = fig.add_axes([0.05, 0.90, 0.09, 0.09])
        ax2.imshow(home_img)
        ax2.axis("off")
        ax3 = fig.add_axes([0.86, 0.90, 0.09, 0.09])
        ax3.imshow(away_img)
        ax3.axis("off")

    def draw_main(self, ax: Axes, prepped_df):
        max_value = prepped_df[self.TOTAL_COLUMN].max()
        max_width = max_value * 2
        if self.UNDERBAR_COLUMN:
            max_value_secondary = prepped_df[self.UNDERBAR_COLUMN].max()

            max_width_secondary = max_value_secondary * 2

        ax.set_facecolor(self._facecolor)
        ax.set_axis_off()
        home_team_df = prepped_df.loc[prepped_df["is_home_team"] == 1]
        away_team_df = prepped_df.loc[prepped_df["is_home_team"] == 0]
        topx = ax.twiny()
        topx.set_axis_off()

        for i, _df in enumerate([home_team_df, away_team_df]):
            if i == 0:
                m = -1
            else:
                m = 1
            _df = _df.sort_values(self.TOTAL_COLUMN, ascending=False)
            _df["idx"] = range(0, len(_df))
            _df["position"] = _df["position"].apply(lambda x: self.format_position(x))
            _df["pos_color"] = _df["position"].apply(lambda x: self.get_position_color(x))
            for i, (col, color) in enumerate(zip(self.BAR_COLUMNS, self.BAR_COLORS)):
                if i == 0:
                    ax.barh(
                        -1 * _df["idx"], m * _df[col], left=m * 0.02 * max_width, color=color, height=0.7, linewidth=0
                    )
                else:
                    ax.barh(
                        -1 * _df["idx"],
                        m * _df[col],
                        left=m * _df[self.BAR_COLUMNS[:i]].sum(axis=1) + m * 0.02 * max_width,
                        color=color,
                        height=0.7,
                        linewidth=0,
                    )
            ax.scatter(
                [m * max_width * 0.955] * len(_df),
                -1 * _df["idx"],
                s=400,
                linewidths=1,
                c=_df["pos_color"],
                edgecolor=self._primary_text_color,
            )
            for _, r in _df.iterrows():
                ax.text(
                    m * max_width * 0.955,
                    -1 * r["idx"],
                    r["position"],
                    color=self._primary_text_color,
                    ha="center",
                    va="center",
                    fontsize=10,
                    fontproperties=font_normal.prop,
                )
                ax.text(
                    m * (max_width * 0.90),
                    -1 * r["idx"],
                    self.name_format(r["player_name"]),
                    color=self._primary_text_color,
                    ha="right" if m == 1 else "left",
                    va="center",
                    fontsize=12,
                    fontproperties=font_normal.prop,
                )
                ax.text(
                    m * r[self.TOTAL_COLUMN] + m * 0.04 * max_width,
                    -1 * r["idx"],
                    self._format_total(r[self.TOTAL_COLUMN]),
                    color="black",
                    ha="left" if m == 1 else "right",
                    va="center",
                    fontsize=10,
                    fontproperties=font_normal.prop,
                    bbox=dict(facecolor="ivory", alpha=1, edgecolor="black", boxstyle="round,pad=0.2"),
                )
            topx.barh(
                -1 * _df["idx"] - 0.35,
                m * _df[self.UNDERBAR_COLUMN],
                color=self.UNDERBAR_COLOR,
                left=m * 0.02 * max_width_secondary,
                height=-0.1,
                zorder=2,
                align="edge",
            )

        ax.set_xbound(-max_width, max_width)
        topx.set_xbound(-max_width_secondary, max_width_secondary)
        ax.set_ybound(min(-11, max(home_team_df.shape[0], away_team_df.shape[0])) - 0.5, 0.5)
        return ax


class HBRProgressiveDistance(HorizontalBarRanking):
    def _prep_dataframe(self, data):
        aggregators.progressive_carry_distance(data)
        aggregators.progressive_pass_distance(data)
        aggregators.touches(data)

        grouped_progressives = (
            data.groupby(["player_name", "team", "is_home_team"])
            .agg(
                {
                    "progressive_carry_distance": "sum",
                    "progressive_pass_distance": "sum",
                    "touches_attempted": "sum",
                    "position": "first",
                }
            )
            .reset_index()
        )
        grouped_progressives["progressive_distance"] = (
            grouped_progressives["progressive_carry_distance"] + grouped_progressives["progressive_pass_distance"]
        )
        grouped_progressives["progressive_distance_per_touch"] = (
            grouped_progressives["progressive_distance"]
            / grouped_progressives["touches_attempted"]
            * (grouped_progressives["touches_attempted"] > 5)
        )
        grouped_progressives = grouped_progressives.loc[grouped_progressives["progressive_distance"] > 30]
        return grouped_progressives

    TOTAL_COLUMN = "progressive_distance"
    BAR_COLUMNS = ["progressive_pass_distance", "progressive_carry_distance"]
    UNDERBAR_COLUMN = "progressive_distance_per_touch"

    TITLE = "Ball Progression Distances"

    BAR_COLORS = ["#e66100", "#5d3a9b"]

    UNDERBAR_COLOR = "lightblue"
    EXPLAIN_TEXT = (
        "Progressive Distance Per Touch\nis on a different scale.  It's useful\nto compare players to each other only"
    )


class HBRExpectedGoalContributions(HorizontalBarRanking):
    def _prep_dataframe(self, data):
        aggregators.xa(data)
        aggregators.npxg(data)
        aggregators.touches(data)

        grouped = (
            data.groupby(["player_name", "team", "is_home_team"])
            .agg(
                {
                    "xa": "sum",
                    "npxg_attempted": "sum",
                    "touches_attempted": "sum",
                    "position": "first",
                }
            )
            .rename(columns={"xa": "expected_assists", "npxg_attempted": "non_penalty_expected_goals"})
            .reset_index()
        )
        grouped["expected_goal_contributions"] = grouped["expected_assists"] + grouped["non_penalty_expected_goals"]
        grouped["expected_goal_contributions_per_touch"] = (
            grouped["expected_goal_contributions"] / grouped["touches_attempted"] * (grouped["touches_attempted"] > 5)
        )
        grouped = grouped.loc[grouped["expected_goal_contributions"] > 0]
        return grouped

    TOTAL_COLUMN = "expected_goal_contributions"
    BAR_COLUMNS = ["non_penalty_expected_goals", "expected_assists"]
    UNDERBAR_COLUMN = "expected_goal_contributions_per_touch"

    TITLE = "Expected Goal Contributions"

    BAR_COLORS = ["#574B60", "#EF767A"]

    UNDERBAR_COLOR = "lightblue"
    EXPLAIN_TEXT = "Expected Goal Contributions Per Touch\nis on a different scale.  It's useful\nto compare players to each other only"

    def _format_total(self, n: float):
        return f"{n:.2f}"


class HBRChanceCreation(HorizontalBarRanking):
    def _prep_dataframe(self, data):
        aggregators.open_play_passes_completed_into_the_box(data)
        aggregators.carries_into_the_box(data)
        aggregators.crosses_completed_into_the_box(data)
        aggregators.touches(data)

        grouped = (
            data.groupby(["player_name", "team", "is_home_team"])
            .agg(
                {
                    "crosses_completed_into_the_box": "sum",
                    "open_play_passes_completed_into_the_box": "sum",
                    "carries_into_the_box": "sum",
                    "touches_attempted": "sum",
                    "position": "first",
                }
            )
            .reset_index()
        )
        grouped["successful_actions_into_box"] = (
            grouped["crosses_completed_into_the_box"]
            + grouped["open_play_passes_completed_into_the_box"]
            + grouped["carries_into_the_box"]
        )
        grouped["successful_deliveries_into_penalty_box"] = (
            grouped["successful_actions_into_box"] / grouped["touches_attempted"] * (grouped["touches_attempted"] > 5)
        )
        grouped = grouped.loc[grouped["successful_actions_into_box"] > 0]
        return grouped

    TOTAL_COLUMN = "successful_actions_into_box"
    BAR_COLUMNS = ["crosses_completed_into_the_box", "open_play_passes_completed_into_the_box", "carries_into_the_box"]
    UNDERBAR_COLUMN = "successful_deliveries_into_penalty_box"

    TITLE = "Successful Deliveries Into Penalty Box"

    BAR_COLORS = ["#DCB8CB", "#3A7D44", "#181D27"]

    UNDERBAR_COLOR = "lightblue"
    EXPLAIN_TEXT = (
        "Expected Deliveries Per Touch\nis on a different scale.  It's useful\nto compare players to each other only"
    )
