from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_houdini.utils.dialogs import Dialogs
from silex_client.utils.log import logger
from silex_client.action.parameter_buffer import ParameterBuffer

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import gazu
import pathlib


class ExportOBJ(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path, "value": "" },
        "file_name": { "label": "Out filename", "type": pathlib.Path, "value": "" },
        "root_name": { "label": "Out Object Name", "type": str, "value": None, "hide": False }
    }

    async def _prompt_label_parameter(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="warning_parameter",
            label="No nodes selected, please select Object nodes and retry."
        )

        # Prompt the user with a label
        label = await self.prompt_user(
            action_query,
            { "label": label_parameter }
        )
        return label["label"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        outdir = parameters["file_dir"]
        outfilename = parameters["file_name"]
        root_name = parameters.get("root_name")

        selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Sop" ]

        # get current selection
        while len(selected_object) == 0:
            await self._prompt_label_parameter(action_query)
            selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Sop" ]

        # Test output path exist
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        
        # create temp root node
        merge_sop = hou.node(selected_object[0].parent().path()).createNode("merge")
        for node in selected_object:
            merge_sop.setNextInput(node)

        extension = await gazu.files.get_output_type_by_name("obj")
        temp_outfilename = outdir / f"{outfilename}_{root_name}"
        final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))
        hou.node(merge_sop.path()).geometry().saveToFile(final_filename)

        # remove temp_subnet
        merge_sop.destroy()

        # export
        logger.info(f"Done export obj, output paths : {final_filename}")
        return final_filename
