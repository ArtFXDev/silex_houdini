from __future__ import annotations
import typing
from typing import Any, Dict, List
import fileseq

import re
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta, AnyParameter
from silex_client.utils.log import logger

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
            "type": ListParameterMeta(str),
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
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        attributes: List[str] = parameters["attributes"]
        indexes: List[int] = parameters["indexes"]

        values = []
        # TODO: This should be done in the get_value method of the ParameterBuffer
        for value in parameters["values"]:
            value = value.get_value(action_query)[0]
            value = value.get_value(action_query)
            values.append(value)

        # Define the function that will repath all the references
        new_values = []
        for attribute, index, values in zip(attributes, indexes, values):
            value = values
            if isinstance(value, list):
                value = value[index]

            # If the attribute is an HDA
            if isinstance(attribute, hou.HDADefinition):
                hou.hda.installFile(value, force_use_assets=True)
                continue

            # If the attribute if from an other referenced scene
            if isinstance(attribute, hou.Parm) or isinstance(attribute, hou.ParmTuple):
                if isinstance(values, list) and len(value) > 1:
                    sequence = fileseq.findSequencesInList(values)
                    raw_value = attribute.rawValue()
                    index_indicator = raw_value.rfind("$")
                    index_expression = re.search(r"\W", raw_value[index_indicator:])
                    if index_indicator >= 0 and match is not None:
                        pass
                    else:
                        logger.warning("Could not recreate the value for the parameter %s", attribute)

                attribute.set(value)

            new_values.append(value)

        return new_values