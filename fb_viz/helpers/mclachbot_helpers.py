from PIL import Image
from urllib.request import urlopen


def get_image_remote(team_name: str, league: str) -> Image:
    url = f"http://www.mclachbot.com/site/img/teams/{league}/{team_name}.png"
    return Image.open(urlopen(url))


def get_mclachhead() -> Image:
    return Image.open(
        urlopen(
            "https://pbs.twimg.com/profile_images/1490059544734703620/7avjgS-D_400x400.jpg"
        )
    )
