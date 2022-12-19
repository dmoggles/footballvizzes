from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd
from fb_viz.helpers.fonts import font_normal, font_bold, font_mono
from fb_viz.helpers.mclachbot_helpers import sportsdb_image_grabber, get_mclachhead
from mplsoccer.pitch import VerticalPitch
from mplsoccer import add_image
from matplotlib.figure import Figure
from copy import deepcopy
from matplotlib import cm
from matplotlib.colors import ListedColormap
import numpy as np
from footmav.event_aggregation.aggregators import (
    ground_duels_won,
    ground_duels_lost,
    touches,
)


@dataclass
class HeatmapData:
    dataframe_success_dict: dict
    dataframe_failure_dict: dict

    bins_success: list
    bins_failure: list

    full_data: pd.DataFrame


class HeatmapBars(ABC):
    SCALE = 1
    PCT_BASED = False

    def __init__(
        self,
        connection,
        home_color,
        away_color,
        pitch_color="#333333",
        text_color="ivory",
    ) -> None:

        self._conn = connection
        self._home_color = home_color
        self._away_color = away_color
        self._pitch_color = pitch_color
        self._text_color = text_color

    @staticmethod
    def get_pitch_cmap():
        map = cm.get_cmap("binary")
        arr = map(np.array([0, 1]))
        arr[0] = np.array([3 / 16, 3 / 16, 3 / 16, 1])
        pitch_cmap = ListedColormap(arr)
        return pitch_cmap

    @abstractmethod
    def get_data(self, match_id) -> HeatmapData:
        pass

    def _draw_top(self, data, fig, ax):
        ax.set_facecolor(self._pitch_color)
        ax.set_axis_off()
        date = data["match_date"].iloc[0]
        home_team = data.loc[
            (data["is_home_team"] == True),
            "decorated_name",
        ].iloc[0]
        away_team = data.loc[
            (data["is_home_team"] == False),
            "decorated_name",
        ].iloc[0]
        ax.text(
            s=self.TITLE,
            x=0.5,
            y=0.99,
            ha="center",
            va="top",
            size=18,
            color=self._text_color,
            fontproperties=font_bold.prop,
        )
        ax.text(
            s=f"{home_team} vs {away_team}",
            x=0.5,
            y=0.5,
            ha="center",
            va="center",
            size=16,
            color=self._text_color,
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.5,
            0.2,
            f'{date.strftime("%A, %B %d %Y")}',
            color="grey",
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
            fontsize=14,
        )
        league = data["competition"].iloc[0]
        home_img = sportsdb_image_grabber(
            data.loc[data["is_home_team"] == True, "team"].iloc[0], league
        )
        away_img = sportsdb_image_grabber(
            data.loc[data["is_home_team"] == False, "team"].iloc[0], league
        )
        ax2 = fig.add_axes([0.15, 0.80, 0.09, 0.09])
        ax2.imshow(home_img)
        ax2.axis("off")
        ax3 = fig.add_axes([0.70, 0.80, 0.09, 0.09])
        ax3.imshow(away_img)
        ax3.axis("off")

    def _positional_bar_charts(self, ax, heatmap_data: HeatmapData):
        df_dict = heatmap_data.dataframe_success_dict
        bin_stat = heatmap_data.bins_success
        bin_stat_fail = heatmap_data.bins_failure

        teams = list(df_dict.keys())

        for i in range(len(bin_stat[teams[0]])):
            t1 = bin_stat[teams[0]][i]
            t2 = bin_stat[teams[1]][i]
            if bin_stat_fail:
                t1_l = bin_stat_fail[teams[0]][i]
                t2_l = bin_stat_fail[teams[1]][i]
            shape = t1["statistic"].shape
            width = 10
            for x in range(shape[0]):
                for y in range(shape[1]):
                    t1_v = t1["statistic"][x][y]
                    t2_v = t2["statistic"][x][y]
                    if bin_stat_fail:
                        t1_v_l = t1_l["statistic"][x][y]
                        t2_v_l = t2_l["statistic"][x][y]

                    t1_y1 = t1["x_grid"][x][y]
                    if t1["cy"].ndim == 1:
                        c = t1["cy"][y]
                    else:
                        c = t1["cy"][x][y]

                    ax.bar(
                        x=c + width / 2,
                        height=t1_v * self.SCALE,
                        width=width,
                        bottom=t1_y1 + 2,
                        color=self._home_color,
                        ec="black",
                    )
                    if bin_stat_fail:
                        ax.text(
                            x=c + width / 2,
                            y=t1_y1 + t1_v * self.SCALE + 4,
                            s=f"{int(t1_v)}/{int(t1_v+t1_v_l)}",
                            ha="center",
                            va="center",
                            color=self._text_color,
                            fontproperties=font_mono.prop,
                        )
                    else:
                        ax.text(
                            x=c + width / 2,
                            y=t1_y1 + t1_v * self.SCALE + 4,
                            s=f"{int(t1_v)}" if not self.PCT_BASED else f"{t1_v:.0%}",
                            ha="center",
                            va="center",
                            color=self._text_color,
                            fontproperties=font_mono.prop,
                        )
                    ax.bar(
                        x=c - width / 2,
                        height=t2_v * self.SCALE,
                        width=width,
                        bottom=t1_y1 + 2,
                        color=self._away_color,
                        ec="black",
                    )
                    if bin_stat_fail:
                        ax.text(
                            x=c - width / 2,
                            y=t1_y1 + 4 + t2_v * self.SCALE,
                            s=f"{int(t2_v)}/{int(t2_v+t2_v_l)}",
                            ha="center",
                            va="center",
                            color=self._text_color,
                            fontproperties=font_mono.prop,
                        )
                    else:
                        ax.text(
                            x=c - width / 2,
                            y=t1_y1 + 4 + t2_v * self.SCALE,
                            s=f"{int(t2_v)}" if not self.PCT_BASED else f"{t2_v:.0%}",
                            ha="center",
                            va="center",
                            color=self._text_color,
                            fontproperties=font_mono.prop,
                        )

    def draw(self, heatmap_data: HeatmapData):
        df_dict = heatmap_data.dataframe_success_dict
        bin_stat = heatmap_data.bins_success
        data = heatmap_data.full_data
        fig = Figure(dpi=100, figsize=(8, 12.6))
        axes = fig.subplot_mosaic(
            [
                [".", "top", ".", "."],
                ["dir_left", "main", "zone_right", "dir_right"],
                [".", "zone_bottom", ".", "."],
                ["bottom", "bottom", "bottom", "bottom"],
            ],
            gridspec_kw={
                "width_ratios": [0.04, 0.81, 0.11, 0.04],
                "height_ratios": [0.1, 0.78, 0.05, 0.02],
            },
        )
        fig.set_facecolor(self._pitch_color)
        for ax in axes.values():
            ax.set_axis_off()
            ax.set_facecolor(self._pitch_color)
        fig.subplots_adjust(wspace=0, hspace=0)
        pitch = VerticalPitch(
            "opta",
            pitch_color=self._pitch_color,
            pad_left=0,
            pad_right=0,
            pad_bottom=0,
            pad_top=0,
            positional=False,
            line_alpha=0.2,
        )
        vertical_thirds = {}
        for third in [1, 2, 3]:
            vertical_thirds[third] = {}
            for home in [1, 0]:
                vertical_thirds[third][home] = len(
                    df_dict[home].loc[
                        (df_dict[home]["x"] >= (third - 1) * (100.0 / 3.0))
                        & (df_dict[home]["x"] < (third) * (100.0 / 3.0))
                    ]
                )
                if self.PCT_BASED:
                    vertical_thirds[third][home] = vertical_thirds[third][home] / (
                        len(df_dict[0]) + len(df_dict[1])
                    )

        horizontal_thirds = {}
        for third in [1, 2, 3]:
            horizontal_thirds[third] = {}
            for home in [1, 0]:
                horizontal_thirds[third][home] = len(
                    df_dict[home].loc[
                        (df_dict[home]["y"] >= (third - 1) * (100.0 / 3.0))
                        & (df_dict[home]["y"] < (third) * (100.0 / 3.0))
                    ]
                )
                if self.PCT_BASED:
                    horizontal_thirds[third][home] = horizontal_thirds[third][home] / (
                        len(df_dict[0]) + len(df_dict[1])
                    )

        pitch.draw(axes["main"])
        sample = deepcopy(bin_stat[0])
        for d in sample:
            d["statistic"] *= 0
        pitch.heatmap_positional(
            sample,
            ax=axes["main"],
            cmap=self.get_pitch_cmap(),
            edgecolors=(1, 1, 1, 1),
            alpha=0.8,
        )
        self._positional_bar_charts(axes["main"], heatmap_data)
        axes["dir_left"].annotate(
            text="",
            xy=(0.5, 0.9),
            xytext=(0.5, 0.1),
            arrowprops={"width": 5, "color": self._home_color},
        )

        axes["dir_left"].text(
            s=df_dict[1]["decorated_name"].iloc[0],
            x=-0.1,
            y=0.5,
            rotation="vertical",
            color=self._text_color,
            size=14,
            va="center",
            ha="center",
        )
        axes["dir_right"].annotate(
            text="",
            xy=(0.25, 0.1),
            xytext=(0.25, 0.9),
            arrowprops={"width": 5, "color": self._away_color},
        )
        axes["dir_right"].text(
            s=df_dict[0]["decorated_name"].iloc[0],
            x=0.7,
            y=0.5,
            rotation=270,
            color=self._text_color,
            size=14,
            va="center",
            ha="center",
        )

        axes["bottom"].text(
            s="@mclachbot",
            x=0.99,
            y=0.5,
            color="grey",
            size=10,
            ha="right",
            va="center",
            alpha=0.5,
        )
        self._draw_top(data, fig, axes["top"])
        axes["zone_right"].set_ylim(0, 100)
        axes["zone_right"].set_xlim(0, 1)
        axes["zone_right"].axhline(
            100.0 / 3.0, 0, 1, color="grey", lw=2, alpha=0.5, linestyle="dotted"
        )
        axes["zone_right"].axhline(
            200.0 / 3.0, 0, 1, color="grey", lw=2, alpha=0.5, linestyle="dotted"
        )
        for third in vertical_thirds:
            bottom = (third - 1) * 100.0 / 3.0 + 2
            width = 0.35
            axes["zone_right"].bar(
                x=0.5 - width / 2,
                bottom=bottom,
                height=vertical_thirds[third][1] * self.SCALE,
                width=width,
                color=self._home_color,
                ec="black",
            )
            axes["zone_right"].text(
                x=0.5 - width / 2,
                y=bottom + (vertical_thirds[third][1]) * self.SCALE + 2,
                s=int(vertical_thirds[third][1])
                if not self.PCT_BASED
                else "{:.0%}".format(vertical_thirds[third][1]),
                ha="center",
                va="center",
                color=self._text_color,
                fontproperties=font_normal.prop,
                size=10,
            )
            axes["zone_right"].bar(
                x=0.5 + width / 2,
                bottom=bottom,
                height=vertical_thirds[third][0] * self.SCALE,
                width=width,
                color=self._away_color,
                ec="black",
            )
            axes["zone_right"].text(
                x=0.5 + width / 2,
                y=bottom + (vertical_thirds[third][0]) * self.SCALE + 2,
                s=int(vertical_thirds[third][0])
                if not self.PCT_BASED
                else "{:.0%}".format(vertical_thirds[third][0]),
                ha="center",
                va="center",
                color=self._text_color,
                fontproperties=font_normal.prop,
                size=10,
            )

        axes["zone_bottom"].set_ylim(0, 1)
        axes["zone_bottom"].set_xlim(0, 100)
        axes["zone_bottom"].axvline(
            100.0 / 3.0, 0, 1, color="grey", lw=2, alpha=0.5, linestyle="dotted"
        )
        axes["zone_bottom"].axvline(
            200.0 / 3.0, 0, 1, color="grey", lw=2, alpha=0.5, linestyle="dotted"
        )
        for third in vertical_thirds:
            left = (third - 1) * 100.0 / 3.0 + 2
            width = 0.45
            axes["zone_bottom"].barh(
                y=0.5 + width / 2,
                left=left,
                width=horizontal_thirds[third][1] * self.SCALE,
                height=width,
                color=self._home_color,
                ec="black",
            )
            axes["zone_bottom"].text(
                y=0.5 + width / 2,
                x=left
                + (horizontal_thirds[third][1]) * self.SCALE
                + (2 if not self.PCT_BASED else 4),
                s=int(horizontal_thirds[third][1])
                if not self.PCT_BASED
                else "{:.0%}".format(horizontal_thirds[third][1]),
                ha="center",
                va="center",
                color=self._text_color,
                fontproperties=font_normal.prop,
                size=10,
            )
            axes["zone_bottom"].barh(
                y=0.5 - width / 2,
                left=left,
                width=horizontal_thirds[third][0] * self.SCALE,
                height=width,
                color=self._away_color,
                ec="black",
            )
            axes["zone_bottom"].text(
                y=0.5 - width / 2,
                x=left
                + (horizontal_thirds[third][0]) * self.SCALE
                + (2 if not self.PCT_BASED else 4),
                s=int(horizontal_thirds[third][0])
                if not self.PCT_BASED
                else "{:.0%}".format(horizontal_thirds[third][0]),
                ha="center",
                va="center",
                color=self._text_color,
                fontproperties=font_normal.prop,
                size=10,
            )

        add_image(get_mclachhead(), fig, 0.86, 0.12, 0.03, 0.06)

        return fig


class GroundDuelsPitchArea(HeatmapBars):
    TITLE = "Ground Duels Won By Zone"

    def get_data(self, match_id) -> HeatmapData:
        data = self._conn.wsquery(
            f"""SELECT W.*, T.decorated_name, M.home_score, M.away_score FROM whoscored W
            LEFT JOIN mclachbot_teams T ON W.team=T.ws_team_name
            LEFT JOIN whoscored_meta M ON W.matchId = M.matchId
            
            WHERE W.matchId = {match_id}
            """
        )

        ground_duels_won_df = data[ground_duels_won(data)]
        ground_duels_lost_df = data[ground_duels_lost(data)]
        df_dict = dict()
        df_dict_lost = dict()
        for t in [1, 0]:
            df_dict[t] = ground_duels_won_df.loc[
                ground_duels_won_df["is_home_team"] == t
            ].copy()
            df_dict_lost[t] = ground_duels_lost_df.loc[
                ground_duels_lost_df["is_home_team"] == t
            ].copy()
            if t == 0:
                df_dict[t]["x"] = 100 - df_dict[t]["x"]
                df_dict[t]["y"] = 100 - df_dict[t]["y"]
                df_dict_lost[t]["x"] = 100 - df_dict_lost[t]["x"]
                df_dict_lost[t]["y"] = 100 - df_dict_lost[t]["y"]

        bin_stat = dict()
        bin_stat_fail = dict()
        pitch = VerticalPitch(
            "opta",
            pad_left=0,
            pad_right=0,
            pad_bottom=0,
            pad_top=0,
            positional=False,
            line_alpha=0.2,
        )
        for t in df_dict.keys():

            bin_stat[t] = [
                pitch.bin_statistic(
                    df_dict[t].x, df_dict[t].y, statistic="count", bins=(3, 3)
                )
            ]
            bin_stat_fail[t] = [
                pitch.bin_statistic(
                    df_dict_lost[t].x, df_dict_lost[t].y, statistic="count", bins=(3, 3)
                )
            ]

        return HeatmapData(df_dict, df_dict_lost, bin_stat, bin_stat_fail, data)


class TouchesPitchArea(HeatmapBars):
    TITLE = "Touches By Zone"
    SCALE = 50
    PCT_BASED = True

    def get_data(self, match_id) -> HeatmapData:
        data = self._conn.wsquery(
            f"""SELECT W.*, T.decorated_name, M.home_score, M.away_score FROM whoscored W
            LEFT JOIN mclachbot_teams T ON W.team=T.ws_team_name
            LEFT JOIN whoscored_meta M ON W.matchId = M.matchId
            
            WHERE W.matchId = {match_id}
            """
        )

        touches_df = data[touches(data)]
        df_dict = dict()
        for t in [1, 0]:
            df_dict[t] = touches_df.loc[touches_df["is_home_team"] == t].copy()
            if t == 0:
                df_dict[t]["x"] = 100 - df_dict[t]["x"]
                df_dict[t]["y"] = 100 - df_dict[t]["y"]

        bin_stat = dict()
        pitch = VerticalPitch(
            "opta",
            pad_left=0,
            pad_right=0,
            pad_bottom=0,
            pad_top=0,
            positional=False,
            line_alpha=0.2,
        )
        for t in df_dict.keys():

            bin_stat[t] = [
                pitch.bin_statistic(
                    df_dict[t].x,
                    df_dict[t].y,
                    statistic="count",
                    bins=(3, 3),
                )
            ]
        for d in [0, 1]:

            bin_stat[d][0]["statistic"] /= df_dict[0].shape[0] + df_dict[1].shape[0]

        return HeatmapData(df_dict, None, bin_stat, None, data)
