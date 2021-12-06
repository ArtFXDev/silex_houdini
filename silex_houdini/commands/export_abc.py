from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta
from silex_houdini.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu


class ExportABC(CommandBase):

    parameters = {
        "file_dir": {"label": "Out directory", "type": pathlib.Path},
        "file_name": {"label": "Out filename", "type": pathlib.Path},
        "root_name": {
            "label": "Out Object Name",
            "type": str,
            "value": "",
            "hide": False,
        },
        "timeline_as_framerange": {
            "label": "Take framerange frame-range?",
            "type": bool,
            "value": False,
            "hide": False,
        },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0],
        },
    }

    async def _prompt_label_parameter(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="label_parameter",
            label="No nodes selected, please select Object nodes and retry.",
        )

        # Prompt the user with a label
        label = await self.prompt_user(action_query, {"label": label_parameter})

        return label["label"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        outdir = parameters.get("file_dir")
        outfilename = parameters.get("file_name")
        root_name = parameters.get("root_name")
        used_timeline = parameters.get("timeline_as_framerange")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]

        def export_abc(selected_object, final_filename, start_frame, end_frame):
            # create a temporary ROP node
            abc_out = hou.node("/out").createNode("alembic")
            abc_out.parm("filename").set(final_filename)
            abc_out.parm("objects").set(selected_object)

            # Set frame range
            abc_out.parm("trange").set(1)
            abc_out.parmTuple("f").deleteAllKeyframes()  # Needed
            abc_out.parmTuple("f").set((start_frame, end_frame, 0))

            # link node to object
            abc_out.parm("execute").pressButton()

            # remove node
            abc_out.destroy()

        # get current selection
        selected_object = [
            item.path()
            for item in hou.selectedNodes()
            if item.type().category().name() == "Object"
        ]
        # Test/update current selection
        while len(selected_object) == 0:
            await self._prompt_label_parameter(action_query)
            selected_object = [
                item.path()
                for item in hou.selectedNodes()
                if item.type().category().name() == "Object"
            ]

        # get list of name ofcurrent selection
        selected_object = " ".join(selected_object)

        # Test output path exist
        os.makedirs(outdir, exist_ok=True)

        # compute final path
        extension = await gazu.files.get_output_type_by_name("abc")
        temp_outfilename = (
            outdir / f"{outfilename}_{root_name}"
            if root_name
            else outdir / f"{outfilename}"
        )

        final_filename = str(
            pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}")
        )

        # Set frame range
        if used_timeline:
            range_playbar = hou.playbar.frameRange()
            start_frame = range_playbar.x()
            end_frame = range_playbar.y()

        await Utils.wrapped_execute(action_query, export_abc, selected_object, final_filename, start_frame, end_frame)

        # export
        logger.info(f"Done export abc, output paths : {final_filename}")
        return final_filename
