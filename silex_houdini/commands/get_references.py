from __future__ import annotations

import pathlib
import typing
import fileseq
import pathlib
import logging
import re
from typing import Any, Dict, List, Tuple, Union

import hou
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer

# Forward references
if typing.TYPE_CHECKING:
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
        self, action_query: ActionQuery
    ) -> Tuple[pathlib.Path, bool]:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        # Create a new parameter to prompt for the new file path
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
            {"new_path": path_parameter, "skip": skip_parameter},
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
                Union[hou.Parm, hou.HDADefinition],
                Union[List[pathlib.Path], pathlib.Path],
                int,
            ]
        ] = []

        for parameter, file_path in hou.fileReferences():
            # Skip the references that are in a locked HDA
            if isinstance(parameter, hou.Parm) and parameter.node().isInsideLockedHDA():
                continue

            file_path = pathlib.Path(hou.expandString(file_path))
            try:
                # Make sure the file path leads to a reachable file
                skip = False
                while not file_path.exists() or not file_path.is_absolute():
                    logger.warning(
                        "Could not reach the file %s at %s", file_path, parameter
                    )
                    file_path, skip = await self._prompt_new_path(action_query)
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
                if (
                    re.search(r"D:\\PIPELINE.+\\publish\\v", str(file_path.parent))
                    is not None
                ):
                    continue

            # Initialize the index to -1, which is the value if there is no sequences
            index = -1

            # Get the definition of the HDA for HDA references
            if parameter is None and file_path.suffix in [
                ".hda",
                ".hdanc",
                ".hdalc",
            ]:
                for definition in hou.hda.definitionsInFile(file_path.as_posix()):
                    if file_path in [
                        referenced_file[1] for referenced_file in referenced_files
                    ]:
                        break
                    logger.info("Referenced HDA %s found at %s", file_path, definition)
                    referenced_files.append((definition, file_path, index))
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
            referenced_files.append((parameter, file_path, index))
            if sequence is None:
                logger.info("Referenced file(s) %s found at %s", file_path, parameter)
            else:
                logger.info("Referenced file(s) %s found at %s", sequence, parameter)

        return {
            "attributes": [file[0] for file in referenced_files],
            "file_paths": [file[1] for file in referenced_files],
            "indexes": [file[2] for file in referenced_files],
        }
