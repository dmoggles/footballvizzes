import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def background_gradient_from_another_column(
    df, column, cmap="PuBu", low=0, high=0, text_luminance_threshold=0.408
):
    """
    Color background in a DataFrame depending on the data in another column.
    The colors range from the minimum of `low` or the column to the maximum of `high` or the column.
    """

    def _luminance(r, g, b):
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    vmin = min(low, column.min())
    vmax = max(high, column.max())
    norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax)
    normed = norm(column.values)
    c = [matplotlib.colors.rgb2hex(x) for x in plt.cm.get_cmap(cmap)(normed)]
    luminance = np.array([_luminance(*matplotlib.colors.to_rgb(color)) for color in c])
    mask = luminance > text_luminance_threshold
    return [
        "background-color: %s; color: %s" % (color, "black" if m else "white")
        for color, m in zip(c, mask)
    ]
