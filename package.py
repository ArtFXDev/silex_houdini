# pylint: skip-file
name = "silex_houdini"
version = "0.1.0"

authors = ["ArtFx TD gang"]

description = """
    Set of python module and houdini config to integrate houdini in the silex pipeline
    Part of the Silex ecosystem
    """

vcs = "git"

build_command = "python {root}/script/build.py {install}"


def commands():
    """
    Set the environment variables for silex_houdini
    """
    env.SILEX_ACTION_CONFIG.prepend("{root}/silex_houdini/config")
    env.PYTHONPATH.append("{root}")
    env.HOUDINI_PATH.append("{root}/startup")
    env.PYTHONPATH.append("{root}/startup/scripts")

    parser_module = ".".join(["silex_houdini", "cli", "parser"])
    alias("silex", f"hython -m {parser_module}")


@late()
def requires():
    major = str(this.version.major)
    silex_requirement = ["silex_client"]
    if major in ["dev", "beta", "prod"]:
        silex_requirement = [f"silex_client-{major}"]

    return ["houdini", "python-3.7"] + silex_requirement
