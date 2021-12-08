import asyncio
import hdefereval
import sys
import os
import errno
from typing import Callable
from silex_client.utils.log import logger
from silex_client.core.context import Context
from concurrent import futures

# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123

class Utils:
    @staticmethod
    async def wrapped_execute(action_query, houdini_function: Callable, *args, **kwargs):

        future = action_query.event_loop.loop.create_future()

        def wrapped_function():
            async def set_future_result(result):
                future.set_result(result)

            async def set_future_exception(exception):
                future.set_exception(exception)

            try:
                result = houdini_function(*args, **kwargs)
                Context.get().event_loop.register_task(set_future_result(result))
            except Exception as ex:
                Context.get().event_loop.register_task(set_future_exception(ex))

        # This maya function execute the given function in the main thread
        hdefereval.executeDeferred(wrapped_function)

        def callback(task_result: futures.Future):
            if task_result.cancelled():
                return

            exception = task_result.exception()
            if exception:
                logger.error("Exception raised in wrapped execute call: %s", exception)
                raise Exception(
                    f"Exception raised in wrapped execute call: {exception}"
                )

        future.add_done_callback(callback)
        await asyncio.wait_for(future, None)
        return future

    @staticmethod
    def is_pathname_valid(pathname: str) -> bool:
        '''
        `True` if the passed pathname is a valid pathname for the current OS;
        `False` otherwise.
        '''
        # If this pathname is either not a string or is but is empty, this pathname
        # is invalid.
        try:
            if not isinstance(pathname, str) or not pathname:
                return False

            _, pathname = os.path.splitdrive(pathname)

            root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
                if sys.platform == 'win32' else os.path.sep
            assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

            # Append a path separator to this directory if needed.
            root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

            # Test whether each path component split from this pathname is valid or
            # not, ignoring non-existent and non-readable path components.
            for pathname_part in pathname.split(os.path.sep):
                try:
                    os.lstat(root_dirname + pathname_part)
                except OSError as exc:
                    if hasattr(exc, 'winerror'):
                        if exc.winerror == ERROR_INVALID_NAME:
                            return False
                    elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                        return False
        except TypeError as exc:
            return False
        else:
            return True
