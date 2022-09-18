from footmav.data_definitions.whoscored.constants import EventType
from tabulate import tabulate


def convert_player_name_for_display(name):
    tokens = name.split(" ")
    if len(tokens) == 1:
        return name.title()
    else:
        return " ".join(
            [" ".join([f"{t[0].upper()}." for t in tokens[:1]]), tokens[-1].title()]
        )


def lineup_card(data):

    lineup_card = (
        data[["shirt_number", "player_name", "position"]]
        .groupby(["shirt_number"])
        .first()
        .reset_index()
    )
    lineup_card = lineup_card.loc[lineup_card["shirt_number"] != -1]
    subs = (
        data.loc[data["event_type"] == EventType.SubstitutionOn][
            ["player_name", "minute", "second"]
        ]
        .set_index("player_name")
        .to_dict()["minute"]
    )
    subs_off = (
        data.loc[data["event_type"] == EventType.SubstitutionOff][
            ["player_name", "minute", "second"]
        ]
        .set_index("player_name")
        .to_dict()["minute"]
    )
    lineup_card["on"] = lineup_card["player_name"].map(subs).fillna(0).astype(int)
    lineup_card["is_position"] = lineup_card["position"].apply(
        lambda x: 1 if x != "GK" else 0
    )
    lineup_card["off"] = (
        lineup_card["player_name"].map(subs_off).fillna(0).astype(int).astype(str)
    )
    lineup_card["off"] = lineup_card["off"].apply(lambda x: x if x != "0" else "--")
    lineup_card["player_name"] = lineup_card["player_name"].apply(
        convert_player_name_for_display
    )
    lineup_card = lineup_card.sort_values(["is_position", "on", "shirt_number"])
    lineup_card = lineup_card.rename(
        columns={
            "player_name": "Player",
            "position": "Pos",
            "shirt_number": "No.",
            "on": "On",
            "off": "Off",
        }
    )
    starters = lineup_card.loc[lineup_card["On"] == 0]
    subs = lineup_card.loc[lineup_card["On"] != 0]
    subs = subs.sort_values("On")
    subs["On"] = subs["On"].astype(str)

    return (
        tabulate(
            starters[["Pos", "Player", "No.", "Off"]],
            headers="keys",
            showindex=False,
            tablefmt="pretty",
        ),
        tabulate(
            subs[["Pos", "Player", "No.", "On"]],
            headers="keys",
            showindex=False,
            tablefmt="pretty",
        ),
    )
