from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os

parameters = {
    "outpath": { "label": "outpath", "type": str, "value": "", "hide": False }
}

class ExportFBX(CommandBase):

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        async def export():
            out_path = parameters.get("outpath", "D:/")
            # Test output path exist
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            
            # get current selection
            for node in hou.selectedNodes():
                print(node.type())
                # create a temporary ROP node
                fbx_rop = hou.node(node.parent().path()).createNode('rop_fbx')
                fbx_rop.parm('sopoutput').set(os.path.join(out_path,node.name())+".fbx")

                # link node to object
                fbx_rop.setInput(0, node)
                fbx_rop.parm('execute').pressButton()
                
                # remove node
                fbx_rop.destroy()

            # export
            return out_path
    
        await export()
