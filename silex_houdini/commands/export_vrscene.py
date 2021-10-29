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

parameters = {
    "outpath": { "label": "outpath", "type": str, "value": "", "hide": False }
}

class ExportVrscene(CommandBase):
    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        out_path = parameters.get("outpath", "D:/")

        # Test output path exist
        if not os.path.exists(out_path):
            os.makedirs(out_path)

        # get current selection
        if len(hou.selectedNodes()) == 0:
            Dialogs().warn("No nodes selected, please select Sop nodes and retry.")
            raise Exception("No nodes selected, please select Sop nodes and retry.")

        # create a temporary ROP node
        vray_renderer = hou.node("/out").createNode('vray_renderer')
        vray_renderer.parm('vobject').set("*")
        vray_renderer.parm('render_export_mode').set("Export")
        out_path += "qqqqq.vrscene"
        vray_renderer.parm('vobject').set(os.path.join(out_path)+".vrscene")

        # link node to object
        vray_renderer.parm('execute').pressButton()

        # remove node
        vray_renderer.destroy()

        print("Done")

        # export
        return out_path
