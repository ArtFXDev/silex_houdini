# pylint: skip-file
name = "silex_houdini"
version = "0.1.0"

authors = ["ArtFx TD gang"]

description = \
    """
    Set of python module and houdini config to integrate houdini in the silex pipeline
    Part of the Silex ecosystem
    """

vcs = "git"

requires = ["silex_client", "houdini", "python-3.7"]

build_command = "python {root}/script/build.py {install}"

def commands():
    """
    Set the environment variables for silex_houdini
    """
    env.SILEX_ACTION_CONFIG = "{root}/config/action"
    env.PYTHONPATH.append("{root}")
    env.HOUDINI_PATH.append("{root}/startup")