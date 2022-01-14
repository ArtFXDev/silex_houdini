import hou
from silex_client.action.action_query import ActionQuery
from silex_client.resolve.config import Config


def create_shelf():
    """
    Entry point of create shelf
    """
    silex_shelf_name = "silex_shelf"
    silex_shelfset_name = "silex_shelfset"

    shelf = None
    shelfset = None

    existing_shelves = hou.shelves.shelves()
    existing_shelfsets = hou.shelves.shelfSets()

    # Check if shelf already exist
    if not silex_shelf_name in existing_shelves:
        shelf = hou.shelves.newShelf(name=silex_shelf_name, label="Silex")
    else:
        shelf = existing_shelves[silex_shelf_name]

        # Destroy all the tools so we can recreate them dynamically
        for tool in existing_shelves[silex_shelf_name].tools():
            tool.destroy()

    # Check if shelf set already exist
    if not silex_shelfset_name in existing_shelfsets:
        shelfset = hou.shelves.newShelfSet(
            name=silex_shelfset_name, label="Silex pipeline"
        )
    else:
        shelfset = existing_shelfsets[silex_shelfset_name]

    # Start editing shelves
    hou.shelves.beginChangeBlock()

    # Construct the python snippet that will be in the shelf
    import_statement = "from silex_client.action.action_query import ActionQuery"
    actions = {}

    # For each actions in silex_houdini
    for item in Config().actions:
        action = ActionQuery(item["name"])

        # Execute the action
        actions[item["name"]] = {
            "script": f"{import_statement}\nActionQuery('{item['name']}').execute()",
            "icon": action.buffer.thumbnail,
            "label": action.buffer.label,
        }

    # Create shelf tools
    shelf_tools = []
    for action in actions:
        tool = hou.shelves.newTool(name=action, **actions[action])
        shelf_tools.append(tool)

    # Set action in pipeline shelf
    shelf.setTools(shelf_tools)

    # Add shelve in shelfset
    silex_shelves = list(shelfset.shelves())
    silex_shelves.append(shelf)
    shelfset.setShelves(silex_shelves)

    # End editing shelves
    hou.shelves.endChangeBlock()
    hou.shelves.reloadShelfFiles()
