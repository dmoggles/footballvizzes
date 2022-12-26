from typing import Dict, List
from urllib.error import HTTPError
from PIL import Image
from urllib.request import urlopen
import requests
import json


def get_image_remote(team_name: str, league: str) -> Image:
    url = f"http://www.mclachbot.com/site/img/teams/{league}/{team_name}.png"
    return Image.open(urlopen(url))


def get_mclachhead() -> Image:
    return Image.open(
        urlopen(
            "https://pbs.twimg.com/profile_images/1490059544734703620/7avjgS-D_400x400.jpg"
        )
    )


def sportsdb_image_grabber(team: str, league: str):
    league = league.replace(" ", "%20")
    team = team.replace(" ", "%20")
    url = f"http://www.mclachbot.com:9000/badge_download/{league}/{team}"
    try:
        return Image.open(urlopen(url))
    except HTTPError:
        return None


def sportsdb_league_image_grabber(league: str):
    league = league.replace(" ", "%20")

    url = f"http://www.mclachbot.com:9000/league_badge_download/{league}"
    try:
        return Image.open(urlopen(url))
    except HTTPError:
        return None


def get_rainbow_image(version=""):
    image = Image.open(urlopen(f"http://mclachbot.com/site/img/rainbow{version}.png"))
    return image


def team_colours(
    team: str,
    league: str,
    existing_map: Dict[str, List[str]] = None,
    default_colours: List[str] = None,
) -> List[str]:
    default_colours = default_colours or ["#bbbbbb", "#000000"]
    existing_map = existing_map or {}

    league = league.replace(" ", "%20")
    team = team.replace(" ", "%20")
    url = f"http://www.mclachbot.com:9000/colours/{league}/{team}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            colours = json.loads(r.text)
            if not colours[0]:
                return default_colours
            return colours
        else:
            return default_colours

    except HTTPError:
        return None


def get_twitter_image():
    image = Image.open(urlopen("http://mclachbot.com/site/img/twitter.png"))
    return image


def get_insta_image():
    image = Image.open(urlopen("http://mclachbot.com/site/img/instagram.webp"))
    return image
