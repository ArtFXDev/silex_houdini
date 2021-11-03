from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_houdini.utils.dialogs import Dialogs


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu


class ExportFBX(CommandBase):

    parameters = {
        "outdir": { "label": "Out directory", "type": str, "value": "" },
        "outfilename": { "label": "Out filename", "type": str, "value": "" }
    }
    
    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        outdir = parameters["outdir"]
        outfilename = parameters["outfilename"]

        # Test output path exist
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # get current selection
        if len(hou.selectedNodes()) == 0:
            Dialogs().warn("No nodes selected, please select Sop nodes and retry.")
            raise Exception("No nodes selected, please select Sop nodes and retry.")
        for node in hou.selectedNodes():
            if node.type().category().name() != "Sop":
                Dialogs().warn(f"Action only available with Sop Nodes.\nNode {node.name()} will not be exported!")
                return ""

            # create a temporary ROP node
            extension = await gazu.files.get_output_type_by_name("Autodesk FBX")
            outfilename = os.path.join(outdir, outfilename, node.name())
            final_filename = str(pathlib.Path(outfilename).with_suffix(f".{extension['short_name']}"))
            fbx_rop = hou.node(node.parent().path()).createNode('rop_fbx')
            fbx_rop.parm('sopoutput').set(final_filename)

            # link node to object
            fbx_rop.setInput(0, node)
            fbx_rop.parm('execute').pressButton()

            # remove node
            fbx_rop.destroy()
        
        print("Done")

        # export
        return final_filename
