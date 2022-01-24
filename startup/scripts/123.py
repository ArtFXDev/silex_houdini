import hou
from silex_client.action.action_query import ActionQuery
from silex_client.core.context import Context

from create_shelf import create_shelf
from custom_save import custom_save

# Start the maya services
if hou.isUIAvailable():
    Context.get().start_services()
    create_shelf()

# Register the increment and save and save
custom_save()

# Save the scene one first time
save_action = ActionQuery("save")
save_action.set_parameter("save:save_scene:only_path", True)
save_action.execute()
