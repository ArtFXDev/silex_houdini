from __future__ import annotations

import pathlib
import typing
import fileseq
import pathlib
from typing import Any, Dict, List, Tuple, Union

import hou
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GetReferences(CommandBase):
    """
    Find all the referenced files, including textures, HDAs...
    """

    async def _prompt_new_path(self, action_query: ActionQuery) -> pathlib.Path:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        new_parameter = ParameterBuffer(
            type=pathlib.Path,
            name="new_path",
            label=f"New path",
        )
        # Prompt the user to get the new path
        file_path = await self.prompt_user(
            action_query,
            {"new_path": new_parameter},
        )
        return pathlib.Path(file_path["new_path"])

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
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
            # Make sure the file path leads to a reachable file
            while not file_path.exists() or not file_path.is_absolute():
                logger.warning(
                    "Could not reach the file %s at %s", file_path, parameter
                )
                file_path = await self._prompt_new_path(action_query)

            # Initialize the index to -1, which is the value if there is no sequences
            index = -1

            # Get the definition of the HDA for HDA references
            if parameter is None and file_path.suffix in [
                ".hda",
                ".hdanc",
                ".hdalc",
            ]:
                for definition in hou.hda.definitionsInFile(file_path.as_posix()):
                    logger.info("Referenced HDA %s found at %s", file_path, definition)
                    referenced_files.append((definition, file_path, index))
                continue

            # Look for a file sequence
            for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                # Find the file sequence that correspond the to file we are looking for
                sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                if file_path in sequence_list and len(sequence_list) > 1:
                    index = sequence_list.index(file_path)
                    file_path = sequence_list
                    break

            # Append to the verified path
            referenced_files.append((parameter, file_path, index))
            logger.info("Referenced file(s) %s found at %s", file_path, parameter)

        return {
            "parameters": [file[0] for file in referenced_files],
            "file_paths": [file[1] for file in referenced_files],
        }
