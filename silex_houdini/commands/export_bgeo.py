from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import gazu
import pathlib
import logging


class ExportBGEO(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path, "value": "" },
        "file_name": { "label": "Out filename", "type": pathlib.Path, "value": "" },
        "timeline_as_framerange": { "label": "Take framerange frame-range?", "type": bool, "value": False, "hide": False },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0]
        }
    }

    async def _prompt_label_parameter(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="label_parameter",
            label="No nodes selected, please select Sop nodes and retry."
        )

        # Prompt the user with a label
        label = await self.prompt_user(
            action_query,
            { "label": label_parameter }
        )
        return label["label"]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        outdir = parameters.get("file_dir")
        outfilename = parameters.get("file_name")
        root_name = parameters.get("root_name")
        used_timeline = parameters.get("timeline_as_framerange")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]

        # get current selection
        selected_object = [item.path() for item in hou.selectedNodes() if item.type().category().name() == "Sop" ]
        while len(selected_object) == 0:
            await self._prompt_label_parameter(action_query)
            selected_object = [item.path() for item in hou.selectedNodes() if item.type().category().name() == "Sop" ]     

        # get current selection
        while len(selected_object) == 0:
            await self._prompt_label_parameter(action_query)
            selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Sop" ]

        # Test output path exist
        os.makedirs(outdir, exist_ok=True)
        # Set frame range
        if used_timeline:
            range_playbar = hou.playbar.frameRange()
            start_frame = range_playbar.x()
            end_frame = range_playbar.y()

        # create temp root node
        merge_sop = hou.node(hou.node(selected_object[0]).parent().path()).createNode("merge")
        for node in selected_object:
            node = hou.node(node)
            merge_sop.setNextInput(node)

        # create rop output
        rop_output = hou.node(merge_sop.parent().path())
        rop_output = rop_output.createNode("rop_geometry")
        rop_output.setInput(0, merge_sop)

        # set frame range
        rop_output.parm("trange").set(1)
        rop_output.parmTuple("f").deleteAllKeyframes() # Needed
        rop_output.parmTuple("f").set((start_frame, end_frame, 0))

        # compute final name
        extension = await gazu.files.get_output_type_by_name("bgeo")
        temp_outfilename = outdir / f"{outfilename}_{root_name}_$F4" if root_name else outdir / f"{outfilename}_$F4"
        final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))

        # register final path
        rop_output.parm("sopoutput").set(final_filename)

        # execute
        rop_output.parm("execute").pressButton()

        # remove temp_subnet
        merge_sop.destroy()
        rop_output.destroy()

        logger.info(f"Done export obj, output paths : {outdir}")
        return str(outdir)
