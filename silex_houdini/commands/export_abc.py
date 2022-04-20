from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta, TextParameterMeta

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
        "timeline_as_framerange": {
            "label": "Use timeline as frame-range",
            "type": bool,
            "value": False,
            "hide": False,
        },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0],
        },
        "multiple_files": {
            "label": "Export as file sequence",
            "type": bool,
            "value": False,
        },
    }

    async def _prompt_info_parameter(
        self, action_query: ActionQuery, message: str, level: str = "warning"
    ) -> pathlib.Path:
        """
        Helper to prompt the user a label
        """
        # Create a new parameter to prompt label

        info_parameter = ParameterBuffer(
            type=TextParameterMeta(level),
            name="Info",
            label="Info",
            value=f"Warning : {message}",
        )
        # Prompt the user with a label
        prompt = await self.prompt_user(action_query, {"info": info_parameter})

        return prompt["info"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        outdir = parameters["file_dir"]
        outfilename = parameters["file_name"]
        multiple_files: bool = parameters["multiple_files"]
        used_timeline = parameters["timeline_as_framerange"]
        start_frame = parameters["frame_range"][0]
        end_frame = parameters["frame_range"][1]

        def export_abc(selected_object, final_filename, start_frame, end_frame):
            # create a temporary ROP node
            abc_out = hou.node("/out").createNode("alembic")
            abc_out.parm("filename").set(final_filename)

            # the exported nodes can be either SOP or OBJ
            if hou.node(selected_object[0]).type().category().name() == "Sop":
                # in the case of SOP nodes, only one node can be exported
                abc_out.parm("use_sop_path").set(True)
                abc_out.parm("sop_path").set(selected_object[0])
            else:
                abc_out.parm("objects").set(" ".join(selected_object))

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
            if item.type().category().name() in ["Object", "Sop"]
        ]

        # Test/update current selection
        while len(selected_object) == 0:
            await self._prompt_info_parameter(
                action_query,
                "No OBJ or SOP nodes selected,\n please select OBJ or SOP nodes and continue.",
            )
            selected_object = [
                item.path()
                for item in hou.selectedNodes()
                if item.type().category().name() in ["Object", "Sop"]
            ]

        # Test output path exist
        os.makedirs(outdir, exist_ok=True)

        # compute final path
        extension = await gazu.files.get_output_type_by_name("abc")
        temp_outfilename = outdir / f"{outfilename}"

        if multiple_files:
            temp_outfilename = temp_outfilename.parent / (temp_outfilename.name + ".$F4")

        final_filename = str(
            temp_outfilename.parent / (temp_outfilename.name + f".{extension['short_name']}")
        )

        # Set frame range
        if used_timeline:
            range_playbar = hou.playbar.frameRange()
            start_frame = range_playbar.x()
            end_frame = range_playbar.y()

        await Utils.wrapped_execute(
            action_query,
            export_abc,
            selected_object,
            final_filename,
            start_frame,
            end_frame,
        )

        # export
        logger.info(f"Done export abc, output paths : {final_filename}")
        if multiple_files:
            return outdir
        return final_filename

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["frame_range"].hide = parameters.get(
            "timeline_as_framerange"
        )
