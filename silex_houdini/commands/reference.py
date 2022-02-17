from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.utils.files import expand_path, find_sequence_from_path
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import pathlib


class Reference(CommandBase):
    """
    Prompt for a publish file and return the expanded information about that publish
    """

    parameters = {
        "reference": {
            "label": "Reference file",
            "type": TaskFileParameterMeta(),
            "hide": False,
        },
        "find_sequence": {
            "label": "Find sequence",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_path: pathlib.Path = parameters["reference"]
        find_sequence: bool = parameters["find_sequence"]
        
        expanded_path = expand_path(file_path)
        sequence = find_sequence_from_path(file_path)
        formated_path = file_path
        if find_sequence and len(sequence) > 1:
            padding = sequence._zfill
            formated_path = sequence.format("{dirname}{basename}" + f"$F{padding}" + "{extension}")
        return {"file_path": file_path, "formated_path": formated_path, **expanded_path}
