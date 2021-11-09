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
import gazu
import pathlib


class ExportOBJ(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": str, "value": "" },
        "file_name": { "label": "Out filename", "type": str, "value": "" }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        outdir = parameters["file_dir"]
        outfilename = parameters["file_name"]
        
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

            extension = await gazu.files.get_output_type_by_name("Wavefront OBJ")
            temp_outfilename = os.path.join(outdir, f"{outfilename}_{node.name()}")
            final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))
            hou.node(node.path()).geometry().saveToFile(final_filename)
        
        print("Done")
        # export
        logger.info(outdir)
        return outdir
