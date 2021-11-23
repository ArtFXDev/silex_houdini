from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import IntArrayParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu


class ExportFBX(CommandBase):

    parameters = {
        "file_dir": { "label": "Out directory", "type": pathlib.Path, "value": "" },
        "file_name": { "label": "Out filename", "type": pathlib.Path, "value": "" },
        "root_name": { "label": "Out Object Name", "type": str, "value": "", "hide": False },
        "timeline_as_framerange": { "label": "Take framerange frame-range?", "type": bool, "value": False, "hide": False },
        "frame_range": {
            "label": "Frame Range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 0]
        }
    }

    async def _prompt_label_parameter(self, action_query: ActionQuery, message: str) -> pathlib.Path:
        """
        Helper to prompt the user a labelb
        """
        # Create a new parameter to prompt label

        label_parameter = ParameterBuffer(
            type=str,
            name="label_parameter",
            label=f"{message}"
        )

        # Prompt the user with a label
        label = await self.prompt_user(
            action_query,
            { "label": label_parameter }
        )

        return label["label"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        outdir = parameters.get("file_dir")
        outfilename = parameters.get("file_name")
        root_name = parameters.get("root_name")
        used_timeline = parameters.get("timeline_as_framerange")
        start_frame = parameters.get("frame_range")[0]
        end_frame = parameters.get("frame_range")[1]

        # get current selection
        while len(hou.selectedNodes()) == 0:
            await self._prompt_label_parameter(action_query, "No nodes selected, please select Object nodes and retry.")

        # get time dependent nodes
        time_dependents = [node.name() for  node in hou.selectedNodes() if len(node.subnetOutputs()) > 0 and node.subnetOutputs()[0].isTimeDependent()]
        while len(time_dependents) > 0:
            await self._prompt_label_parameter(action_query, f"Animation cannot be made in SOP level for objects : {time_dependents}")
            time_dependents = [node.name() for  node in hou.selectedNodes() if len(node.subnetOutputs()) > 0 and node.subnetOutputs()[0].isTimeDependent()]

        # Test output path exist

        selected_object = [item for item in hou.selectedNodes() if item.type().category().name() == "Object" ]
        selected_name = [item.name() for item in selected_object ]

        # create a temporary ROP node
        extension = await gazu.files.get_output_type_by_name("fbx")
        temp_outfilename = outdir / f"{outfilename}_{root_name}" if root_name else outdir / f"{outfilename}"
        final_filename = str(pathlib.Path(temp_outfilename).with_suffix(f".{extension['short_name']}"))

         # Set frame range
        if used_timeline:
            range_playbar = hou.playbar.frameRange()
            start_frame = range_playbar.x()
            end_frame = range_playbar.y()

        # create temp filmboxfbx
        fbx_rop = hou.node("out").createNode("filmboxfbx")
        fbx_rop.parm("sopoutput").set(final_filename)
        fbx_rop.parm("createsubnetroot").set(0)

        # create temp root node
        temp_subnet = hou.node("obj").createNode("subnet")

        # animation keys
        fbx_rop.parm("trange").set(1)
        fbx_rop.parmTuple("f").deleteAllKeyframes() # Needed
        fbx_rop.parmTuple("f").set((start_frame, end_frame, 0))

        hou.moveNodesTo(selected_object, temp_subnet)

        # past temp_subnet in export fbx 
        fbx_rop.parm("startnode").set(temp_subnet.path())

        # link node to object
        fbx_rop.parm("execute").pressButton()

        # remove fbx export
        fbx_rop.destroy()
        
        # reup node in temp_subnet into /obj
        selected = [hou.node(f"{temp_subnet.path()}/{item}") for item in selected_name]
        hou.moveNodesTo(selected, hou.node("/obj/"))

        # remove temp_subnet
        temp_subnet.destroy()

        # export
        logger.info(f"Done export fbx, output paths : {final_filename}")

        return final_filename

    @CommandBase.conform_command()
    async def __undo__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        outdir = parameters.get("file_dir")
