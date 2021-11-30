from __future__ import annotations
import typing
import logging
from typing import Any, Dict

import pathlib
from silex_client.action.command_base import CommandBase
from silex_houdini.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou


class Open(CommandBase):
    """
    Open the given scene file
    """

    parameters = {
        "file_path": {
            "label": "filename",
            "type": pathlib.Path,
            "value": None,
        },
        "save": {
            "label": "Save before opening",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        file_path: pathlib.Path = parameters["file_path"]
        save_before_open: bool = parameters["save"]

        # First get the current file name
        current_file = pathlib.Path(hou.hipFile.path())

        # Test if the scene that we have to open exists
        if not file_path.exists():
            logger.error("Could not open %s: The file does not exists", file_path)
            return {"old_path": current_file, "new_path": current_file}

        # Check if there is some modifications to save
        file_state: bool = hou.hipFile.hasUnsavedChanges()
        # Save the current scene before openning a new one
        if file_state and save_before_open:
            await Utils.wrapped_execute(action_query, hou.hipFile.save)
        logger.info("Openning file %s", file_path)

        await Utils.wrapped_execute(action_query, hou.hipFile.load, file_path.as_posix(), suppress_save_prompt=True)
        return {"old_path": current_file, "new_path": parameters["file_path"]}
