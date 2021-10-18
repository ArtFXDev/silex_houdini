from silex_client.core.context import Context
import hou
import os
import pathlib


def create_shelf():
    """
    Entry point of create shelf
    """
    shelf_id = "silex_shelf"


    # update shelf if already exist
    for shelf in hou.shelves.shelves():
        if shelf_id in str(shelf):
            hou.shelves.shelves()[shelf].destroy()
            hou.shelves.reloadShelfFiles()

    # start editing shelves
    hou.shelves.beginChangeBlock()
    
    # to switch to another context
    shot_id = Context.get().metadata.get("shot_id", -1)
    if shot_id is not -1:
        os.environ["SILEX_TASK_ID"] = shot_id
        Context.get().is_outdated = True

    # create shelf
    shelf = hou.shelves.newShelf(name=shelf_id, label=shelf_id)
    
    # get action
    actions = { item["name"]: f"from silex_client.core.context import Context;Context.get().get_action('{item['name']}').execute()" for item in Context.get().config.actions }
    shelf_tools = []
    for action in actions:
        tool = hou.shelves.newTool(label=action, name=action, script=actions[action])
        shelf_tools.append(tool)

    # set action in pipeline shelf
    shelf.setTools(list(shelf.tools()) + list(shelf_tools))
    
    # end editing shelves
    hou.shelves.endChangeBlock()
    hou.shelves.reloadShelfFiles()

create_shelf()