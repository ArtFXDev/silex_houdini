from __future__ import annotations
import typing
from typing import Any, Dict
import logging

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou


class SetUpdateMode(CommandBase):
    """
    Change the update mode
    """

    parameters = {
        "mode": {
            "label": "Attributes",
            "type": SelectParameterMeta("Auto", "On Mouse Up", "Manual"),
            "value": "Auto",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        mode: str = parameters["mode"]

        update_mode_mapping = {
            "Auto": hou.updateMode.AutoUpdate,
            "On Mouse Up": hou.updateMode.OnMouseUp,
            "Manual": hou.updateMode.Manual,
        }

        logger.info(
            "Setting the update mode to %s", update_mode_mapping.get(mode, "Auto")
        )
        hou.setUpdateMode(update_mode_mapping.get(mode, "Auto"))
