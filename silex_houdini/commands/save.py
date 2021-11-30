from __future__ import annotations
import typing
import pathlib
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import hou

class Save(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
        "file_path": {"label": "filename", "type": str, "value": None, "hide": False}
    }
    
    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        file_path: pathlib.Path = parameters["file_path"]

        logger.info("Saving scene to %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        hou.hipFile.save(file_name=file_path)

        return {"new_path": file_path}
