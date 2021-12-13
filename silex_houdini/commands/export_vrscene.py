from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TextParameterMeta
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_houdini.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu
import logging


class ExportVrscene(CommandBase):

    parameters = {
        "file_dir": {"label": "Out directory", "type": str, "value": ""},
        "file_name": {"label": "Out filename", "type": str, "value": ""},
    }

    async def _prompt_info_parameter(
        self, action_query: ActionQuery, message: str, level: str = "warning"
    ) -> pathlib.Path:
        """
        Helper to prompt the user a labelb
        """
        # Create a new parameter to prompt label

        info_parameter = ParameterBuffer(
            type=TextParameterMeta(level),
            name="Info",
            label="Info",
            value=f"Warning : {message}",
        )
        label_parameter = ParameterBuffer(
            type=str, name="label_parameter", label=f"{message}"
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
        def export_fbx(selected_object, node, out_file_name, to_return, logger):
            node_filename = f"{out_file_name}_{node.name()}"
            node_filename = pathlib.Path(os.path.join(outdir, node_filename))
            node_filename = str(
                node_filename.with_suffix(f".{extension['short_name']}")
            )
            to_return.append(node_filename)
            node.parm("render_export_filepath").set(node_filename)
            node.parm("render_export_mode").set("2")
            logger.info(f"Done export abc, output paths : {node_filename}")

        def exec(selected_object):
            selected_object.parm("execute").pressButton()

        outdir = parameters["file_dir"]
        outFilename = parameters["file_name"]

        to_return = []
        # create out dir if not exist
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        # get current selection
        selected_object = [
            item
            for item in hou.selectedNodes()
            if item.type().name() == "vray_renderer"
        ]
        while len(selected_object) != 1:
            await self._prompt_info_parameter(
                action_query,
                "Invalid nodes selected,\n Please select V-Ray ROP nodes and continue.",
            )
            selected_object = [
                item
                for item in hou.selectedNodes()
                if item.type().name() == "vray_renderer"
            ]
        selected_object = selected_object[0]

        # inputDependencies
        # test current selection only composed of vrscene rop nodes
        selected_objects_types = selected_object.inputDependencies()
        logger.info(selected_objects_types)

        selected_objects_types = [
            item[0] for item in selected_objects_types
        ]  # [0] to avoid frames
        logger.info(selected_objects_types)
        not_allowed_rop = [
            item
            for item in selected_objects_types
            if item.type().name() != "vray_renderer"
        ]
        allowed_rop = [
            item
            for item in selected_objects_types
            if item.type().name() == "vray_renderer"
        ]

        # disable all not allowed rop nodes
        for node in not_allowed_rop:
            node.bypass(1)

        # get extension from api
        extension = await gazu.files.get_output_type_by_name("vrscene")

        # set outputpath for each render node
        for node in allowed_rop:
            await Utils.wrapped_execute(
                action_query,
                export_fbx,
                selected_object,
                node,
                outFilename,
                to_return,
                logger,
            )
        await Utils.wrapped_execute(action_query, exec, selected_object)
        for node in not_allowed_rop:
            node.bypass(0)

        # export
        return to_return
