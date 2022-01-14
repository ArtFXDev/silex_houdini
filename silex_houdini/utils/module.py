from inspect import getmembers, isfunction
from typing import Callable, List


def get_functions_in_module(module: object) -> List[Callable]:
    """Return a list of functions in a module"""
    return [e[1] for e in getmembers(module, isfunction)]
