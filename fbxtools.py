import hou
from pathlib import Path
from collections import Counter

default_folder = 'C:/Projects/MegaProject/models/vegetation/grass'

def test():
    hou.ui.displayMessage("Hello Form Python!")

def list_fbx_iter(object):
    files_to_process = []
    iter_obj = object
    while True:
        try:
            element = next(iter_obj)
            if element.is_dir():
                files = [str(_path) for _path in Path(element).glob('**/*.fbx') if _path.is_file() and _path]
                files_to_process.extend(files)
            else:
                files_to_process.append(str(element))

        except StopIteration:
            break
    return files_to_process


def process_fbx_to_pieces(item):
    print ("Processing " + item)
    fbx = hou.hipFile.importFBX(item)
    if fbx:
        print ("---------- Imported FBX ----------")
        print (fbx)
        print ("---------- Imported FBX ----------")

        # Set FBX scale
        fbx[0].parm('scale').set(0.01)

        # Get and print FBX nodes
        listNodesFBX = fbx[0].children()
        for node in listNodesFBX:
            print (node)
            print (node.type().name())
            if node.type().name() == 'geo':
                print ("Creating separate network for "+node.name())
                obj = hou.node('/obj')
                root = obj.createNode('geo')
                root.setName('ProcessFBX-'+node.name())

                #fbx = root.createOutputNode('object_merge', 'IMPORT_FBX_OBJ')
                fbx = root.createNode('object_merge','IMPORT_FBX_OBJ')
                fbx.parm('objpath1').set(node.path())
                fbx.parm('xformtype').set(1)

                fbx.setDisplayFlag(1)
                fbx.setRenderFlag(1)





def processFbx2Pieces():
    working_folder = default_folder
    working_folder = hou.ui.selectFile(start_directory=default_folder, title='Select Folder For Processing', collapse_sequences=True, file_type=hou.fileType.Directory, pattern='*',
               default_value=None, multiple_select=False, image_chooser=False,
               chooser_mode=hou.fileChooserMode.ReadAndWrite, width=0, height=0)

    print ("Working Folder: %s" % working_folder)
    if any(Path(working_folder).iterdir()):
        print("BEFORE PROCESS: listing the existing items")
        files = list_fbx_iter(iter(Path(working_folder).iterdir()))
        print (files)
        for item in files:
            process_fbx_to_pieces(item)




