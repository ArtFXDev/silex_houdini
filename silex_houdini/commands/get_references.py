from __future__ import annotations

import pathlib
import fileseq
import pathlib
import logging
import os
from typing import TYPE_CHECKING, List, Tuple, Dict, Any, Union

import hou

from silex_client.utils.files import is_valid_pipeline_path, is_valid_path
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import TextParameterMeta
from silex_houdini.utils.utils import Utils

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


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
        }
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
            value=f"The file {file_path} referenced in {parameter} could not be reached",
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
                "new_path": path_parameter,
                "skip": skip_parameter,
            },
        )
        if response["new_path"] is not None:
            response["new_path"] = pathlib.Path(response["new_path"])
        return response["new_path"], response["skip"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        referenced_files: List[
            Tuple[
                List[Union[hou.Parm, hou.HDADefinition]],
                Union[List[pathlib.Path], pathlib.Path],
                List[int],
            ]
        ] = []

        scene_references = await Utils.wrapped_execute(action_query, hou.fileReferences)
        filtered_references = await self.filter_references(await scene_references)

        for parameter, file_path in filtered_references:
            # Skip the references that are in a locked HDA
            if isinstance(parameter, hou.Parm):
                is_locked_lamnda = lambda: parameter.node().isInsideLockedHDA()
                is_locked = await Utils.wrapped_execute(action_query, is_locked_lamnda)
                if await is_locked:
                    continue

            expanded_path = await Utils.wrapped_execute(
                action_query, hou.expandString, file_path
            )
            file_path = pathlib.Path(await expanded_path)
            try:
                # Make sure the file path leads to a reachable file
                skip = False
                while not file_path.exists() or not file_path.is_absolute():
                    file_path, skip = await self._prompt_new_path(
                        action_query, file_path, parameter
                    )
                    if skip or file_path is None:
                        break
                # The user can decide to skip the references that are not reachable
                if skip or file_path is None:
                    logger.info("Skipping the reference at %s", parameter)
                    continue

            except OSError:
                sequences = fileseq.findSequencesOnDisk(str(file_path.parent))
                for sequence in sequences:
                    if str(sequence.basename()) in str(file_path):
                        file_path = pathlib.Path(str(sequence[0]))
                        break

            # Skip the references that are already conformed
            if parameters["skip_conformed"]:
                if is_valid_pipeline_path(file_path):
                    continue

            # Initialize the index to -1, which is the value if there is no sequences
            index = -1

            # Get the definition of the HDA for HDA references
            if parameter is None and file_path.suffix in [
                ".hda",
                ".hdanc",
                ".hdalc",
            ]:
                definitions = await Utils.wrapped_execute(
                    action_query, hou.hda.definitionsInFile, file_path.as_posix()
                )
                for definition in await definitions:
                    if file_path in [
                        referenced_file[1] for referenced_file in referenced_files
                    ]:
                        break
                    logger.info("Referenced HDA %s found at %s", file_path, definition)
                    referenced_files.append(([definition], file_path, [index]))
                continue

            # Look for a file sequence
            sequence = None
            for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                # Find the file sequence that correspond the to file we are looking for
                sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                if file_path in sequence_list and len(sequence_list) > 1:
                    sequence = file_sequence
                    index = sequence_list.index(file_path)
                    file_path = sequence_list
                    break

            # Append to the verified path
            referenced_files.append(([parameter], file_path, [index]))
            if sequence is None:
                logger.info("Referenced file(s) %s found at %s", file_path, parameter)
            else:
                logger.info("Referenced file(s) %s found at %s", sequence, parameter)

        # Remove all the duplicates
        filtered_references = []
        for reference in referenced_files:
            file_paths = [file[1] for file in filtered_references]
            try:
                index = file_paths.index(reference[1])
                filtered_references[index][0].extend(reference[0])
                filtered_references[index][2].extend(reference[2])
            except ValueError:
                filtered_references.append(reference)

        return {
            "attributes": [file[0] for file in filtered_references],
            "file_paths": [file[1] for file in filtered_references],
            "indexes": [file[2] for file in filtered_references],
        }

    async def filter_references(self, references):
        filtered_references = []
        for parameter, file_path in references:
            if isinstance(parameter, hou.Parm):
                node = parameter.node()

                # Skip TOP network nodes
                if parameter.node().type().category().name() == "TopNet":
                    continue
                # Skip TOP nodes
                if parameter.node().type().category().name() == "Top":
                    continue

                # Skip hidden/disabled parameters
                if parameter.isDisabled() or parameter.isHidden():
                    continue

                # Skip hidden/disabled containing folders
                folders = {p: p.parmTemplate() for p in node.parms() if isinstance(p.parmTemplate(), hou.FolderSetParmTemplate)}
                for folder_name in parameter.containingFolders():
                    for parameter, template in folders.items():
                        if folder_name in template.folderNames() and (parameter.isDisabled() or parameter.isHidden()):
                            continue
                    
                # Skip channel references
                if parameter.getReferencedParm() == parameter:
                    continue

                file_path = parameter.eval()

            # Skip invalid path
            if not is_valid_path(file_path):
                continue

            # Skip path relative
            if not pathlib.Path(file_path).is_absolute():
                continue

            # Skip path relative to HOUDINI_PATH
            for houdini_path in os.getenv("HOUDINI_PATH", "").split(os.pathsep):
                if str(pathlib.Path(houdini_path)) in str(pathlib.Path(file_path)):
                    continue

            filtered_references.append((parameter, file_path))

        return filtered_references
