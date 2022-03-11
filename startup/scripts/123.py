import hou
from silex_client.core.context import Context

from create_shelf import create_shelf
from custom_save import custom_save

# Start the maya services
if hou.isUIAvailable():
    Context.get().start_services()
    create_shelf()

# Register the increment and save and save
custom_save()
