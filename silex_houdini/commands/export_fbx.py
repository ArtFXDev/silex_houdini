from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.action.parameter_buffer import ParameterBuffer

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu


class ExportFBX(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path, "value": "" },
        "file_name": { "label": "Out filename", "type": pathlib.Path, "value": "" },
        "root_name": { "label": "Out Object Name", "type": str, "value": "", "hide": False },
    }
    
    async def _prompt_label_parameter(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user a labelb
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="label_parameter",
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

        outdir = parameters.get("file_dir")
        outfilename = parameters.get("file_name")
        root_name = parameters.get("root_name")

        # get current selection
        while len(hou.selectedNodes()) == 0:
            await self._prompt_label_parameter(action_query)

        # Test output path exist
        os.makedirs(outdir, exist_ok=True)

        selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Object" ]
        selected_name = [item.name() for item in selected_object ]

        # create a temporary ROP node
        extension = await gazu.files.get_output_type_by_name("fbx")
        temp_outfilename = outdir / f"{outfilename}_{root_name}" if root_name else outdir / f"{outfilename}"
        final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))

        # create temp filmboxfbx
        fbx_rop = hou.node("out").createNode("filmboxfbx")
        fbx_rop.parm("sopoutput").set(final_filename)
        fbx_rop.parm("createsubnetroot").set(0)

        # create temp root node
        temp_subnet = hou.node("obj").createNode("subnet")
        hou.moveNodesTo(selected_object, temp_subnet)

        # past temp_subnet in export fbx 
        fbx_rop.parm("startnode").set(temp_subnet.path())
        
        # link node to object
        fbx_rop.parm("execute").pressButton()

        # remove fbx export
        fbx_rop.destroy()
        
        # reup node in temp_subnet into /obj
        selected = [hou.node(f"{temp_subnet.path()}/{item}") for item in selected_name]
        hou.moveNodesTo(selected, hou.node("/obj/"))

        # remove temp_subnet
        temp_subnet.destroy()

        # export
        logger.info(f"Done export fbx, output paths : {final_filename}")
        return final_filename

    @CommandBase.conform_command()
    async def __undo__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        outdir = parameters.get("file_dir")
