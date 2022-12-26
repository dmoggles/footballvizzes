from mplsoccer import VerticalPitch, set_visible
from fb_viz.helpers.mplsoccer_helpers import make_grid
from fb_viz.helpers.mclachbot_helpers import (
    sportsdb_league_image_grabber,
    sportsdb_image_grabber,
)
from fb_viz.helpers.fonts import font_bold, font_normal
from matplotlib.axes import Axes
from typing import Dict
from PIL.PngImagePlugin import PngImageFile
import numpy as np
from dbconnect.connector import Connection


def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return width, height


class TeamOfTheWeek:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_data(self, week, league, season):
        conn = Connection("M0neyMa$e")

        data = conn.query(
            f"""
            SELECT TOTW.*, ML.sportsdbname, ML.sportsdbid, ML.decorated_name, 
            IF (ISNULL(MT.image_name_override), TOTW.squad, MT.image_name_override) AS image_name_override FROM derived.team_of_the TOTW
            LEFT JOIN football_data.mclachbot_leagues ML ON TOTW.comp = ML.league_name
            LEFT JOIN football_data.mclachbot_teams MT ON TOTW.squad = MT.team_name AND MT.gender=ML.gender
            WHERE team_type = 'team_of_the_week'
            AND label='{week}'
            AND comp='{league}'
            AND season={season}

            """
        )

        return data

    def get_overall_data(self, league):
        conn = Connection("M0neyMa$e")
        data = conn.query(
            f""" 
        SELECT position, shotstopping, distribution, area_control, defending, finishing, providing, progressing FROM derived.fbref_power_ranking_new WHERE comp='{league}'
        """
        )
        return data

    def _draw_title(self, data, pitch: VerticalPitch, ax: Axes):
        ax.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        ax.text(
            0.05,
            0.7,
            f"Team of the Week",
            ha="left",
            va="center",
            fontsize=24,
            color="ivory",
            fontproperties=font_bold.prop,
        )
        ax.text(
            0.05,
            0.2,
            f'{data["decorated_name"].iloc[0]} Matchweek {data["label"].iloc[0]}',
            ha="left",
            va="center",
            fontsize=16,
            color="ivory",
            fontproperties=font_bold.prop,
        )

        league_image = sportsdb_league_image_grabber(data["comp"].iloc[0])

        ax_width, ax_height = get_ax_size(ax, ax.get_figure())

        target_height = 1.1
        target_width = target_height * ax_height / ax_width

        ax_img = pitch.inset_axes(
            y=1 - target_width / 2.0,
            x=0.5,
            width=target_width,
            length=target_height,
            ax=ax,
        )
        ax_img.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        set_visible(ax_img)
        ax_img.imshow(league_image)

    def _draw_one_position(
        self,
        data,
        pitch: VerticalPitch,
        ax: Axes,
        position: str,
        team_badges: Dict[str, PngImageFile],
    ):
        set_visible(ax)
        ax.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        ax.set_alpha(0.0)
        data_position = data[data["placement_position"] == position]

        badge_image_inset = pitch.inset_axes(
            x=0.75, y=0.25, width=0.5, length=0.5, ax=ax
        )
        set_visible(badge_image_inset)
        badge_image_inset.imshow(
            team_badges[data_position["image_name_override"].iloc[0]], zorder=5
        )
        badge_image_inset.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        performance_inset = pitch.inset_axes(
            x=0.75, y=0.75, width=0.5, length=0.5, ax=ax
        )

        if position == "GK":
            self.draw_equalateral_triangle(
                performance_inset,
                data_position["shotstopping_ranking"].iloc[0],
                data_position["distribution_ranking"].iloc[0],
                data_position["area_control_ranking"].iloc[0],
            )
        else:
            self.draw_diamond(
                performance_inset,
                data_position["progressing_ranking"].iloc[0],
                data_position["defending_ranking"].iloc[0],
                data_position["providing_ranking"].iloc[0],
                data_position["finishing_ranking"].iloc[0],
            )

        if data_position["total"].iloc[0] == data["total"].max():
            badge_image_inset.scatter(
                80,
                80,
                color="gold",
                alpha=1,
                marker="*",
                zorder=10,
                s=200,
                linewidth=1,
                edgecolor="black",
            )

        # ax.text(
        #     0.0,
        #     0.4,
        #     f'{data_position["player"].iloc[0].title()}',
        #     ha='left',
        #     va='center',
        #     fontsize=10,
        #     color='ivory',
        #     fontproperties=font_normal.prop,
        # )

        ax.text(
            0.5,
            0.4,
            f'{data_position["player"].iloc[0].title()}',
            ha="center",
            va="center",
            fontsize=10,
            color="ivory",
            fontproperties=font_normal.prop,
        )

        texts = "\n".join(
            [
                self._get_stat_text(
                    data_position[f"top_category_{i}"].iloc[0],
                    data_position[f"top_value_{i}"].iloc[0],
                )
                for i in range(1, 4)
            ]
        )
        # ax.text(
        #     0.0,
        #     0.3,
        #     texts,
        #     ha='left',
        #     va='top',
        #     fontsize=9,
        #     color='silver',
        #     fontproperties=font_normal.prop,
        # )
        ax.text(
            0.5,
            0.3,
            texts,
            ha="center",
            va="top",
            fontsize=9,
            color="silver",
            fontproperties=font_normal.prop,
        )

    def _get_stat_text(self, category, value):
        category = category.replace("_", " ").title()
        replacements = {
            "Passes Into Penalty Area": "Passes Into Box",
            "Sca": "Created Shots",
            "Psxg": "PSxG Overperformance",
        }
        no_number_categories = [
            "Clean Sheet",
            "Winning Goal",
            "Equalising Goal",
            "Opening Goal",
        ]
        category = replacements.get(category, category)

        if value == 1 and category.endswith("s"):
            category = category[:-1]

        if category in no_number_categories:
            return category
        return (
            f"{value:.0f} {category}"
            if value.is_integer()
            else f"{value:.2f} {category}"
        )

    def _get_team_badge_table(self, data):
        team_names = data["image_name_override"].unique()
        league = data["comp"].iloc[0]
        team_badges = {
            team_name: sportsdb_image_grabber(team_name.replace("_", " "), league)
            for team_name in team_names
        }
        return team_badges

    def _draw_pitch(
        self, data, pitch: VerticalPitch, ax: Axes, team_badges: Dict[str, PngImageFile]
    ):
        positions_axes = pitch.inset_formation_axes("433", length=12, aspect=1, ax=ax)
        for position, ax in positions_axes.items():
            self._draw_one_position(data, pitch, ax, position, team_badges)

    def _attach_ranking(self, data, ranking_baseline_data):

        for i, row in data.iterrows():
            if row["position"] == "GK":
                comparision = ranking_baseline_data[
                    ranking_baseline_data["position"] == "GK"
                ]
                stats = ["shotstopping", "area_control", "distribution"]

            else:
                comparision = ranking_baseline_data[
                    ranking_baseline_data["position"] != "GK"
                ]
                stats = ["defending", "finishing", "providing", "progressing"]

            for stat in stats:
                comp = comparision[comparision[stat] != 0].copy()
                data.loc[i, f"{stat}_ranking"] = len(
                    comp[comp[stat] < row[stat]]
                ) / len(comp)

    def draw(self, week, league, season):
        data = self.get_data(week, league, season)
        ranking_baseline_data = self.get_overall_data(league)
        self._attach_ranking(data, ranking_baseline_data)

        pitch = VerticalPitch(pitch_type="opta", line_zorder=4, **self.kwargs)
        fig, axes = make_grid(
            pitch=pitch,
            figheight=14,
            title_height=0.05,
            title_space=0,
            endnote_height=0.05,
            endnote_space=0,
        )
        fig.set_facecolor(self.kwargs.get("pitch_color", "#333333"))

        for ax_name in ["title", "endnote"]:
            set_visible(axes[ax_name])

        self._draw_title(data, pitch, axes["title"])
        team_badges = self._get_team_badge_table(data)
        self._draw_pitch(data, pitch, axes["pitch"], team_badges)
        self._draw_endnote(pitch, axes["endnote"])
        return fig

    def draw_diamond(self, ax, left, bottom, right, top):
        ax.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        ax.set_alpha(0.0)
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        set_visible(ax)
        for i in range(1, 4):
            ax.plot(
                [0, i / 3.0, 0, -i / 3.0, 0],
                [i / 3.0, 0, -i / 3.0, 0, i / 3.0],
                color="#ffffff",
                linewidth=1,
                alpha=0.2,
            )
        ax.fill(
            [-left, 0, right, 0],
            [0, top, 0, -bottom],
            color="red",
            linewidth=1,
            alpha=0.2,
        )
        ax.scatter(0, 0, color="ivory", s=3)

    def draw_equalateral_triangle(self, ax, top, left, right):
        ax.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        ax.set_alpha(0.0)
        ax.set_xlim(-np.sqrt(3) / 2, np.sqrt(3) / 2)
        ax.set_ylim(-0.5, 1)
        set_visible(ax)
        for i in range(3, 0, -1):
            ax.plot(
                [
                    -(i / 3) * np.sqrt(3) / 2,
                    0,
                    (i / 3) * np.sqrt(3) / 2,
                    -(i / 3) * np.sqrt(3) / 2,
                ],
                [
                    -(i / 3) * 0.5,
                    (i / 3) * 1,
                    -(i / 3) * 0.5,
                    -(i / 3) * 0.5,
                ],
                color="#ffffff",
                linewidth=1,
                alpha=0.2,
            )

        ax.fill(
            [
                -(left) * np.sqrt(3) / 2,
                0,
                (right) * np.sqrt(3) / 2,
                -(left) * np.sqrt(3) / 2,
            ],
            [
                -(left) * 0.5,
                (top) * 1,
                -(right) * 0.5,
                -(left) * 0.5,
            ],
            color="magenta",
            linewidth=1,
            alpha=0.2,
        )
        ax.scatter(0, 0, color="ivory", s=3)

    def _draw_endnote(self, pitch, ax):
        ax.set_facecolor(self.kwargs.get("pitch_color", "#333333"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.scatter(
            0.02,
            0.5,
            color="gold",
            marker="*",
            s=200,
            linewidth=1,
            edgecolor="black",
            zorder=5,
        )
        ax.text(
            0.045,
            0.5,
            "Player of\nthe Week",
            color="silver",
            fontsize=10,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )
        diamond_inset = pitch.inset_axes(0.5, 0.35, length=0.8, aspect=1, ax=ax)
        self.draw_diamond(diamond_inset, 0.6, 0.6, 0.6, 0.6)
        ax.text(
            0.305,
            0.5,
            "progressing",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="right",
            va="center",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.35,
            1.1,
            "shooting",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="top",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.35,
            -0.1,
            "defending",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="bottom",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.395,
            0.5,
            "creating",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )

        triange_inset = pitch.inset_axes(0.5, 0.65, length=0.8, aspect=1, ax=ax)
        self.draw_equalateral_triangle(triange_inset, 0.6, 0.6, 0.6)
        ax.text(
            0.65,
            1.1,
            "shot stopping",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="center",
            va="top",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.6,
            0.2,
            "distribution",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="right",
            va="center",
            fontproperties=font_normal.prop,
        )
        ax.text(
            0.7,
            0.2,
            "area control",
            color="ivory",
            alpha=0.5,
            fontsize=9,
            ha="left",
            va="center",
            fontproperties=font_normal.prop,
        )

        ax.text(
            0.98,
            0.5,
            "Follow on\n@McLachBot",
            color="silver",
            fontsize=10,
            ha="right",
            va="center",
            fontproperties=font_normal.prop,
        )
