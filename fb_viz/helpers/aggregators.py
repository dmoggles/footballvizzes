from footmav.utils import whoscored_funcs as WF
from footmav.event_aggregation.event_aggregator_processor import event_aggregator
from footmav.event_aggregation.aggregators import (
    touches,
    xa,
    npxg,
    crosses,
    open_play_balls_into_box,
    ground_duels_won,
    aerials,
    ground_duels_lost,
)
from footmav.data_definitions.whoscored.constants import EventType

import numpy as np


@event_aggregator(suffix="")
def progressive_pass_distance(dataframe):
    return np.maximum(
        0,
        np.nan_to_num(
            WF.progressive_distance(dataframe)
            * (dataframe["event_type"] == EventType.Pass)
            * (dataframe["outcomeType"] == 1),
            0,
        ),
    )


@event_aggregator(suffix="")
def progressive_carry_distance(dataframe):
    return np.maximum(
        0,
        np.nan_to_num(
            WF.progressive_distance(dataframe)
            * (dataframe["event_type"] == EventType.Carry)
            * (dataframe["outcomeType"] == 1),
            0,
        ),
    )


@event_aggregator(suffix="")
def open_play_passes_completed_into_the_box(dataframe):
    return (
        (dataframe["event_type"] == EventType.Pass)
        & (WF.col_has_qualifier(dataframe, qualifier_code=2))  # not cross
        & (~WF.col_has_qualifier(dataframe, qualifier_code=5))  # not free kick
        & (~WF.col_has_qualifier(dataframe, qualifier_code=6))  # not corner
        & (~WF.col_has_qualifier(dataframe, qualifier_code=107))  # not throw in
        & (~WF.col_has_qualifier(dataframe, qualifier_code=123))  # not keeper throw
        & (WF.into_attacking_box(dataframe))
    )


@event_aggregator(suffix="")
def crosses_completed_into_the_box(dataframe):
    return crosses.success(dataframe) & WF.in_attacking_box(dataframe)


@event_aggregator(suffix="")
def carries_into_the_box(dataframe):
    return (dataframe["event_type"] == EventType.Carry) & WF.into_attacking_box(
        dataframe
    )
