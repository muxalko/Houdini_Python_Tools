import hou
from pathlib import Path
from collections import Counter

default_folder = 'C:/Projects/MegaProject/models/rocks/stone'
target_folder = Path(default_folder)
orig_filename = ''
tops = True

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
                if element.suffix in ['.fbx','.FBX']:
                    files_to_process.append(str(element))

        except StopIteration:
            break
    return files_to_process


def process_fbx_to_pieces(item,target,orig_filename):
    print ("    Processing " + item)
    obj = hou.node('/obj')
    fbx = hou.hipFile.importFBX(item)
    if fbx:
        print ("    ---------- Imported FBX ----------")
        print ('    ' + str(fbx))
        print ("    ---------- Imported FBX ----------")

        # Set FBX scale
        #fbx[0].parm('scale').set(0.01)
        try:
            # Get and process FBX nodes
            listNodesFBX = fbx[0].children()
            
            for node in listNodesFBX:
                print ('         * FBX Found object: name=' + node.name() + ', type=' + str(node.type()))
                if node.type().name() == 'geo':
                    if tops:
                        process_with_tops(obj,node,target,orig_filename)
                    else:
                        create_sop_network(obj,node,target,orig_filename)
                else:
                    print('      - Bypassing object...')

        except AttributeError:
            print ('       Error: FBX is empty or broken !')

        obj.layoutChildren()    

def process_with_tops(obj,node,target,orig_filename):
    sop, sop_path = create_sop_network(obj,node,target,orig_filename)
    rop, rop_path = create_separate_rop_network(obj,node,target,orig_filename)
    top = create_top_network(sop,sop_path,rop_path)
    
    #Have to save hip file in order fo TOP to execute correctly, otherwise ROP isn't found 
    hou.hipFile.save(file_name=None, save_to_recent_files=True)
    #print ('Cleaning TOP Network '+ str(top.pth()))
    #top.dirtyAllTasks(True)
    # blocking execute PDG Graph
    print ('         - Preparing TOP Network '+ str(top.path()))
    top.displayNode().executeGraph(False, True, False, True)
    print ('         - Executing TOP Network '+ str(top.path()))
    top.displayNode().executeGraph(False, True, False, False)
    #filter_static=False, block=True, generate_only=False, tops_only=True
    print ('         - Finished executing TOP Network '+ str(top.path()))
    #topnetmgr.getPDGNode().executeGraph()

        
def create_separate_rop_network(obj,node,target,orig_filename):
    print ("        - Creating separate network for rendering/writing PDG result" + node.name())
    # ROP Output for PDG
    rop = obj.createNode('geo')
    rop.setName('RenderFBX-'+node.name())
    file_pdg = rop.createNode('file')
    file_pdg.parm('file').setExpression('@pdg_input')

    rop_geometry = file_pdg.createOutputNode('rop_geometry')
    #piece_folder = orig_filename + '_Pieces'
    #rop_geometry.parm('sopoutput').set(str(Path(Path(target / piece_folder).with_name('/'+node.name()+'/'+node.name()+'_`@piecevalue`')).with_suffix('.bgeo.sc')))
    #rop_geometry.parm('sopoutput').set(str(Path(target))+('\\'+piece_folder+'\\'+node.name()+'_`@piecevalue`.bgeo.sc'))
    rop_geometry.parm('sopoutput').set(str(Path(target))+('\\'+orig_filename+'_'+node.name()+'_`@piecevalue`.bgeo.sc'))
    #rop_geometry.setRenderFlag(1)

    rop.layoutChildren()
    print ('        - Done')
    return rop, rop_geometry


def fracture_to_pieces(root, piece_count):
    print('          - Fracturing ...')

    isooffset = root.createOutputNode('isooffset')
    isooffset.parm('offset').set(-10)

    scatter = isooffset.createOutputNode('scatter::2.0')
    scatter.parm('npts').set(piece_count)

    voronoifracture = root.createOutputNode('voronoifracture::2.0')
    voronoifracture.setInput(1,scatter)


    '''
    rbdfracture = root.createOutputNode('rbdmaterialfracture::3.0','OBJECT_FRACTURE')
    rbdfracture.parm('concrete_fractureratio1').set(0.8)
    rbdfracture.parm('concrete_fractureratio2').set(0.6)
    '''
    return voronoifracture

def write_files_with_loop(node,root,target,orig_filename):
    
    #for loop 
    block_begin = node.createOutputNode('block_begin')
    block_end = block_begin.createOutputNode('block_end')
    block_begin.parm('blockpath').set(block_begin.relativePathTo(block_end))
    block_begin.parm('method').set('piece')
    block_end.parm('itermethod').set(1)
    block_end.parm('method').set(1)
    block_end.parm('class').set(0)
    block_end.parm('useattrib').set(1)
    block_end.parm('attrib').set('name')
    block_end.parm('blockpath').set(block_end.relativePathTo(block_begin))
    block_end.parm('templatepath').set(block_end.relativePathTo(block_begin))
    
    metadata = root.createNode('block_begin')
    metadata.parm('method').set('metadata')
    metadata.parm('blockpath').set(metadata.relativePathTo(block_end))

    file_cache = block_begin.createOutputNode('filecache')
    file_cache.parm('filemode').set('write')
    file_cache.parm('trange').set('off')
    file_cache.parm('file').set(str(Path(target))+('\\'+orig_filename+'_'+node.name()+'_piece-`padzero(2, detail("'+file_cache.relativePathTo(metadata)+'","iteration",0))`.bgeo.sc'))

    block_end.setInput(0,file_cache)

    return block_end

def create_sop_network(obj,node,target,orig_filename):
    print ("        - Creating separate Geo network for "+node.name())
    
    root = obj.createNode('geo')
    root.setName('ProcessFBX-'+node.name())

    #fbx = root.createOutputNode('object_merge', 'IMPORT_FBX_OBJ')
    fbx = root.createNode('object_merge','IMPORT_FBX_OBJ')
    fbx.parm('objpath1').set(fbx.relativePathTo(node))
    fbx.parm('xformtype').set(1)

    
    fracture = fracture_to_pieces(fbx,10)
    last = fracture
 
    if not tops:
        write_files = write_files_with_loop(last,root,target,orig_filename)
        last = write_files
        
     # OUTPUTS
    pieces_final = root.createNode('null')
    pieces_final.setInput(0, last)
    pieces_final.setName("OUT_PIECES")
    pieces_final.setColor(hou.Color(0, 0, 0))
    pieces_final.setUserData('nodeshape', "circle")
    pieces_final.setDisplayFlag(1)
    pieces_final.setRenderFlag(1)

    # clean up a bit
    root.layoutChildren()
    print ('        - Done')
    return root, pieces_final

def create_top_network(root_node,sop_path,rop_path):
    print ("        - Creating TOP network inside "  +root_node.path())
    # TOP Network
    topnetmgr = root_node.createNode('topnetmgr')

    geometryimport = topnetmgr.createNode('geometryimport')
    geometryimport.parm('geometrysource').set(0) # Sop import
    geometryimport.parm('soppath').set(geometryimport.relativePathTo(sop_path))  # Get our shattered geometry
    #geometryimport.parm('storagetype').set(0) # Don't create intermediate geometry
    geometryimport.parm('class').set(2) # Get Attr from Primitives
    geometryimport.parm('grouptype').set(3) # Create work item for each piece by attr (by default is "class")
    geometryimport.parm('pieceattribute').set('name') 

    # Hook ROP Fetch
    ropfetch = geometryimport.createOutputNode('ropfetch')
    ropfetch.parm('roppath').set(rop_path.path())
    ropfetch.parm('pdg_cachemode').set(2) # overwrite files
    ropfetch.setDisplayFlag(True)

    
    pipeline_end = topnetmgr.createNode('null')
    pipeline_end.setInput(0, ropfetch)
    pipeline_end.setName("PIPELINE_END")
    pipeline_end.setColor(hou.Color(0, 0, 0))
    pipeline_end.setUserData('nodeshape', "circle")

    topnetmgr.layoutChildren()
    print ('        - Done')
    return topnetmgr

def processFbx2Pieces():
    
    working_folder = default_folder
    # try to get input from the user
    tmp = hou.ui.selectFile(start_directory=default_folder, 
                title='Select Folder or File(s) For Processing', 
                collapse_sequences=False, file_type=hou.fileType.Directory, pattern='*.*',
               default_value=None, multiple_select=True, image_chooser=False,
               chooser_mode=hou.fileChooserMode.ReadAndWrite, width=0, height=0)
    
    
    if tmp:
        print('\n\n\nSTART PROCESSING...')
        #case when multiple files are selected
        if tmp.find(';') != -1:
            tmp=tmp.split(';')
        if type(tmp) is list:
            for item in tmp:
                item=item.strip()
                working_folder = Path(item).parent
                target_folder = working_folder
                orig_filename = Path(item).stem
                print (" Working Folder: %s" % working_folder)
                print (" Target Folder: %s" % target_folder)
                print ("  Working on file: %s" % orig_filename)
                process_fbx_to_pieces(item,target_folder,orig_filename)
                print('     --------====== *** ======----------')
        else: # Case when only one file chosen
            working_folder = tmp
            try:
                if Path(working_folder).is_file():
                    item = working_folder # save file path
                    orig_filename = Path(item).stem
                    working_folder = Path(working_folder).parent
                    target_folder = working_folder
                    print (" Working Folder: %s" % working_folder)
                    print (" Target Folder: %s" % target_folder)
                    print ("  Working on file: %s" % orig_filename)
                    process_fbx_to_pieces(item,target_folder,orig_filename)
                    print('     --------====== *** ======----------')
                else: # case when directory is chosen
                    target_folder = Path(working_folder)
                    print (" Working Folder: %s" % working_folder)
                    print (" Target Folder: %s" % target_folder)
                    if any(Path(working_folder).iterdir()):
                        print("BEFORE PROCESS: listing the existing items")
                        files = list_fbx_iter(iter(Path(working_folder).iterdir()))
                        print (files)
                        for item in files:
                            orig_filename = Path(item).stem
                            print ("  Working on file: %s" % orig_filename)
                            process_fbx_to_pieces(item,target_folder,orig_filename)
                            print('     --------====== *** ======----------')
            except WindowsError:
                print ('Error: Path is empty or broken !')

    else: # case of dialog cancel - do not continue with the default folder
        return

    
    print("FINISHED PROCESSING.\n\n\n")


