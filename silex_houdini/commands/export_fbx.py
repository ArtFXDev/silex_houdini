from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_houdini.utils.dialogs import Dialogs
from silex_client.utils.log import logger


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu

class ExportFBX(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": str, "value": "" },
        "file_name": { "label": "Out filename", "type": str, "value": "" },
        "root_name": { "label": "Out Object Name", "type": str, "value": None, "hide": False }
    }
    
    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        outdir = parameters["file_dir"]
        outfilename = parameters["file_name"]
        root_name = parameters["root_name"]

        # Test output path exist
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # get current selection
        if len(hou.selectedNodes()) == 0:
            Dialogs().warn("No nodes selected, please select Sop nodes and retry.")
            raise Exception("No nodes selected, please select Sop nodes and retry.")

        selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Object" ]
        selected_name = [item.name() for item in selected_object ]
        logger.info(selected_object)
        
        # create a temporary ROP node
        extension = await gazu.files.get_output_type_by_name("fbx")
        temp_outfilename = os.path.join(outdir, f"{outfilename}_{root_name}")
        final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))
        
        # create temp filmboxfbx
        fbx_rop = hou.node("out").createNode('filmboxfbx')
        fbx_rop.parm('sopoutput').set(final_filename)

        # create temp root node
        temp_subnet = hou.node("obj").createNode("subnet")
        hou.moveNodesTo(selected_object, temp_subnet)
        
        # past temp_subnet in export fbx 
        fbx_rop.parm("startnode").set(temp_subnet.path())
        
        # link node to object
        fbx_rop.parm("execute").pressButton()

        # remove node
        fbx_rop.destroy()

        selected = [hou.node(f"{temp_subnet.path()}/{item}") for item in selected_name]
        hou.moveNodesTo(selected, hou.node("/obj/"))

        # export
        logger.info(f"Done export fbx, output paths : {final_filename}")
        return final_filename
