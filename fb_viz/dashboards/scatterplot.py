import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple, Sequence, Dict, List
import numpy as np
from fb_viz.helpers.fonts import font_normal, font_bold, font_italic
from fb_viz.helpers.mclachbot_helpers import sportsdb_league_image_grabber
from sklearn.ensemble import IsolationForest
from adjustText import adjust_text
from footmav import fb
from matplotlib.cm import get_cmap


class ScatterPlot:
    FIG_SIZE = (14, 15.4)
    BACKGROUND_COLOR = "oldlace"
    LEAGUE_COLOURS = {
        "La Liga": ("yellow", "red"),
        "Premier League": ("red", "white"),
        "Ligue 1": ("white", "blue"),
        "Bundesliga": ("black", "white"),
        "Serie A": ("white", "green"),
        "Eredivisie": ("black", "orange"),
        "Primeira Liga": ("green", "red"),
    }
    TITLE_IDX = 0
    SCATTER_PLOT_IDX = 1
    ENDNOTE_IDX = 2

    TITLE_SIZE = 24
    SUBTITLE_SIZE = 18

    TOP_BOUNDARY_MULT = 1.05
    BOTTOM_BOUNDARY_MULT = 0.95
    LEFT_BOUNDARY_MULT = 0
    RIGHT_BOUNDARY_MULT = 1.05
    GRID_COLOR = "silver"
    MEAN_LINE_COLOR = "ivory"
    TOP_RIGHT_HALF_COLOR = "green"
    BOTTOM_RIGHT_HALF_COLOR = "yellow"
    TOP_LEFT_HALF_COLOR = "yellow"
    BOTTOM_LEFT_HALF_COLOR = "red"
    INNER_DATA_COLOUR = "silver"

    COLOR_MARKING_THRESHOLD = 0.4
    NAME_ANNOTATION_THRESHOLD = 0.2
    ARROW_COLOR = "darkslategray"

    HALF_ANNOTATIONS = {
        "topright": {"x": 0.99, "y": 0.99, "va": "top", "ha": "right"},
        "topleft": {"x": 0.01, "y": 0.99, "va": "top", "ha": "left"},
        "bottomright": {"x": 0.99, "y": 0.01, "va": "bottom", "ha": "right"},
        "bottomleft": {"x": 0.01, "y": 0.01, "va": "bottom", "ha": "left"},
    }
    FAN_ANNOTATIONS = [
        {"x": 0.01, "y": 0.99, "va": "top", "ha": "left"},
        {"x": 0.99, "y": 0.01, "va": "bottom", "ha": "right"},
    ]

    @staticmethod
    def _player_name(name):
        tokens = name.split(" ")
        if len(tokens) == 1:
            return name.title()
        return " ".join([tokens[0][0], tokens[-1]]).title()

    @staticmethod
    def _get_aspect(ax):
        """Get the aspect ratio of an axes.
        From Stackoverflow post by askewchan:
        https://stackoverflow.com/questions/41597177/get-aspect-ratio-of-axes

        Parameters
        ----------
        ax : matplotlib.axes.Axes, default None
        Returns
        -------
        float
        """
        left_bottom, right_top = ax.get_position() * ax.figure.get_size_inches()
        width, height = right_top - left_bottom
        return height / width * ax.get_data_ratio()

    @classmethod
    def _init_fig(cls) -> Tuple[Figure, Sequence[Axes]]:
        fig = plt.figure(figsize=cls.FIG_SIZE)
        fig.set_facecolor(cls.BACKGROUND_COLOR)
        axes = fig.subplots(nrows=3, height_ratios=[0.05, 0.9, 0.05])
        for ax in axes:
            ax.set_facecolor(cls.BACKGROUND_COLOR)
        for ax_idx in [cls.TITLE_IDX, cls.ENDNOTE_IDX]:
            axes[ax_idx].axis("off")
            axes[ax_idx].set_xlim(0, 1)
            axes[ax_idx].set_ylim(0, 1)
        return fig, axes

    @classmethod
    def _draw_title(cls, ax: Axes, title: str, subtitle: str):
        ax.text(
            0.5,
            0.5,
            title,
            ha="center",
            va="center",
            size=cls.TITLE_SIZE,
            fontproperties=font_bold.prop,
        )
        if subtitle:
            ax.text(
                0.5,
                -0.2,
                subtitle,
                ha="center",
                va="center",
                size=cls.SUBTITLE_SIZE,
                fontproperties=font_italic.prop,
            )

    @classmethod
    def _draw_league_legend(cls, ax: Axes, competitions: Sequence[str]):
        competitions = sorted(competitions)
        n_comps = len(competitions)
        for i, league in enumerate(competitions):
            border, colour = cls.LEAGUE_COLOURS[league]
            x = 0.01 + i * 1.0 / n_comps
            ax.scatter([x], [0.5], c=colour, edgecolor=border, s=100)
            inset_ax = ax.inset_axes([x + 0.02, 0, cls._get_aspect(ax), 1])
            inset_ax.axis("off")
            inset_ax.imshow(sportsdb_league_image_grabber(league))

    @classmethod
    def _add_endnote_annotations(cls, ax: Axes, explanatory_comment: str):
        if explanatory_comment:
            ax.text(
                0.01,
                1.1,
                explanatory_comment,
                size=10,
                ha="left",
                va="bottom",
                fontproperties=font_italic.prop,
            )
        ax.text(
            0.99,
            0.5,
            "@mclachbot\nData:FbRef",
            size=10,
            va="center",
            ha="center",
            fontproperties=font_normal.prop,
        )

    @classmethod
    def _draw_endnote(
        cls, ax: Axes, competitions: Sequence[str], explanatory_comment: str
    ):
        cls._draw_league_legend(ax, competitions)
        cls._add_endnote_annotations(ax, explanatory_comment)

    @classmethod
    def _setup_data(cls, df, x_param, y_param):
        model1 = IsolationForest(
            contamination=cls.COLOR_MARKING_THRESHOLD, random_state=0
        )
        model2 = IsolationForest(
            contamination=cls.NAME_ANNOTATION_THRESHOLD, random_state=0
        )

        df["inner_ring"] = model1.fit_predict(df[[x_param, y_param]])
        df["annotate"] = model2.fit_predict(df[[x_param, y_param]])

    @classmethod
    def _setup_scatter_axes(
        cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str
    ):
        max_y = df[y_param].max() * cls.TOP_BOUNDARY_MULT
        min_y = df[y_param].min() * cls.BOTTOM_BOUNDARY_MULT
        max_x = df[x_param].max() * cls.RIGHT_BOUNDARY_MULT
        min_x = df[x_param].min() * cls.LEFT_BOUNDARY_MULT
        ax.set_ylim(min_y, max_y)
        ax.set_xlim(min_x, max_x)
        ax.grid(color=cls.GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.5)
        ax.set_xlabel(x_param, fontproperties=font_normal.prop, size=16)
        ax.set_ylabel(y_param, fontproperties=font_normal.prop, size=16)
        for label in ax.get_xticklabels():
            label.set_fontproperties(font_normal.prop)

        for label in ax.get_yticklabels():
            label.set_fontproperties(font_normal.prop)

    @classmethod
    def _scatter_inner_points(
        cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str
    ):
        inner_df = df.loc[df["inner_ring"] == 1]
        ax.scatter(
            inner_df[x_param],
            inner_df[y_param],
            c=cls.INNER_DATA_COLOUR,
            alpha=0.5,
            zorder=2,
        )

    @classmethod
    def _scatter_league_marked_points(
        cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str
    ):
        leagues = df[fb.COMPETITION.N].unique()
        outer_df = df.loc[df["inner_ring"] == -1]
        for league in leagues:
            border, color = cls.LEAGUE_COLOURS[league]
            df_ = outer_df.loc[outer_df[fb.COMPETITION.N] == league]
            ax.scatter(
                df_[x_param], df_[y_param], c=color, edgecolor=border, s=100, zorder=3
            )

    @classmethod
    def _annotate_player_names(
        cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str
    ) -> list:
        annotate_df = df.loc[df["annotate"] == -1]
        annotate_df["name"] = annotate_df[fb.PLAYER.N].apply(
            lambda x: cls._player_name(x)
        )

        texts = []
        props = dict(boxstyle="round", facecolor=cls.BACKGROUND_COLOR, alpha=1)
        for _, row in annotate_df.iterrows():
            texts.append(
                ax.text(
                    row[x_param],
                    row[y_param],
                    row["name"],
                    size=11,
                    fontproperties=font_normal.prop,
                    bbox=props,
                    zorder=4,
                )
            )

        return texts

    @classmethod
    def _plot_scatters(cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str):
        cls._scatter_inner_points(ax, df, x_param, y_param)
        cls._scatter_league_marked_points(ax, df, x_param, y_param)

    @classmethod
    def _draw_halves(cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str):
        mean_x = df[x_param].mean()
        mean_y = df[y_param].mean()
        min_x, max_x = ax.get_xlim()
        min_y, max_y = ax.get_ylim()

        ax.axvline(
            [mean_x],
            ymin=0,
            ymax=1,
            linestyle="--",
            lw=1,
            color=cls.MEAN_LINE_COLOR,
            zorder=1,
        )
        ax.axhline(
            [mean_y],
            xmin=0,
            xmax=1,
            linestyle="--",
            lw=1,
            color=cls.MEAN_LINE_COLOR,
            zorder=1,
        )
        ax.fill(
            [min_x, min_x, mean_x, mean_x],
            [mean_y, max_y, max_y, mean_y],
            color=cls.TOP_LEFT_HALF_COLOR,
            alpha=0.1,
            zorder=0.9,
        )
        ax.fill(
            [min_x, min_x, mean_x, mean_x],
            [mean_y, min_y, min_y, mean_y],
            color=cls.BOTTOM_LEFT_HALF_COLOR,
            alpha=0.1,
            zorder=0.9,
        )
        ax.fill(
            [max_x, max_x, mean_x, mean_x],
            [mean_y, min_y, min_y, mean_y],
            color=cls.BOTTOM_RIGHT_HALF_COLOR,
            alpha=0.1,
            zorder=0.9,
        )
        ax.fill(
            [max_x, max_x, mean_x, mean_x],
            [mean_y, max_y, max_y, mean_y],
            color=cls.TOP_RIGHT_HALF_COLOR,
            alpha=0.1,
            zorder=0.9,
        )

    @classmethod
    def _draw_fans(cls, ax: Axes, df: pd.DataFrame, x_param: str, y_param: str):
        cmap = get_cmap("RdYlGn")
        z = np.polyfit(df[x_param], df[y_param], 1)
        coefs = sorted([1.6, 1.3, 1.0, 1 / 1.3, 1 / 1.6])
        x = sorted(df[x_param].tolist() + [ax.get_xlim()[0], ax.get_xlim()[1]])

        for i, coef in enumerate(coefs):

            p = np.poly1d([z[0] * coef, z[1]])

            ax.plot(
                x,
                p(x),
                linestyle="--",
                lw=1,
                color=cls.MEAN_LINE_COLOR,
                zorder=1,
            )
            if i == 0:
                ax.fill_between(
                    x,
                    p(x),
                    np.ones(len(x)) * ax.get_ylim()[0],
                    color=cmap(0.0),
                    alpha=0.1,
                    zorder=0.9,
                )

            else:
                p_prev = np.poly1d([z[0] * coefs[i - 1], z[1]])
                ax.fill_between(
                    x,
                    p(x),
                    p_prev(x),
                    color=cmap(i / (len(coefs) + 1)),
                    alpha=0.1,
                    zorder=0.9,
                )

        ax.fill_between(
            x,
            p(x),
            np.ones(len(x)) * ax.get_ylim()[1],
            color=cmap(1.0),
            alpha=0.1,
            zorder=0.9,
        )

    @classmethod
    def _annotate_halves(cls, ax: Axes, half_annotations: Dict[str, str]):
        props = dict(boxstyle="round", facecolor=cls.BACKGROUND_COLOR, alpha=1)
        for location, annotation in half_annotations.items():
            placement = cls.HALF_ANNOTATIONS[location]
            ax.text(
                s=annotation,
                transform=ax.transAxes,
                bbox=props,
                fontproperties=font_normal.prop,
                size=12,
                **placement,
                zorder=6
            )

    @classmethod
    def _annotate_fans(cls, ax: Axes, fan_annotations: List[str]):
        props = dict(boxstyle="round", facecolor=cls.BACKGROUND_COLOR, alpha=1)
        for i, annotation in enumerate(fan_annotations):
            placement = cls.FAN_ANNOTATIONS[i]
            ax.text(
                s=annotation,
                transform=ax.transAxes,
                bbox=props,
                fontproperties=font_normal.prop,
                size=12,
                **placement,
                zorder=6
            )

    @classmethod
    def _draw_scatter(
        cls,
        ax: Axes,
        df: pd.DataFrame,
        x_column: str,
        y_column: str,
        draw_halves: bool,
        draw_fans: bool,
        half_annotations: Dict[str, str],
        fan_annotations: List[str],
    ):
        cls._setup_data(df, x_column, y_column)
        cls._setup_scatter_axes(ax, df, x_column, y_column)
        if draw_fans and draw_halves:
            raise ValueError("Cannot draw fans and halves at the same time")

        if draw_halves:
            cls._draw_halves(ax, df, x_column, y_column)
        if draw_fans:
            cls._draw_fans(ax, df, x_column, y_column)

        cls._plot_scatters(ax, df, x_column, y_column)

        player_name_texts = cls._annotate_player_names(ax, df, x_column, y_column)
        cls._annotate_halves(ax, half_annotations)
        cls._annotate_fans(ax, fan_annotations)
        adjust_text(
            player_name_texts,
            ax=ax,
            only_move={"text": "xy"},
            force_points=(8, 8),
            force_objects=(8, 8),
            arrowprops=dict(arrowstyle="->", color=cls.ARROW_COLOR, lw=1),
            zorder=7,
        )

    @classmethod
    def draw(
        cls,
        data: pd.DataFrame,
        title: str,
        x_column: str,
        y_column: str,
        subtitle: str = "",
        explanatory_comment: str = "",
        draw_halves: bool = False,
        draw_fans: bool = False,
        half_annotations: Dict[str, str] = None,
        fan_annotations: List[str] = None,
    ) -> Figure:

        half_annotations = half_annotations or {}
        fig, axes = cls._init_fig()

        cls._draw_title(axes[cls.TITLE_IDX], title, subtitle)
        cls._draw_endnote(
            axes[cls.ENDNOTE_IDX], data[fb.COMPETITION.N].unique(), explanatory_comment
        )

        cls._draw_scatter(
            axes[cls.SCATTER_PLOT_IDX],
            data,
            x_column,
            y_column,
            draw_halves,
            draw_fans,
            half_annotations,
            fan_annotations,
        )

        return fig
