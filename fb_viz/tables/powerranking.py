from typing import Callable, Tuple
from dbconnect.connector import Connection
import pandas as pd
import numpy as np
from fb_viz.helpers.dataframe_style_helpers import (
    background_gradient_from_another_column,
)
import math


class PowerRank:
    LEAGUE_COLOURS = {
        "Premier League": ("red", "white"),
        "La Liga": ("yellow", "red"),
        "Ligue 1": ("blue", "white"),
        "Bundesliga": ("black", "red"),
        "Serie A": ("green", "white"),
    }
    KEEPING_RANGE = (-1500, 3300)
    DEFENDING_RANGE = (-500, 2500)
    FINISHING_RANGE = (0, 1700)
    PROGRESSING_RANGE = (-500, 6000)
    PROVIDING_RANGE = (0, 2000)
    TOTAL_RANGE = (-1500, 7200)

    def __init__(self):
        self.connection = Connection("M0neyMa$e")

    def team_data(self) -> pd.DataFrame:
        team_query = """
            SELECT team_name, decorated_name FROM mclachbot_teams
            WHERE gender='m'
            """
        return self.connection.query(team_query)

    def test(self, season: int) -> pd.DataFrame:
        sql = f"""
        SELECT * FROM derived.fbref_power_ranking WHERE season = {season}
        """
        return self.connection.query(sql)

    def get_data_last_n_games_player(self, n_games: int, season: int) -> pd.DataFrame:
        sql = f"""
            WITH match_index AS (
                SELECT fb.*, ROW_NUMBER() OVER (PARTITION BY player,squad ORDER BY date DESC) AS rn
                FROM derived.fbref_power_ranking AS fb WHERE SEASON={season}
            ) SELECT * FROM match_index WHERE rn <={n_games+1};

        """
        data = self.connection.query(sql)
        team_names = self.team_data()
        data = pd.merge(
            data, team_names, how="left", left_on="squad", right_on="team_name"
        )
        data["opponent"] = data["opponent"].map(
            team_names.set_index("team_name")["decorated_name"]
        )

        domestic_leagues = (
            data.groupby("squad")
            .agg(
                {
                    "comp": lambda x: ",".join(x.unique())
                    .replace("Champions League", "")
                    .replace("Europa League", "")
                    .strip(",")
                }
            )
            .reset_index()
            .rename(columns={"comp": "domestic league"})
        )
        data = pd.merge(left=data, right=domestic_leagues, on="squad", how="left")
        data = data.loc[data["domestic league"] != ""]
        return data

    def get_data_last_n_games(self, n_games: int, season: int) -> pd.DataFrame:
        sql = f"""

            WITH main_match_key AS(
                SELECT *,CONCAT(squad, ',', match_id) as match_key
                FROM derived.fbref_power_ranking
                WHERE season = {season}
                    AND comp IN ('Premier League','Ligue 1','La Liga','Bundesliga','Serie A','Champions League','Europa League')
            )
            SELECT * FROM main_match_key WHERE match_key IN (
                SELECT CONCAT(squad,',', match_id) as match_key FROM(
                WITH TOPTEN AS (
                    SELECT *, ROW_NUMBER() 
                    over (
                        PARTITION BY squad
                        order by date DESC
                    ) AS RowNo 
                    FROM (
                        SELECT DISTINCT(match_id), date, squad 
                        FROM derived.fbref_power_ranking 
                        WHERE season = {season}
                        AND comp IN ('Premier League','Ligue 1','La Liga','Bundesliga','Serie A','Champions League','Europa League')
                    ) AS all_data
                )
                SELECT * FROM TOPTEN WHERE RowNo <= {n_games+1}
                ) AS match_ids
            ) ORDER BY match_key
            """

        data = self.connection.query(sql)
        team_names = self.team_data()
        data = pd.merge(
            data, team_names, how="left", left_on="squad", right_on="team_name"
        )
        data["opponent"] = data["opponent"].map(
            team_names.set_index("team_name")["decorated_name"]
        )

        domestic_leagues = (
            data.groupby("squad")
            .agg(
                {
                    "comp": lambda x: ",".join(x.unique())
                    .replace("Champions League", "")
                    .replace("Europa League", "")
                    .strip(",")
                }
            )
            .reset_index()
            .rename(columns={"comp": "domestic league"})
        )
        data = pd.merge(left=data, right=domestic_leagues, on="squad", how="left")
        data = data.loc[data["domestic league"] != ""]
        return data

    def _prev_for_teams(self, data) -> Tuple[pd.DataFrame, pd.DataFrame]:

        first_match = (
            data.sort_values("date", ascending=True)
            .groupby(["squad"])
            .apply(lambda x: x["match_id"].unique()[0])
        )
        last_match = (
            data.sort_values("date", ascending=True)
            .groupby(["squad"])
            .apply(lambda x: x["match_id"].unique()[-1])
        )
        first_match.name = "first_match"
        last_match.name = "last_match"
        data = pd.merge(data, first_match, on="squad", how="left")
        data = pd.merge(data, last_match, on="squad", how="left")
        prev_data = data.loc[data["match_id"] != data["last_match"]]
        data = data.loc[data["match_id"] != data["first_match"]]
        return data, prev_data

    def _prev_for_players(self, data) -> Tuple[pd.DataFrame, pd.DataFrame]:

        first_match = (
            data.sort_values("date", ascending=True)
            .groupby(["squad", "player"])
            .apply(lambda x: x["match_id"].unique()[0])
        )
        last_match = (
            data.sort_values("date", ascending=True)
            .groupby(["squad", "player"])
            .apply(lambda x: x["match_id"].unique()[-1])
        )
        first_match.name = "first_match"
        last_match.name = "last_match"
        data = pd.merge(data, first_match, on=["squad", "player"], how="left")
        data = pd.merge(data, last_match, on=["squad", "player"], how="left")
        prev_data = data.loc[data["match_id"] != data["last_match"]]
        data = data.loc[data["match_id"] != data["first_match"]]
        return data, prev_data

    def create_rank(self, data: pd.DataFrame, metric_to_use: str) -> pd.DataFrame:
        return self._create_rank(data, metric_to_use, self._prev_for_teams)

    def create_player_rank(
        self, data: pd.DataFrame, metric_to_use: str
    ) -> pd.DataFrame:
        return self._create_rank(data, metric_to_use, self._prev_for_players)

    def _create_rank(
        self,
        data: pd.DataFrame,
        metric_to_use: str,
        prev_f: Callable[[pd.DataFrame], Tuple[pd.DataFrame, pd.DataFrame]],
    ) -> pd.DataFrame:
        data, prev_data = prev_f(data)
        data["squad"] = data["decorated_name"]
        prev_data["squad"] = prev_data["decorated_name"]
        aggregated = (
            data.groupby(["player", "domestic league", "squad"])
            .agg(
                {
                    "defending": "sum",
                    "finishing": "sum",
                    "progressing": "sum",
                    "providing": "sum",
                    "keeping": "sum",
                    "total": "sum",
                    "rank_position": "first",
                }
            )
            .reset_index()
        )
        prev_aggregated = (
            prev_data.groupby(["player", "domestic league", "squad"])
            .agg(
                {
                    "defending": "sum",
                    "finishing": "sum",
                    "progressing": "sum",
                    "providing": "sum",
                    "keeping": "sum",
                    "total": "sum",
                    "rank_position": "first",
                }
            )
            .reset_index()
        )
        for c in [
            "finishing",
            "defending",
            "progressing",
            "providing",
            "keeping",
            "total",
        ]:
            aggregated[f"{c}_r"] = aggregated[c].rank(pct=True, method="dense") * 100
        aggregated["is_keeper"] = aggregated["rank_position"] == "GK"
        aggregated = aggregated.drop(labels=["rank_position"], axis=1)
        aggregated["Percentile Rank (Overall)"] = (
            aggregated[metric_to_use].rank(pct=True) * 100
        )
        aggregated["Rank (Overall)"] = aggregated[metric_to_use].rank(ascending=False)
        prev_aggregated["Rank (Overall)"] = prev_aggregated[metric_to_use].rank(
            ascending=False
        )
        for i, g in aggregated.groupby("domestic league"):
            aggregated.loc[
                aggregated["domestic league"] == i, "Percentile Rank (League)"
            ] = (g[metric_to_use].rank(pct=True) * 100)

        for i, g in aggregated.groupby("squad"):
            aggregated.loc[aggregated["squad"] == i, "Rank (Team)"] = g[
                metric_to_use
            ].rank(ascending=False)
            aggregated.loc[aggregated["squad"] == i, "PCT Rank (Team)"] = (
                g[metric_to_use].rank(pct=True) * 100
            )
        aggregated["Rank Change"] = (
            pd.merge(
                left=aggregated,
                right=prev_aggregated,
                on=["player", "squad"],
                how="left",
            )["Rank (Overall)_y"]
            - pd.merge(
                left=aggregated,
                right=prev_aggregated,
                on=["player", "squad"],
                how="left",
            )["Rank (Overall)_x"]
        )

        return aggregated.sort_values(metric_to_use, ascending=False)

    @staticmethod
    def rank_formatter(v):
        if v < 10:
            return "color:grey;font-weight: bold"
        if v < 25:
            return "color:white;font-weight: bold"
        if v < 50:
            return "color:green;font-weight: bold"
        if v < 75:
            return "color:blue;font-weight: bold"
        if v < 95:
            return "color:purple;font-weight: bold"
        if v < 99:
            return "color:orange;font-weight: bold"
        return "color:pink;font-weight: bold"

    @staticmethod
    def rank_formatter_based_on_column(df):

        mask_10 = df["PCT Rank (Team)"] < 10
        mask_25 = df["PCT Rank (Team)"] < 25
        mask_50 = df["PCT Rank (Team)"] < 50
        mask_75 = df["PCT Rank (Team)"] < 75
        mask_95 = df["PCT Rank (Team)"] < 95
        mask_99 = df["PCT Rank (Team)"] < 99
        mask_100 = df["PCT Rank (Team)"] >= 99

        df1 = pd.DataFrame("", index=df.index, columns=df.columns)

        df1.loc[mask_100, "Rank (Team)"] = "color:pink;font-weight: bold"
        df1.loc[mask_99, "Rank (Team)"] = "color:orange;font-weight: bold"
        df1.loc[mask_95, "Rank (Team)"] = "color:purple;font-weight: bold"
        df1.loc[mask_75, "Rank (Team)"] = "color:blue;font-weight: bold"
        df1.loc[mask_50, "Rank (Team)"] = "color:green;font-weight: bold"
        df1.loc[mask_25, "Rank (Team)"] = "color:white;font-weight: bold"
        df1.loc[mask_10, "Rank (Team)"] = "color:grey;font-weight: bold"

        return df1

    @staticmethod
    def remove_irrelevant_columns(df):

        df1 = pd.DataFrame("", index=df.index, columns=df.columns)

        df1.loc[
            df["is_keeper"] == False, "keeping"
        ] = "color:#000011;background-color:#000011"
        df1.loc[
            df["is_keeper"] == True,
            ["providing", "progressing", "finishing", "defending"],
        ] = "color:#000011;background-color:#000011"

        return df1

    @classmethod
    def apply_league_colors(cls, df):
        df1 = pd.DataFrame("", index=df.index, columns=df.columns)
        for league, colors in cls.LEAGUE_COLOURS.items():
            df1.loc[
                df["domestic league"] == league, "domestic league"
            ] = f"color:{colors[1]};background-color:{colors[0]}"
        return df1

    @staticmethod
    def apply_rank_change_formatter(v):
        if v >= 100:
            return "↑↑↑"
        if v >= 50:
            return "↑↑"
        if v > 0:
            return "↑"
        if v <= -100:
            return "↓↓↓"
        if v <= -50:
            return "↓↓"
        if v < 0:
            return "↓"
        return "-"

    @staticmethod
    def apply_rank_change_formatter_style(df):
        df1 = pd.DataFrame("", index=df.index, columns=df.columns)
        df1.loc[
            df["Rank Change"] >= 100, "Rank Change"
        ] = "color:green;font-weight: bold;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] >= 50, "Rank Change"
        ] = "color:green;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] > 0, "Rank Change"
        ] = "color:lightgreen;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] <= -100, "Rank Change"
        ] = "color:red;font-weight: bold;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] <= -50, "Rank Change"
        ] = "color:red;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] < 0, "Rank Change"
        ] = "color:lightcoral;text-align: center;font-size: 150%"
        df1.loc[
            df["Rank Change"] == 0, "Rank Change"
        ] = "color:grey;text-align: center;font-size: 150%"
        return df1

    @classmethod
    def format(cls, styler, num_games, dataframe, heatmap_style):

        assert heatmap_style in [
            "absolute",
            "relative",
        ], 'heatmap_style must be either "absolute" or "relative"'
        styler.set_caption(
            f"Top 5 League Power Rankings - Based on Last {num_games} Games"
        )
        styler.set_properties(
            **{
                "background-color": "#000011",
                "color": "ivory",
                "border": "1px black solid !important",
            }
        )
        styler.format(precision=0)
        styler.format(lambda x: x.title(), subset=["player"])
        styler.apply(cls.rank_formatter_based_on_column, axis=None)

        styler.applymap(
            lambda x: cls.rank_formatter(x), subset=["Percentile Rank (Overall)"]
        )
        styler.applymap(
            lambda x: cls.rank_formatter(x), subset=["Percentile Rank (League)"]
        )
        styler.apply(cls.apply_league_colors, axis=None)
        styler.apply(cls.apply_rank_change_formatter_style, axis=None)
        styler.format(cls.apply_rank_change_formatter, subset=["Rank Change"])
        styler.hide()
        if heatmap_style == "absolute":
            styler.background_gradient(
                vmin=-cls.TOTAL_RANGE[0] * np.sqrt(num_games),
                vmax=cls.TOTAL_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["total"],
            )
            styler.background_gradient(
                vmin=-cls.PROVIDING_RANGE[0] * np.sqrt(num_games),
                vmax=cls.PROVIDING_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["providing"],
            )
            styler.background_gradient(
                vmin=-cls.PROGRESSING_RANGE[0] * np.sqrt(num_games),
                vmax=cls.PROGRESSING_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["progressing"],
            )
            styler.background_gradient(
                vmin=-cls.FINISHING_RANGE[0] * np.sqrt(num_games),
                vmax=cls.FINISHING_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["finishing"],
            )
            styler.background_gradient(
                vmin=-cls.DEFENDING_RANGE[0] * np.sqrt(num_games),
                vmax=cls.DEFENDING_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["defending"],
            )
            styler.background_gradient(
                vmin=-cls.KEEPING_RANGE[0] * np.sqrt(num_games),
                vmax=cls.KEEPING_RANGE[1] * np.sqrt(num_games),
                cmap="RdYlGn",
                subset=["keeping"],
            )
        else:
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["total"],
                column=dataframe["total_r"],
            )
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["providing"],
                column=dataframe["providing_r"],
            )
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["progressing"],
                column=dataframe["progressing_r"],
            )
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["finishing"],
                column=dataframe["finishing_r"],
            )
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["defending"],
                column=dataframe["defending_r"],
            )
            styler.apply(
                background_gradient_from_another_column,
                cmap="RdYlGn",
                subset=["keeping"],
                column=dataframe["keeping_r"],
            )

        styler.hide(
            ["PCT Rank (Team)", "is_keeper"]
            + [
                "finishing_r",
                "defending_r",
                "progressing_r",
                "providing_r",
                "keeping_r",
                "total_r",
                "Rank (Overall)",
            ],
            axis=1,
        )

        styler.format_index(lambda x: x.title(), axis=1)
        styler.apply(cls.remove_irrelevant_columns, axis=None)
        headers = {
            "selector": "th",
            "props": [
                ("background-color", "#000022"),
                ("color", "ivory"),
                ("font-weight", "bold"),
                ("border-bottom-style", "solid"),
                ("border-bottom-width", "1px"),
                ("border-bottom-color", "ivory"),
            ],
        }
        caption = {
            "selector": "caption",
            "props": [
                ("color", "ivory"),
                ("font-weight", "bold"),
                ("font-size", "150%"),
                ("background-color", "#000022"),
            ],
        }
        styler.set_table_styles([headers, caption], overwrite=False)
        return styler

    def format_for_team(self, data: pd.DataFrame, team: str, stat_type: str):
        curr_total_data, _ = self._prev_for_teams(data)
        curr_data = curr_total_data.loc[curr_total_data["decorated_name"] == team]
        n_games = len(curr_data)
        curr_data = curr_data.sort_values(by="date", ascending=True)
        curr_data["date"] = curr_data["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        table = curr_data.pivot(
            index="player",
            columns=["opponent", "comp", "date"],
            values=stat_type.lower(),
        )
        table["Total"] = table.sum(axis=1)

        table = table.sort_values("Total", ascending=False)
        table = table.reset_index().rename(columns={"player": "Player"})

        styler = table.style
        styler.set_properties(
            **{
                "background-color": "#000011",
                "color": "ivory",
                "border": "1px black solid !important",
            }
        )

        for c in table.columns[1:6]:

            styler.background_gradient(
                cmap="RdYlGn",
                subset=pd.IndexSlice[:, c],
                vmax=curr_total_data["total"].max(),
                vmin=curr_total_data["total"].min(),
            )
        styler.background_gradient(
            cmap="RdYlGn",
            subset=pd.IndexSlice[:, "Total"],
            vmax=curr_total_data.groupby("player").agg({"total": "sum"}).max(),
            vmin=curr_total_data.groupby("player").agg({"total": "sum"}).min(),
        )
        styler.format(lambda x: x.title(), subset=["Player"])
        headers = {
            "selector": "th",
            "props": [
                ("background-color", "#000022"),
                ("color", "ivory"),
                ("font-weight", "bold"),
                ("text-align", "center"),
            ],
        }
        styler.hide()
        styler.format(precision=0)
        for c in table.columns[1 : 1 + n_games]:
            styler.applymap(
                lambda x: "background-color: #333333" if math.isnan(x) else "",
                subset=pd.IndexSlice[:, c],
            )
            styler.format(
                lambda x: f"{x:.0f}" if not math.isnan(x) else "Did Not Play",
                subset=pd.IndexSlice[:, c],
            )

        styler.set_table_styles([headers], overwrite=False)
        return styler

    def format_for_player(self, data: pd.DataFrame, team: str, player: str):
        curr_total_data, _ = self._prev_for_teams(data)
        curr_data = curr_total_data.loc[
            (curr_total_data["decorated_name"] == team)
            & (curr_total_data["player"] == player.lower())
        ]
        n_games = len(curr_data)
        curr_data = curr_data.sort_values(by="date", ascending=True)
        curr_data["date"] = curr_data["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
        curr_data = curr_data[
            [
                "date",
                "comp",
                "opponent",
                "rank_position",
                "defending",
                "finishing",
                "progressing",
                "providing",
                "keeping",
                "total",
            ]
        ].rename(columns={"rank_position": "Position", "comp": "Competition"})
        totals = pd.DataFrame(
            {k: curr_data[k].sum() for k in curr_data.columns[4:]}, index=[0]
        )
        totals["date"] = "Total"
        curr_data = curr_data.append(totals, ignore_index=True).fillna("")
        styler = curr_data.style
        styler.set_properties(
            **{
                "background-color": "#000011",
                "color": "ivory",
                "border": "1px black solid !important",
            }
        )
        styler.format(precision=0)
        headers = {
            "selector": "th",
            "props": [
                ("background-color", "#000022"),
                ("color", "ivory"),
                ("font-weight", "bold"),
                ("text-align", "center"),
                ("border-bottom-style", "solid"),
                ("border-bottom-width", "1px"),
                ("border-bottom-color", "ivory"),
            ],
        }
        styler.hide()
        styler.set_table_styles([headers], overwrite=False)
        styler.format_index(lambda x: x.title(), axis=1)

        for c in curr_data.columns[4:]:

            styler.background_gradient(
                cmap="RdYlGn",
                subset=pd.IndexSlice[0 : n_games - 1, c],
                vmax=curr_total_data[c].max(),
                vmin=curr_total_data[c].min(),
            )
            styler.background_gradient(
                cmap="RdYlGn",
                subset=pd.IndexSlice[n_games, c],
                vmax=curr_total_data.groupby(["squad", "player"]).sum()[c].max(),
                vmin=curr_total_data.groupby(["squad", "player"])[c].sum().min(),
            )
        return styler
