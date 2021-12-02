from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import gazu.files
import gazu.task
import re
import hou


class Build(CommandBase):
    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        async def get_scene_path():
            # task = await gazu.task.get_task(action_query.context_metadata.get("task_id", "ac0e79cf-e5ce-49ff-932f-6aed3d425e4a"))
            task_id = action_query.context_metadata.get("task_id", "none")
            working_file_with_extension = await gazu.files.build_working_file_path(
                task_id
            )
            if task_id == "none":
                return -1, None

            current_soft = {
                hou.licenseCategoryType.Commercial: "houdini",
                hou.licenseCategoryType.Indie: "hindie",
                hou.licenseCategoryType.Apprentice: "happrentice",
            }

            soft = await gazu.files.get_software_by_name(
                current_soft.get(hou.licenseCategory(), "houdini")
            )
            if not soft:
                return -1, None
            extension = soft.get("file_extension", ".no")
            extension = extension if "." in extension else f".{extension}"
            working_file_with_extension += extension

            return working_file_with_extension, extension

        async def build():

            # create recusively directory from path
            working_file_with_extension, ext = await get_scene_path()

            # error in future
            if working_file_with_extension == -1 or not ext:
                return

            filename = os.path.basename(working_file_with_extension)
            working_file_without_extension = os.path.splitext(filename)[0]
            working_folders = os.path.dirname(working_file_with_extension)

            # if file already exist
            version = re.findall("[0-9]*$", working_file_without_extension)
            version = (
                version[0] if len(version) > 0 else ""
            )  # get last number of file name
            zf = len(version)
            version = int(version)

            # error in future
            if version == "":
                return

            file_without_version = re.findall(
                "(?![0-9]*$).", working_file_without_extension
            )
            file_without_version = "".join(file_without_version)
            while os.path.exists(working_file_with_extension):
                version += 1
                working_file_with_extension = os.path.join(
                    working_folders,
                    f"{file_without_version}{str(version).zfill(zf)}{ext}",
                )

            if not os.path.exists(working_folders):
                os.makedirs(working_folders)
            hou.hipFile.save(file_name=working_file_with_extension)

        await build()
