from silex_client.core.context import Context
import hou
import os

def create_shelf():
    shelf_id = "silex_shelf"

    # to switch to another context
    shot_id = Context.get().metadata.get("shot_id", -1)
    if shot_id is not -1:
        os.environ["SILEX_TASK_ID"] = shot_id
        Context.get().is_outdated = True

    hou.shelves.beginChangeBlock()

    # create shelf
    shelf = hou.shelves.newShelf(name=shelf_id, label=shelf_id)
    
    # get action
    actions = { item["name"]: f"from silex_client.core.context import Context;Context.get().get_action('{item['name']}').execute()" for item in Context.get().config.actions }
    print(actions)
    shelf_tools = []
    for action in actions:
        tool = hou.shelves.newTool(label=action, name=action, script=actions[action])
        shelf_tools.append(tool)

    shelf.setTools(list(shelf.tools()) + list(shelf_tools))
    hou.shelves.endChangeBlock()

create_shelf()