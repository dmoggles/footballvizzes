from typing import Tuple
from footmav.event_aggregation import aggregators as agg
from footmav.event_aggregation.event_aggregator_processor import event_aggregator
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch
from fb_viz.helpers.fonts import font_bold, font_normal, font_italic, font_mono
from fb_viz.helpers.mclachbot_helpers import sportsdb_image_grabber


@event_aggregator
def npxgot(dataframe):
    return agg.npxg(dataframe) * agg.shots_on_target(dataframe).astype(int)


def agg_minutes(dataframe):
    seconds_dict = {}
    home = dataframe.loc[dataframe["is_home_team"] == True, "team"].iloc[0]
    away = dataframe.loc[dataframe["is_home_team"] == False, "team"].iloc[0]

    for i, g in dataframe.groupby("possession_number"):
        team = g["team"].iloc[0]
        seconds = g["match_seconds"].max() - g["match_seconds"].min()
        if team in seconds_dict:
            seconds_dict[team] += seconds
        else:
            seconds_dict[team] = seconds
    return (
        seconds_dict[home] / sum(seconds_dict.values()) * 100,
        seconds_dict[away] / sum(seconds_dict.values()) * 100,
    )


def stat_wrapper(f):
    def wrapper(dataframe, *args, **kwargs):
        data = dataframe.copy()
        data[f.col_name] = f(data, *args, **kwargs)
        group = data.groupby("team").agg({f.col_name: "sum"}).to_dict()[f.col_name]
        home = data.loc[data["is_home_team"] == True, "team"].iloc[0]
        away = data.loc[data["is_home_team"] == False, "team"].iloc[0]
        return (group[home], group[away])

    return wrapper


def stat_wrapper_success(f):
    def wrapper(dataframe, *args, **kwargs):
        data = dataframe.copy()
        data[f.col_name] = f.success(data, *args, **kwargs)
        group = data.groupby("team").agg({f.col_name: "sum"}).to_dict()[f.col_name]
        home = data.loc[data["is_home_team"] == True, "team"].iloc[0]
        away = data.loc[data["is_home_team"] == False, "team"].iloc[0]
        return (group[home], group[away])

    return wrapper


def stat_wrapper_success_pct(f):
    def wrapper(dataframe, *args, **kwargs):
        data = dataframe.copy()
        data[f"{f.col_name}_success"] = f.success(data, *args, **kwargs)
        data[f.col_name] = f(data, *args, **kwargs)
        group = data.groupby("team").agg(
            {f.col_name: "sum", f"{f.col_name}_success": "sum"}
        )
        group = (group[f"{f.col_name}_success"] / group[f.col_name] * 100).to_dict()
        home = data.loc[data["is_home_team"] == True, "team"].iloc[0]
        away = data.loc[data["is_home_team"] == False, "team"].iloc[0]
        return (group[home], group[away])

    return wrapper


def tackle_pct_success(dataframe):
    tackles = stat_wrapper(agg.tackles)(dataframe)
    tackles_won = stat_wrapper(agg.tackles_successful)(dataframe)
    return (tackles_won[0] / tackles[0] * 100, tackles_won[1] / tackles[1] * 100)


class MatchStat:
    def __init__(
        self,
        name,
        data_generator_f,
        parenthesis=None,
        parenthesis_data_generator_f=None,
        precision=0,
        main_pct=False,
        parenthesis_pct=False,
        reverse_success=False,
    ):
        self.name = name
        self.parenthesis = parenthesis
        self.data_generator_f = data_generator_f
        self.parenthesis_data_generator_f = parenthesis_data_generator_f
        self.precision = precision
        self.parenthesis_pct = parenthesis_pct
        self.main_pct = main_pct
        self.reverse_success = reverse_success

    def __str__(self):
        if self.parenthesis:
            return f"{self.name} ({self.parenthesis})"
        else:
            return f"{self.name}"

    def format(self, value):
        if self.precision == 0:
            return f"{value}"
        else:
            return f"{value:.{self.precision}f}"

    def generate(self, data):
        if self.precision == 0:
            return tuple([int(round(v)) for v in self.data_generator_f(data)])
        else:
            return tuple(
                [round(v, self.precision) for v in self.data_generator_f(data)]
            )

    def generate_parenthesis(self, data):
        if self.precision == 0:
            return tuple(
                [int(round(v)) for v in self.parenthesis_data_generator_f(data)]
            )
        else:
            return tuple(
                [
                    round(v, self.precision)
                    for v in self.parenthesis_data_generator_f(data)
                ]
            )


stats = [
    MatchStat(
        "Shots", stat_wrapper(agg.shots), "on target", stat_wrapper(agg.shots_on_target)
    ),
    MatchStat("Big Chances", stat_wrapper(agg.big_chances)),
    MatchStat("NPxG", stat_wrapper(agg.npxg), precision=2),
    MatchStat("NPxG On Target", stat_wrapper(npxgot), precision=2),
    MatchStat("Pct Possession", agg_minutes, main_pct=True),
    MatchStat(
        "Passes",
        stat_wrapper(agg.passes),
        "% complete",
        stat_wrapper_success_pct(agg.passes),
        parenthesis_pct=True,
    ),
    MatchStat(
        "Prog. Passes",
        stat_wrapper(agg.progressive_passes),
        "% complete",
        stat_wrapper_success_pct(agg.progressive_passes),
        parenthesis_pct=True,
    ),
    MatchStat(
        "Tackles",
        stat_wrapper(agg.tackles),
        "% won",
        tackle_pct_success,
        parenthesis_pct=True,
    ),
    MatchStat("Interceptions", stat_wrapper(agg.interceptions)),
    MatchStat("Ground Duels Won", stat_wrapper(agg.ground_duels_won)),
    MatchStat("Aerial Duels Won", stat_wrapper_success(agg.aerials)),
    MatchStat("Fouls", stat_wrapper(agg.fouls_conceded), reverse_success=True),
    MatchStat("Yellow Cards", stat_wrapper(agg.yellow_cards), reverse_success=True),
    MatchStat("Red Cards", stat_wrapper(agg.red_cards), reverse_success=True),
    MatchStat("Keeper Saves", stat_wrapper(agg.keeper_saves)),
]


class MatchSummaryDashboard:
    def __init__(
        self,
        connection,
        background_color="#000011",
        primary_text_color="ivory",
        secondary_text_color="gray",
        success_color="green",
        failure_color="red",
        neutral_color="yellow",
    ):
        self.background_color = background_color
        self.primary_text_color = primary_text_color
        self.secondary_text_color = secondary_text_color
        self.success_color = success_color
        self.failure_color = failure_color
        self.neutral_color = neutral_color
        self._connection = connection

    def _prep_fig(self, figsize=(8, 8)) -> Tuple[Figure, Axes]:
        fig = Figure(figsize=figsize, facecolor=self.background_color)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_facecolor(self.background_color)
        ax.set_axis_off()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return fig, ax

    def _draw_top(self, data, fig, ax):
        date = data["match_date"].iloc[0]
        home_score = data["home_score"].iloc[0]
        away_score = data["away_score"].iloc[0]
        home_team = data.loc[data["is_home_team"] == True, "decorated_name"].iloc[0]
        away_team = data.loc[data["is_home_team"] == False, "decorated_name"].iloc[0]
        league = data["competition"].iloc[0]
        ax.add_patch(
            FancyBboxPatch(
                (0.05, 0.89),
                0.90,
                0.09,
                boxstyle="round,pad=0.01",
                facecolor=self.background_color,
                edgecolor=self.primary_text_color,
                linewidth=2,
            )
        )
        ax.text(
            0.5,
            0.98,
            f'{date.strftime("%A, %B %d %Y")}',
            color=self.secondary_text_color,
            va="top",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        ax.text(
            0.5,
            0.95,
            f"{home_score} - {away_score}",
            color=self.primary_text_color,
            va="top",
            ha="center",
            fontproperties=font_mono.prop,
            fontsize=20,
        )
        ax.text(
            0.15,
            0.95,
            f"{home_team}",
            color=self.primary_text_color,
            va="top",
            ha="left",
            fontproperties=font_normal.prop,
            fontsize=18,
        )
        ax.text(
            0.85,
            0.95,
            f"{away_team}",
            color=self.primary_text_color,
            va="top",
            ha="right",
            fontproperties=font_normal.prop,
            fontsize=18,
        )
        ax.text(
            0.5,
            0.91,
            f"{data['league_decorated_name'].iloc[0]}",
            color=self.secondary_text_color,
            va="top",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        home_img = sportsdb_image_grabber(
            data.loc[data["is_home_team"] == True, "team"].iloc[0], league
        )
        away_img = sportsdb_image_grabber(
            data.loc[data["is_home_team"] == False, "team"].iloc[0], league
        )
        ax2 = fig.add_axes([0.05, 0.89, 0.09, 0.09])
        ax2.imshow(home_img)
        ax2.axis("off")
        ax3 = fig.add_axes([0.86, 0.89, 0.09, 0.09])
        ax3.imshow(away_img)
        ax3.axis("off")

    def draw_data(self, data, ax):
        for i, match_stat in enumerate(stats):
            if match_stat.parenthesis is not None:

                ax.text(
                    0.5,
                    0.83 - i * 0.05,
                    f"{match_stat}",
                    color=self.primary_text_color,
                    va="center",
                    ha="center",
                    fontproperties=font_bold.prop,
                    fontsize=18,
                )
                home_stat, away_stat = match_stat.generate(data)
                (
                    home_parenthesis_stat,
                    away_parenthesis_stat,
                ) = match_stat.generate_parenthesis(data)
                if (home_stat > away_stat and not match_stat.reverse_success) or (
                    (home_stat < away_stat) and match_stat.reverse_success
                ):
                    home_color = self.success_color
                    away_color = self.failure_color
                elif (home_stat < away_stat and not match_stat.reverse_success) or (
                    (home_stat > away_stat) and match_stat.reverse_success
                ):
                    home_color = self.failure_color
                    away_color = self.success_color
                else:
                    home_color = self.neutral_color
                    away_color = self.neutral_color

                ax.text(
                    0.15,
                    0.83 - i * 0.05,
                    f"{match_stat.format(home_stat)}{'%' if match_stat.main_pct else ''} ({match_stat.format(home_parenthesis_stat)}{'%' if match_stat.parenthesis_pct else ''})",
                    color=home_color,
                    va="center",
                    ha="left",
                    fontproperties=font_normal.prop,
                    fontsize=18,
                )
                ax.text(
                    0.85,
                    0.83 - i * 0.05,
                    f"{match_stat.format(away_stat)}{'%' if match_stat.main_pct else ''} ({match_stat.format(away_parenthesis_stat)}{'%' if match_stat.parenthesis_pct else ''})",
                    color=away_color,
                    va="center",
                    ha="right",
                    fontproperties=font_normal.prop,
                    fontsize=18,
                )

            else:
                ax.text(
                    0.5,
                    0.83 - i * 0.05,
                    f"{match_stat.name}",
                    color=self.primary_text_color,
                    va="center",
                    ha="center",
                    fontproperties=font_bold.prop,
                    fontsize=18,
                )
                home_stat, away_stat = match_stat.generate(data)
                if (home_stat > away_stat and not match_stat.reverse_success) or (
                    (home_stat < away_stat) and match_stat.reverse_success
                ):
                    home_color = self.success_color
                    away_color = self.failure_color
                elif (home_stat < away_stat and not match_stat.reverse_success) or (
                    (home_stat > away_stat) and match_stat.reverse_success
                ):
                    home_color = self.failure_color
                    away_color = self.success_color
                else:
                    home_color = self.neutral_color
                    away_color = self.neutral_color
                ax.text(
                    0.15,
                    0.83 - i * 0.05,
                    f"{match_stat.format(home_stat)}{'%' if match_stat.main_pct else ''}",
                    color=home_color,
                    va="center",
                    ha="left",
                    fontproperties=font_normal.prop,
                    fontsize=18,
                )
                ax.text(
                    0.85,
                    0.83 - i * 0.05,
                    f"{match_stat.format(away_stat)}{'%' if match_stat.main_pct else ''}",
                    color=away_color,
                    va="center",
                    ha="right",
                    fontproperties=font_normal.prop,
                    fontsize=18,
                )
            if i < (len(stats) - 1):

                ax.hlines(
                    [0.805 - i * 0.05],
                    0.1,
                    0.9,
                    color=self.primary_text_color,
                    linewidth=1,
                    linestyles="dotted",
                    alpha=0.5,
                )

    def _draw_footer(self, fig, ax):
        ax.add_patch(
            FancyBboxPatch(
                (0.05, 0.05),
                0.90,
                0.02,
                boxstyle="round,pad=0.01",
                facecolor=self.background_color,
                edgecolor=self.primary_text_color,
                linewidth=2,
            )
        )

        ax.text(
            0.5,
            0.07,
            f"Data by @mclachbot",
            color=self.secondary_text_color,
            va="top",
            ha="center",
            fontproperties=font_italic.prop,
            fontsize=10,
        )

    def draw(self, data):
        fig, ax = self._prep_fig()
        self._draw_top(data, fig, ax)
        self.draw_data(data, ax)
        self._draw_footer(fig, ax)
        return fig, ax

    def get_data(self, match_id):
        query = f"""
            SELECT 
            W.*,
            XG.xg as xG,
            INFO.*,
            TEAM.decorated_name,
            LEAGUE.decorated_name as league_decorated_name,
            META.home_score, META.away_score,
            SEQUENCE.possession_number
            FROM football_data.whoscored W 
            LEFT JOIN derived.whoscored_shot_data XG
            ON W.id = XG.id
            LEFT JOIN derived.whoscored_extra_event_info INFO
            ON W.id = INFO.id
            LEFT JOIN football_data.mclachbot_teams TEAM ON W.team = TEAM.ws_team_name
            LEFT JOIN football_data.mclachbot_leagues LEAGUE ON W.competition = LEAGUE.ws_league_name
            LEFT JOIN football_data.whoscored_meta META ON W.matchId = META.matchId
            LEFT JOIN derived.whoscored_possession_sequence SEQUENCE ON W.id = SEQUENCE.id
            WHERE W.matchId = {match_id}
        """
        return self._connection.wsquery(query)
