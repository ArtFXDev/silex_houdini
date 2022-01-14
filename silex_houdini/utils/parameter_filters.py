import hou


def skip_inside_locked_hda(node, parameter, file_path) -> bool:
    return node.isInsideLockedHDA()


def skip_parameter_name(node, parameter, file_path) -> bool:
    skip_names = ["SettingsOutput_img_file_path"]
    return parameter.name() in skip_names


def skip_node_category_name(node, parameter, file_path) -> bool:
    skip_categories = ["TopNet", "Top"]
    return node.type().category().name() in skip_categories


def skip_file_name(node, parameter, file_path) -> bool:
    skip_names = ["OPlibVRay.hda"]
    return file_path.name in skip_names


def skip_hidden_or_disabled(node, parameter, file_path) -> bool:
    return parameter.isDisabled() or parameter.isHidden()


def skip_containing_folders(node, parameter, file_path) -> bool:
    folders = {
        p: p.parmTemplate()
        for p in node.parms()
        if isinstance(p.parmTemplate(), hou.FolderSetParmTemplate)
    }

    for folder_name in parameter.containingFolders():
        for node_parameter, template in folders.items():
            if folder_name in template.folderNames() and (
                node_parameter.isDisabled() or node_parameter.isHidden()
            ):
                return True

    return False


def skip_file_cache(node, parameter, file_path) -> bool:
    if not node.type().name() == "filecache":
        return False

    load_from_disk = node.parm("loadfromdisk").eval() == 1
    file_mode_read = node.parm("filemode").eval() == 1

    is_reference = load_from_disk or file_mode_read

    return not is_reference


def skip_locked(node, parameter, file_path) -> bool:
    if not isinstance(node, hou.SopNode):
        return False

    return node.isHardLocked() or node.isSoftLocked()


def skip_rop(node, parameter, file_path) -> bool:
    return isinstance(node, hou.RopNode)


def skip_dopio(node, parameter, file_path) -> bool:
    return node.type().name() == "dopio" and node.parm("loadfromdisk").eval() == 0


def skip_bypassed(node, parameter, file_path) -> bool:
    return isinstance(node, hou.SopNode) and node.isBypassed()
