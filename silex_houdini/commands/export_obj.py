from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta
from silex_houdini.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import gazu
import pathlib


class ExportOBJ(CommandBase):

    parameters = {
        "file_dir": {"label": "Out directory", "type": pathlib.Path, "value": ""},
        "file_name": {"label": "Out filename", "type": pathlib.Path, "value": ""},
        "root_name": {
            "label": "Out Object Name",
            "type": str,
            "value": "",
            "hide": False,
        },
    }

    async def _prompt_info_parameter(
        self, action_query: ActionQuery, message: str, level: str = "warning"
    ) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        info_parameter = ParameterBuffer(
            type=TextParameterMeta(level),
            name="Info",
            label="Info",
            value=f"Warning : {message}",
        )
        # Prompt the user with a label
        prompt = await self.prompt_user(action_query, {"info": info_parameter})

        return prompt["info"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        outdir = parameters.get("file_dir")
        outfilename = parameters.get("file_name")
        root_name = parameters.get("root_name")

        def export_obj(selected_object, final_filename):
            merge_sop = hou.node(selected_object[0].parent().path()).createNode("merge")

            # create temp root node
            for node in selected_object:
                merge_sop.setNextInput(node)
            # Test output path exist
            os.makedirs(outdir, exist_ok=True)

            hou.node(merge_sop.path()).geometry().saveToFile(final_filename)

            # remove temp_subnet
            merge_sop.destroy()

        selected_object = [
            item
            for item in hou.selectedNodes()
            if item.type().category().name() == "Sop"
        ]

        # get current selection
        while len(selected_object) == 0:
            await self._prompt_info_parameter(
                action_query,
                "No nodes selected,\n please select Sop nodes and continue.",
            )
            selected_object = [
                item
                for item in hou.selectedNodes()
                if item.type().category().name() == "Sop"
            ]

        extension = await gazu.files.get_output_type_by_name("obj")
        temp_outfilename = (
            outdir / f"{outfilename}_{root_name}"
            if root_name
            else outdir / f"{outfilename}"
        )

        final_filename = str(
            pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}")
        )
        await Utils.wrapped_execute(
            action_query, export_obj, selected_object, final_filename
        )

        # export
        logger.info(f"Done export obj, output paths : {final_filename}")
        return final_filename
