from __future__ import annotations
import typing
from typing import Any, Dict, List
import logging
import pathlib
import fileseq

import re
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta, AnyParameter
from silex_client.utils.files import format_sequence_string
from silex_houdini.utils.constants import FILE_PATH_SEQUENCE_CAPTURE

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
            "type": ListParameterMeta(ListParameterMeta(AnyParameter)),
            "value": None,
        },
        "values": {
            "label": "Values",
            "type": ListParameterMeta(AnyParameter),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        attributes: List[List[Any]] = parameters["attributes"]

        attribute_values = []
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            value = value.get_value(action_query)[0]
            value = value.get_value(action_query)
            attribute_values.append(value)

        # Define the function that will repath all the references
        new_values = []
        for attribute_list, values in zip(attributes, attribute_values):
            for attribute in attribute_list:
                value = values
                if isinstance(values, list):
                    value = values[0]
                else:
                    value = values

                # Houdini need posix path
                value = pathlib.Path(value).as_posix()

                # If the attribute is an HDA
                if isinstance(attribute, hou.HDADefinition):
                    logger.info("Installing HDA at path %s", value)
                    hou.hda.installFile(value, force_use_assets=True)
                    continue

                # If the attribute if from an other referenced scene
                if isinstance(attribute, hou.Parm) or isinstance(
                    attribute, hou.ParmTuple
                ):
                    value = self.set_parameter(value, values, attribute)
                    logger.info("Setting attribute %s to %s", attribute, value)

                new_values.append(value)

        return new_values

    def set_parameter(self, value, values, attribute):
        if isinstance(values, list) and len(values) > 1:
            sequence = fileseq.findSequencesInList(values)[0]
            raw_value = attribute.rawValue()

            value = format_sequence_string(
                sequence, raw_value, FILE_PATH_SEQUENCE_CAPTURE
            )

        attribute.set(value)
        return value
