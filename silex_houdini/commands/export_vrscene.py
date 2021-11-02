from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_houdini.utils.dialogs import Dialogs


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os

class ExportVrscene(CommandBase):

    parameters = {
    "outpath": { "label": "outpath", "type": str, "value": "" },
    "camera": {
        "type": SelectParameterMeta(
        *[c.path() for c in hou.node("/obj").children() if c.parent().recursiveGlob(c.path(), hou.nodeTypeFilter.ObjCamera)]
        ),
        "value": "No camera"
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        out_path = parameters["outpath"]
        # get current selection
        #if len(hou.selectedNodes()) == 0:
            # Dialogs().warn("No nodes selected, please select Sop nodes and retry.")
            #raise Exception("No nodes selected, please select Sop nodes and retry.")

        # create a temporary ROP node
        vray_renderer = hou.node('/out').createNode('vray_renderer')
        vray_renderer.parm('vobject').set("*")
        vray_renderer.parm('render_export_mode').set("2")
        vray_renderer.parm('render_export_filepath').set(os.path.join(out_path)+".vrscene")

        # link selected camera
        vray_renderer.parm('render_camera').set(parameters["camera"])

        # link node to object
        vray_renderer.parm('execute').pressButton()

        # remove node
        vray_renderer.destroy()

        print("Done")

        # export
        return out_path
