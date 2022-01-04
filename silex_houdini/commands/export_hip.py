from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_houdini.utils.utils import Utils

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou
import os
import pathlib
import gazu
import logging

class ExportHip(CommandBase):
    """
    Export selection as ma
    """

    parameters = {
        "directory": {
            "label": "File directory",
            "type": pathlib.Path,
            "value": None,
        },
        "file_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": None,
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

       
        directory: str = str(parameters.get("directory"))
        file_name: str = str(parameters.get("file_name"))
        extension = await gazu.files.get_output_type_by_name("hip")
        full_scene: bool = False
        export_valid: bool =  False
        
        # Check for extension
        if "." in file_name:
            file_name = file_name.split('.')[0]
          
        export_path: str = f"{directory}{os.path.sep}{file_name}.{extension['name']}"

        # export
        os.makedirs(directory, exist_ok=True)
        await Utils.wrapped_execute(action_query, hou.hipFile.save, export_path)
       

        if not os.path.exists(export_path):
            raise Exception(
                f"An error occured while exporting {export_path} to ma")
        return export_path


    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if 'info' in parameters:
            if parameters.get("full_scene", False):            
                self.command_buffer.parameters["info"].type = TextParameterMeta('warning')
                self.command_buffer.parameters["info"].value = "WARNING: No selection detected -> Please selecte somthing or publish full scene"
            else:
                self.command_buffer.parameters["info"].type = TextParameterMeta('info')
                self.command_buffer.parameters["info"].value = 'Select somthing to publish'

