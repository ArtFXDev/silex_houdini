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
            print("aaaa")
            out_path = parameters.get("outpath", "D:/")
            # Test output path exist
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            
            # get current selection
            for node in hou.selectedNodes():
                print(node.path())
                print(node.type())
                hou.node(node).geometry().saveToFile(out_path)

            print("aaaaa")

            # export
            return out_path
    
        await export()
