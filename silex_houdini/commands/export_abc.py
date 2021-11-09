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


class ExportABC(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path},
        "file_name": { "label": "Out filename", "type": pathlib.Path },
        "start_frame": { "label": "start frame", "type": int },
        "end_frame": { "label": "End frame", "type": int }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        
        out_dir: str = parameters.get("file_dir", "D:/")
        file_name: str = parameters.get("file_name")
        out_path: str = f"{out_dir}{os.path.sep}{os.path.sep}{file_name}"

        # Test output path exist
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        
        # get current selection
        if len(hou.selectedNodes()) == 0:
            Dialogs().warn("No nodes selected, please select Sop nodes and retry.")
            raise Exception("No nodes selected, please select Sop nodes and retry.")

        for node in hou.selectedNodes():
            if node.type().category().name() != "Sop":
                Dialogs().warn(f"Action only available with Sop Nodes.\nNode {node.name()} will not be exported!")
                return ""

            # create a temporary ROP node
            abc_rop = hou.node(node.parent().path()).createNode('rop_alembic')
            output_path = os.path.join(out_path,node.name())+".abc"
            abc_rop.parm('filename').set(out_path)

            # Set frame range
            start = parameters.get("start_frame", "$FSTART")
            end = parameters.get("end_frame", "$FEND")

            abc_rop.parm('f1').deleteAllKeyframes()
            abc_rop.parm('f1').set(start)

            abc_rop.parm('f2').deleteAllKeyframes()
            abc_rop.parm('f2').set(end)
            

            # link node to object
            abc_rop.setInput(0, node)
            abc_rop.parm('execute').pressButton()
            
            # remove node
            abc_rop.destroy()
        
        print("Done")
        # export
        return out_dir
    
