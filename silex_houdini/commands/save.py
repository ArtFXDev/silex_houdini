from __future__ import annotations
import typing
import pathlib
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_houdini.utils.utils import Utils

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
        "file_path": {"label": "filename", "type": str, "value": None, "hide": False},
        "only_path": {
            "label": "Only set the path",
            "type": bool,
            "value": False,
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_path: pathlib.Path = parameters["file_path"]

        logger.info("Saving scene to %s", file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Set the right extension according to the license type
        extension_mapping = {
            hou.licenseCategoryType.Apprentice: ".hipnc",
            hou.licenseCategoryType.Education: ".hipnc",
            hou.licenseCategoryType.ApprenticeHD: ".hipnc",
            hou.licenseCategoryType.Indie: ".hiplc",
            hou.licenseCategoryType.Commercial: ".hip",
        }
        file_path = pathlib.Path(
            os.path.splitext(file_path)[0]
            + extension_mapping.get(hou.licenseCategory(), ".hip")
        )
        file_name = file_path.as_posix()

        await Utils.wrapped_execute(
            action_query, hou.hipFile.setName, file_name=file_name
        )
        if not parameters["only_path"]:
            await Utils.wrapped_execute(
                action_query, hou.hipFile.save, file_name=file_name
            )

        return {"new_path": file_name}
