from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_houdini.utils.dialogs import Dialogs
from silex_client.utils.log import logger
from silex_client.utils.parameter_types import IntArrayParameterMeta


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu


class ExportABC(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path},
        "file_name": { "label": "Out filename", "type": pathlib.Path },
        "frame_range": {
            "label": "IntArray Tester",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0]
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        outdir: str = parameters.get("file_dir")
        outfilename: str = parameters.get("file_name")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]

        to_return_paths = []
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
            abc_rop = hou.node(node.parent().path()).createNode('rop_alembic')

            # compute final path
            extension = await gazu.files.get_output_type_by_name("alembic")
            temp_outfilename = os.path.join(outdir, f"{outfilename}_{node.name()}")
            final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))
            
            abc_rop.parm('filename').set(final_filename)

            # append to return
            to_return_paths.append(final_filename)

            # Set frame range
            abc_rop.parm("trange").set(1)
            abc_rop.parmTuple("f").deleteAllKeyframes() # Needed
            abc_rop.parmTuple('f').set((start_frame, end_frame, 0))

            # link node to object
            abc_rop.setInput(0, node)
            abc_rop.parm('execute').pressButton()
            
            # remove node
            abc_rop.destroy()

        # export
        logger.info(f"Done export abc, output paths : {to_return_paths}")
        return to_return_paths
