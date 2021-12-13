from __future__ import annotations

import pathlib
import fileseq
import pathlib
import logging
import os
import pathlib
from typing import TYPE_CHECKING, List, Tuple, Dict, Any, Union

import hou

from silex_client.utils.files import is_valid_pipeline_path, is_valid_path
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta, ListParameterMeta
from silex_houdini.utils.utils import Utils

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


References = List[
    Tuple[
        List[Union[hou.Parm, hou.HDADefinition]],
        Union[List[pathlib.Path], pathlib.Path],
    ]
]

PARAMETER_BLACK_LIST = ["SettingsOutput_img_file_path"]


class GetReferences(CommandBase):
    """
    Find all the referenced files, including textures, HDAs...
    """

    parameters = {
        "skip_conformed": {
            "label": "Skip conformed references",
            "type": bool,
            "value": True,
            "tooltip": "The references that point to a file that is already in the right folder will be skipped",
        },
        "filters": {
            "label": "Custom filters",
            "type": ListParameterMeta(str),
            "value": [],
            "tooltip": "List of file extensions to ignore",
        },
    }

    async def _prompt_new_path(
        self, action_query: ActionQuery, file_path: pathlib.Path, parameter: Any
    ) -> Tuple[pathlib.Path, bool]:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("warning"),
            name="info",
            label=f"Info",
            value=f"The file:\n{file_path}\n\nReferenced in:\n{parameter}\n\nCould not be reached",
        )
        path_parameter = ParameterBuffer(
            type=pathlib.Path,
            name="new_path",
            label=f"New path",
        )
        skip_parameter = ParameterBuffer(
            type=bool,
            name="skip",
            value=False,
            label=f"Skip this reference",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "skip": skip_parameter,
                "new_path": path_parameter,
            },
        )
        if response["new_path"] is not None:
            response["new_path"] = pathlib.Path(response["new_path"])
        return response["new_path"], response["skip"]

    def _filter_references(
        self,
        references: List[Tuple[Any, pathlib.Path]],
        skipped_extensions: List[str] = [],
        skip_conformed=True,
    ) -> List[Tuple[Any, pathlib.Path]]:
        """
        Filter out all the references that we don't care about
        """
        filtered_references = []

        for parameter, file_path in references:
            file_path = pathlib.Path(str(file_path))

            if isinstance(parameter, hou.Parm):
                # Get the real parameter
                while parameter.getReferencedParm() != parameter:
                    parameter = parameter.getReferencedParm()

                # Get the node the parameter belongs to
                node = parameter.node()

                # Skip the references that are in a locked HDA
                if node.isInsideLockedHDA():
                    continue

                # Skip black listed parameters
                if parameter.name() in PARAMETER_BLACK_LIST:
                    continue

                # Skip TOP network nodes
                if node.type().category().name() == "TopNet":
                    continue
                # Skip TOP nodes
                if node.type().category().name() == "Top":
                    continue

                # Skip hidden/disabled parameters
                if parameter.isDisabled() or parameter.isHidden():
                    continue

                # Skip hidden/disabled containing folders
                is_hidden_folder = False
                folders = {
                    p: p.parmTemplate()
                    for p in node.parms()
                    if isinstance(p.parmTemplate(), hou.FolderSetParmTemplate)
                }
                for folder_name in parameter.containingFolders():
                    for node_parameter, template in folders.items():
                        if folder_name in template.folderNames() and (
                            node_parameter.isDisabled() or node_parameter.isHidden()
                        ):
                            is_hidden_folder = True
                            break
                if is_hidden_folder:
                    continue

                # Get the real path
                file_path = pathlib.Path(str(parameter.eval()))

            # Skip invalid path
            if not is_valid_path(str(file_path)):
                continue

            # Skip path relative
            if not file_path.is_absolute():
                continue

            # Skip the references that are already conformed
            if skip_conformed and is_valid_pipeline_path(file_path):
                continue

            # Skip path relative to HOUDINI_PATH
            houdini_path_relative = False
            for houdini_path in os.getenv("HOUDINI_PATH", "").split(os.pathsep):
                if not os.path.exists(houdini_path):
                    continue
                if str(pathlib.Path(houdini_path)) in str(file_path):
                    houdini_path_relative = True
            if houdini_path_relative:
                continue

            # Skip the custom extensions provided
            if "".join(pathlib.Path(file_path).suffixes) in skipped_extensions:
                continue

            filtered_references.append((parameter, file_path))

        return filtered_references

    def _merge_duplicates(self, references: References) -> References:
        """
        Merge the files referenced multiple times into one item in the list of references
        """
        filtered_references = []
        for reference in references:
            file_paths = [file[1] for file in filtered_references]
            try:
                index = file_paths.index(reference[1])
                filtered_references[index][0].extend(reference[0])
            except ValueError:
                filtered_references.append(reference)

        return filtered_references

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # All the references found will be stored in this variable
        references_found: References = []

        # Get all the references of the scene
        scene_references = await Utils.wrapped_execute(action_query, hou.fileReferences)
        filtered_scene_references = await Utils.wrapped_execute(
            action_query,
            self._filter_references,
            await scene_references,
            parameters["filters"],
            parameters["skip_conformed"],
        )

        # Loop over all the filtered references
        for parameter, file_path in await filtered_scene_references:
            # Get the real path
            expanded_path = await Utils.wrapped_execute(
                action_query, hou.expandString, str(file_path)
            )
            file_path = pathlib.Path(await expanded_path)

            # Make sure the file path leads to a reachable file
            skip = False
            while not file_path.exists():
                file_path, skip = await self._prompt_new_path(
                    action_query, file_path, parameter
                )
                if skip or file_path is None:
                    break
            # The user can decide to skip the references that are not reachable
            if skip or file_path is None:
                logger.info("Skipping the reference at %s", parameter)
                continue

            # Special treatment for HDAs
            hda_extensions = [".hda", ".hdanc", ".hdalc"]
            if parameter is None and file_path.suffix in hda_extensions:
                definitions = await Utils.wrapped_execute(
                    action_query, hou.hda.definitionsInFile, file_path.as_posix()
                )
                references_found.append((await definitions, file_path))

            # Look for file sequence
            sequence = None
            for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                # Find the file sequence that correspond the to file we are looking for
                sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                if file_path in sequence_list and len(sequence_list) > 1:
                    sequence = file_sequence
                    file_path = sequence_list
                    break

            # Append to the references found
            references_found.append(([parameter], file_path))
            if sequence is None:
                logger.info("Referenced file(s) %s found at %s", file_path, parameter)
            else:
                logger.info("Referenced file(s) %s found at %s", sequence, parameter)

        # Remove all the duplicates
        references_found = self._merge_duplicates(references_found)

        # Display a message to the user to inform about all the references to conform
        referenced_file_paths = [
            fileseq.findSequencesInList(reference[1])
            if isinstance(reference[1], list)
            else [reference[1]]
            for reference in references_found
        ]
        message = f"The scene\n{hou.hipFile.path()}\nis referencing non conformed file(s) :\n\n"
        for file_path in referenced_file_paths:
            message += f"- {' '.join([str(f) for f in file_path])}\n"

        message += "\nThese files must be conformed and repathed first. Press continue to conform and repath them"
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=message,
        )
        # Send the message to the user
        if referenced_file_paths:
            await self.prompt_user(action_query, {"info": info_parameter})

        return {
            "attributes": [file[0] for file in references_found],
            "file_paths": [file[1] for file in references_found],
        }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        new_path_parameter = self.command_buffer.parameters.get("new_path")
        skip_parameter = self.command_buffer.parameters.get("skip")
        if new_path_parameter is not None and skip_parameter is not None:
            if not skip_parameter.hide:
                new_path_parameter.hide = parameters.get("skip", True)
