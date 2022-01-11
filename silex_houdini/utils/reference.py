from __future__ import annotations

import logging
import pathlib

# from inspect import getmembers, isfunction
from typing import Any, List, Tuple

import hou
from silex_client.utils.files import is_valid_pipeline_path
from silex_houdini.utils import parameter_filters, reference_path_filters
from silex_houdini.utils.module import get_functions_in_module


def filter_references(
    references: List[Tuple[Any, pathlib.Path]],
    logger: logging.Logger,
    skipped_extensions: List[str] = [],
    skip_conformed=True,
) -> List[Tuple[Any, pathlib.Path]]:
    """
    Filter out all the references that we don't care about
    """
    filtered_references = []

    # Skip the references that are already conformed
    def filter_already_conformed(node, parameter, file_path):
        return skip_conformed and is_valid_pipeline_path(file_path)

    # Skip the custom extensions provided
    def filter_custom_extensions(node, parameter, file_path):
        return "".join(pathlib.Path(file_path).suffixes) in skipped_extensions

    # Get all the filter functions dynamically from modules
    path_filters = get_functions_in_module(reference_path_filters)

    param_filters = get_functions_in_module(parameter_filters) + [
        filter_already_conformed,
        filter_custom_extensions,
    ]

    for parameter, file_path in references:
        file_path = pathlib.Path(str(file_path))
        is_param = isinstance(parameter, hou.Parm)

        if is_param:
            # Evaluate the Houdini expression to get the real path
            file_path = pathlib.Path(str(parameter.eval()))

            # Get the real parameter
            while parameter.getReferencedParm() != parameter:
                parameter = parameter.getReferencedParm()

        # Skip duplicates
        if (parameter, file_path) in filtered_references:
            continue

        # Filter the reference path
        if any([path_filter(file_path) for path_filter in path_filters]):
            continue

        if is_param:
            # Get the node the parameter belongs to
            node = parameter.node()

            # Check the node against filters
            filter_hit= False
            for param_filter in param_filters:
                if param_filter(node, parameter, file_path):
                    filter_hit = True
                    logger.info("Skipping %s: Filtered by %s", file_path, param_filter)
                    break

            if filter_hit:
                continue

        filtered_references.append((parameter, file_path))

    return filtered_references
