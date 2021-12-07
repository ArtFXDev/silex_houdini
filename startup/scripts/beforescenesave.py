from silex_client.action.action_query import ActionQuery
save_action = ActionQuery("save")
save_action.set_parameter("save:save_scene:only_path", True)
save_action.execute()