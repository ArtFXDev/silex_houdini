print("aaaa")

from silex_client.core.context import Context
import hou
from hou import shelves

def create_shelf():
    print("aaaa")

    hou.shelves.beginChangeBlock()

    # create shelf
    shelf = hou.shelves.newShelf("silex_shelf")
    
    # get action
    actions = { item["name"]: f"Context.get().get_action('{item['name']}').execute()" for item in Context.get().config.actions }
    print(actions)
    shelf_tools = []
    for action in actions:
        tool = hou.shelves.newTool(label=action, name=action, script=actions[action])
        shelf_tools.append(tool)

    shelf.setTools(list(shelf.tools()) + list(shelf_tools))
    hou.shelves.endChangeBlock()

create_shelf()