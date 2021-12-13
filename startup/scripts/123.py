import hou

import pathlib

from silex_client.utils.files import is_valid_pipeline_path
from silex_client.core.context import Context
from create_shelf import create_shelf
from silex_client.action.action_query import ActionQuery

if hou.isUIAvailable():
    Context.get().start_services()
    create_shelf()

# Add a shortcut for increment and save
if hou.isUIAvailable():
    inctement_save_symbol = hou.hotkeys.hotkeySymbol("/Houdini", "increment_save")
    hou.hotkeys.addAssignment(inctement_save_symbol, "alt+shift+s")

# Add a save callback
def save_callback(event_type):
    if event_type != hou.hipFileEventType.BeforeSave:
        return

    if is_valid_pipeline_path(pathlib.Path(hou.hipFile.path()), "working"):
        return

    save_action = ActionQuery("save")
    save_action.set_parameter("save:save_scene:only_path", True)
    save_action.execute()


hou.hipFile.addEventCallback(save_callback)

# Save the scene one first time
save_action = ActionQuery("save")
save_action.set_parameter("save:save_scene:only_path", True)
save_action.execute()
