from __future__ import annotations
import typing
from typing import Any, Dict, List
import logging
import pathlib
import fileseq

import re
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta, AnyParameter

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou


class SetReferences(CommandBase):
    """
    Repath the given references
    """

    parameters = {
        "attributes": {
            "label": "Attributes",
            "type": ListParameterMeta(AnyParameter),
            "value": None,
        },
        "values": {
            "label": "Values",
            "type": ListParameterMeta(AnyParameter),
            "value": None,
        },
        "indexes": {
            "label": "Indexes",
            "type": ListParameterMeta(int),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        attributes: List[str] = parameters["attributes"]
        indexes: List[int] = parameters["indexes"]

        attribute_values = []
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            value = value.get_value(action_query)[0]
            value = value.get_value(action_query)
            attribute_values.append(value)

        # Define the function that will repath all the references
        new_values = []
        for attribute, index, values in zip(attributes, indexes, attribute_values):
            value = values
            if isinstance(values, list):
                value = values[index]

            # Houdini need posix path
            value = pathlib.Path(value).as_posix()

            # If the attribute is an HDA
            if isinstance(attribute, hou.HDADefinition):
                logger.info("Installing HDA at path %s", value)
                hou.hda.installFile(value, force_use_assets=True)
                continue

            # If the attribute if from an other referenced scene
            if isinstance(attribute, hou.Parm) or isinstance(attribute, hou.ParmTuple):
                if isinstance(values, list) and len(values) > 1:
                    sequence = fileseq.findSequencesInList(values)[0]
                    raw_value = attribute.rawValue()

                    REGEX_MAPPING = {r"\$[FTRN]": r"\W", r"\%.": r"\).", r"\<": r"\>."}
                    for start_regex, end_regex in REGEX_MAPPING.items():
                        index_start = list(re.finditer(start_regex, raw_value))
                        if not index_start:
                            continue
                        index_start = index_start[-1].start()
                        index_end = list(re.finditer(end_regex, raw_value[index_start+1:]))
                        if not index_end:
                            continue
                        index_end = index_end[0].end()

                        index_expression = raw_value[index_start:index_start + index_end]
                        dirname = pathlib.Path(str(sequence.dirname()))
                        basename = sequence.format("{basename}" + str(index_expression) + "{extension}")
                        value = (dirname / basename).as_posix()

                logger.info("Setting attribute %s to %s", attribute, value)
                attribute.set(value)

            new_values.append(value)

        return new_values
