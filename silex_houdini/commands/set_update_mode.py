from __future__ import annotations
import typing
from typing import Any, Dict
import logging

from silex_houdini.utils.utils import Utils
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
        current_mode = await Utils.wrapped_execute(action_query, hou.updateModeSetting)
        current_mode = await current_mode
        new_mode = update_mode_mapping.get(mode, "Auto")
        await Utils.wrapped_execute(action_query, hou.setUpdateMode, new_mode)

        previous_mode_key = next(
            key for key, value in update_mode_mapping.items() if value == current_mode
        )
        new_mode_key = next(
            key for key, value in update_mode_mapping.items() if value == new_mode
        )
        return {
            "previous_mode": previous_mode_key,
            "new_mode": new_mode_key,
        }
