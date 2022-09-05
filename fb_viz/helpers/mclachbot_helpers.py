from PIL import Image
from urllib.request import urlopen


def get_image_remote(team_name: str, league: str) -> Image:
    url = f"http://www.mclachbot.com/site/img/teams/{league}/{team_name}.png"
    return Image.open(urlopen(url))
