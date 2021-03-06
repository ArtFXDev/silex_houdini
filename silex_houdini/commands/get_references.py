from __future__ import annotations

import logging
import pathlib
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import fileseq
import hou
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import ListParameterMeta, TextParameterMeta
from silex_client.utils.files import find_sequence_from_path
from silex_houdini.utils import reference
from silex_houdini.utils.constants import FILE_PATH_SEQUENCE_CAPTURE
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
        "skip_prompt": {'type': bool, 'value': False},
    }

    async def _prompt_new_path(
        self, action_query: ActionQuery, file_path: pathlib.Path, parameter: Any
    ) -> Tuple[pathlib.Path, bool, bool]:
        """
        Helper to prompt the user for a new path and wait for its response
        """
        current_skip = self.command_buffer.parameters.get("skip")
        current_skip_value = current_skip.value if current_skip is not None else False
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
            value=current_skip_value,
            label=f"Skip this reference",
        )
        skip_all_parameter = ParameterBuffer(
            type=bool,
            name="skip_all",
            value=False,
            label=f"Skip all unresolved reference",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "skip_all": skip_all_parameter,
                "skip": skip_parameter,
                "new_path": path_parameter,
            },
        )
        if response["new_path"] is not None:
            response["new_path"] = pathlib.Path(response["new_path"])
        return response["new_path"], response["skip"], response["skip_all"]

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

    def _find_sequence(
        self, file_path: pathlib.Path
    ) -> Tuple[Optional[fileseq.FileSequence], List[pathlib.Path]]:
        sequence = None
        regex = fileseq.FileSequence.DISK_RE

        match = regex.match(str(file_path))

        if not self._test_possible_sequence(file_path) or match is None:
            return sequence, [file_path]

        _, basename, _, ext = match.groups()
        for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
            # Find the file sequence that correspond the to file we are looking for
            sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
            if (
                basename == file_sequence.basename()
                and ext == file_sequence.extension()
            ):
                return sequence, sequence_list

        return sequence, [file_path]

    def _test_possible_sequence(self, file_path: pathlib.Path) -> bool:
        """
        Test if the file path contains a sequence
        """

        return any([r.match(str(file_path)) for r in FILE_PATH_SEQUENCE_CAPTURE])

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
            reference.filter_references,
            await scene_references,
            logger,
            parameters["filters"],
            parameters["skip_conformed"],
        )

        # Loop over all the filtered references
        skip_all = False
        for parameter, file_path in await filtered_scene_references:

            # Get the real path
            expanded_path = await Utils.wrapped_execute(
                action_query, hou.expandString, str(file_path)
            )

            file_path = pathlib.Path(await expanded_path)
            sequence = find_sequence_from_path(file_path)
            file_path_list = [pathlib.Path(file) for file in sequence]
            file_path = file_path_list[0]

            # Make sure the file path leads to a reachable file
            skip = False
            while not file_path.exists():
                if skip_all:
                    skip = True
                    break
                file_path, skip, skip_all = await self._prompt_new_path(
                    action_query, file_path, parameter
                )
                if skip or file_path is None or skip_all:
                    skip = True
                    break
                # Recompute the sequence
                sequence, file_path_list = self._find_sequence(file_path)
                file_path = file_path_list[0]

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
                references_found.append((list(await definitions), file_path_list))
            # Append to the references found
            references_found.append(([parameter], file_path_list))
            if sequence is None:
                logger.info("Referenced file(s) %s found at %s", file_path, parameter)
            else:
                logger.info("Referenced file(s) %s found at %s", sequence, parameter)

        # Remove all the duplicates
        references_found = self._merge_duplicates(references_found)

        referenced_file_paths = [
            fileseq.findSequencesInList(reference[1])
            if isinstance(reference[1], list)
            else [reference[1]]
            for reference in references_found
        ]
        
        # Send the message to the user
        if referenced_file_paths and not parameters['skip_prompt']:
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
        skip_all_parameter = self.command_buffer.parameters.get("skip_all")
        if (
            new_path_parameter is not None
            and skip_parameter is not None
            and skip_all_parameter is not None
        ):
            if not skip_all_parameter.hide:
                skip_parameter.hide = parameters.get("skip_all", True)
                new_path_parameter.hide = parameters.get("skip_all", True)
            if not skip_parameter.hide:
                new_path_parameter.hide = parameters.get("skip", True)
