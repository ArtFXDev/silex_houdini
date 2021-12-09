from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.action.action_query import ActionQuery
import hou
import os


def create_shelf():
    """
    Entry point of create shelf
    """
    shelf_id = "silex_shelf"
    shelfset_id = "silex_shelfset"

    # create shelfset
    shelfset = None
    # create shelf
    shelf = None

    # update shelf if already exist
    for shelf_item in hou.shelves.shelves():
        if shelf_id in str(shelf_item):
            shelf = hou.shelves.shelves()[shelf_id]

            # clear content of existing shelf
            for tool_index in range(len(shelf.tools()), 0, -1):
                shelf.tools()[tool_index - 1].destroy()

    if not shelf:
        shelf = hou.shelves.newShelf(name=shelf_id, label=shelf_id)

    # find silex shelfset
    for shelfset_item in hou.shelves.shelfSets():
        if shelfset_id in str(shelfset_item):
            shelfset = hou.shelves.shelfSets()[shelfset_item]

    # create shelfset if not exist
    if not shelfset:
        shelfset = hou.shelves.newShelfSet(name=shelfset_id, label=shelfset_id)

    # reload in case of update
    hou.shelves.reloadShelfFiles()

    # start editing shelves
    hou.shelves.beginChangeBlock()

    # get action
    import_statement = "from silex_client.action.action_query import ActionQuery\n"
    actions = {}
    for item in Config().actions:
        action = ActionQuery(item["name"])
        actions[item["name"]] = {
            "script":  f"{import_statement}ActionQuery('{item['name']}').execute()",
            "icon": action.buffer.thumbnail,
            "label": action.buffer.label
        }

    shelf_tools = []
    for action in actions:
        tool = hou.shelves.newTool(name=action, **actions[action])
        shelf_tools.append(tool)

    # set action in pipeline shelf
    shelf.setTools(list(shelf.tools()) + list(shelf_tools))

    # add shelve in shelfset
    silex_shelves = list(shelfset.shelves())
    silex_shelves.append(shelf)
    shelfset.setShelves(silex_shelves)

    # end editing shelves
    hou.shelves.endChangeBlock()
    hou.shelves.reloadShelfFiles()
