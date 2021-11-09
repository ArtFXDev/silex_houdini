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
import pathlib
import gazu

class ExportVrscene(CommandBase):

    parameters = {
    "file_dir": { "label": "Out directory", "type": str, "value": "" },
    "file_name": { "label": "Out filename", "type": str, "value": "" },
    "framerange": { "label": "Take timeline as frame-range?", "type": bool, "value": False },
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

        outdir = parameters["file_dir"]
        outFilename = parameters["file_name"]

        # create out dir if not exist
        if not os.path.exists(outdir):
                os.makedirs(outdir)

        # create a temporary ROP node
        vray_renderer = hou.node('/out').createNode('vray_renderer')
        vray_renderer.parm('vobject').set("*")
        vray_renderer.parm('render_export_mode').set("2")
        final_filename = os.path.join(outdir, outFilename)
        
        extension = await gazu.files.get_output_type_by_name("V-Ray Scene File")
        final_filename = str(pathlib.Path(final_filename).with_suffix(f".{extension['short_name']}"))

        vray_renderer.parm("render_export_filepath").set(final_filename)

        # link selected camera
        vray_renderer.parm("render_camera").set(parameters["camera"])

        # Set frame range
        if parameters["framerange"]:
            vray_renderer.parm("trange").set(1)

            range_playbar = hou.playbar.frameRange()
            vray_renderer.parm("f1").set(range_playbar.x())
            vray_renderer.parm("f2").set(range_playbar.y())
            vray_renderer.parm("f3").set(1)

        # Render
        vray_renderer.parm('execute').pressButton()

        # remove node
        vray_renderer.destroy()

        print("Done")

        # export
        return final_filename
