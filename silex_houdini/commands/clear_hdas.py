from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import hou


class ClearHDAs(CommandBase):
    """
    Uninstall all the uninstanciated HDA definitions
    """

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        hda_files = hou.hda.loadedFiles()
        for hda_file in hda_files:
            isUsed = False
            for definition in hou.hda.definitionsInFile(hda_file):
                if definition.isPreferred():
                    isUsed = True
            
            if not isUsed and hou.text.expandString("$HH") not in hda_file:
                logger.info("Clearing HDA file %s", hda_file)
                hou.hda.uninstallFile(hda_file)
