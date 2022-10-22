import os
import matplotlib.font_manager as fm


def get_url(file_name):
    return os.path.join(os.path.dirname(__file__), "../..", "font_files", file_name)


class FontManagerLocal:
    def __init__(self, path):
        self._prop = fm.FontProperties(fname=path)

    @property
    def prop(self):
        return self._prop


font_normal = FontManagerLocal(
    get_url("roboto_normal.ttf"),
)
font_italic = FontManagerLocal(get_url("roboto_italic.ttf"))
font_bold = FontManagerLocal(
    get_url("roboto_bold.ttf"),
)

font_mono = FontManagerLocal(
    get_url("roboto_mono.ttf"),
)
