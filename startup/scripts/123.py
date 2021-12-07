from silex_client.core.context import Context
from create_shelf import create_shelf
from silex_client.action.action_query import ActionQuery

Context.get().start_services()
create_shelf()

save_action = ActionQuery("save")
save_action.set_parameter("save:save_scene:only_path", True)
save_action.execute()
