from silex_client.core.context import Context
from create_shelf import create_shelf

Context.get().start_services()
create_shelf()
