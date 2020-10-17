import hou
from pathlib import Path
#from collections import Counter

default_folder = 'C:/Projects/MegaProject/models'
target_folder = Path(default_folder)
orig_filename = ''
tops = False
counter = 0
break_pieces = 10
isooffset_offset = -1

incr_x=4
incr_y=-1

def test():
    hou.ui.displayMessage("Hello Form Python!")

def list_fbx_iter(object):
    files_to_process = []
    iter_obj = object
    counter=0
    while True:
        try:
            element = next(iter_obj)
            if element.is_dir():
                files = [str(_path) for _path in Path(element).glob('**/*.fbx') if _path.is_file() and _path]
                files_to_process.extend(files)
                counter+=len(files)

            else:
                if element.suffix in ['.fbx','.FBX']:
                    files_to_process.append(str(element))
                    counter+=1

        except StopIteration:
            break
    return files_to_process,counter


def process_fbx_to_pieces(item,target,orig_filename,counter):
    global tops
    print ('\n')
    print ("    Working on file: %s" % orig_filename)
    print ("    Target Folder: %s" % target_folder)
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
            # move the created node right and down
            fbx[0].move(hou.Vector2(incr_x*counter,-counter))
            
            # Get and process FBX nodes
            listNodesFBX = fbx[0].children()
            
            item_count=0
            for node in listNodesFBX:
                print ('         * FBX Found object: name=' + node.name() + ', type=' + str(node.type()))
                if node.type().name() == 'geo':
                    item_count+=1
                    if tops:
                        process_with_tops(obj,node,target,orig_filename,fbx[0],item_count)
                    else:
                        create_sop_network(obj,node,target,orig_filename,fbx[0],item_count)
                else:
                    print('         - Bypassing the object...')

            
        except AttributeError:
            print ('       Error: FBX is empty or broken !')

        # auto-layout produces messy result , we will use moveToGoodPlace method
        # obj.layoutChildren()    

def process_with_tops(obj,node,target,orig_filename,root_node,item_count):
    sop, sop_path = create_sop_network(obj,node,target,orig_filename,root_node,item_count)
    rop, rop_path = create_separate_rop_network(obj,node,target,orig_filename, sop, item_count)
    top = create_top_network(sop,sop_path,rop_path)
    
    #Have to save hip file in order fo TOP to execute correctly, otherwise ROP isn't found 
    hou.hipFile.save(file_name=None, save_to_recent_files=True)
    #print ('Cleaning TOP Network '+ str(top.pth()))
    #top.dirtyAllTasks(True)
    # blocking execute PDG Graph
    print ('         - Preparing TOP Network '+ str(top.path()))
    top.displayNode().executeGraph(False, True, False, True)

    # Delay real execution until all the networks are ready
    #print ('         - Executing TOP Network '+ str(top.path()))
    #top.displayNode().executeGraph(False, True, False, False)
    #filter_static=False, block=True, generate_only=False, tops_only=True
    #print ('         - Finished executing TOP Network '+ str(top.path()))

def create_sop_network(obj,node,target,orig_filename,root_node,item_count):
    global tops
    print ("        - Creating separate Geo network for item# "+str(item_count)+". "+node.name())
    
    root = obj.createNode('geo')
    root.setName('ProcessFBX_'+orig_filename+'_'+node.name())
    
    #fbx = root.createOutputNode('object_merge', 'IMPORT_FBX_OBJ')
    fbx = root.createNode('object_merge','IMPORT_FBX_OBJ')
    fbx.parm('objpath1').set(fbx.relativePathTo(node))
    fbx.parm('xformtype').set(1)

    
    fracture = fracture_to_pieces(fbx,break_pieces)
    last = fracture
 
    if not tops:
        write_files = write_files_with_loop(last,node,target,orig_filename,root)
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
    root.move(hou.Vector2(root_node.position()[0],root_node.position()[1]+incr_y*item_count))
    #print (root.name() + " position " + str(root.position()))
    #root.moveToGoodPosition()
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
    topnetmgr.moveToGoodPosition()

    print ('        - Done')
    return topnetmgr

def create_separate_rop_network(obj,node,target,orig_filename,root_node,item_count):
    print ("        - Creating separate network for rendering/writing PDG result" + node.name())
    # ROP Output for PDG
    rop = obj.createNode('geo')
    rop.setName('RenderFBX_'+orig_filename+'_'+node.name())
    file_pdg = rop.createNode('file')
    file_pdg.parm('file').setExpression('@pdg_input')

    rop_geometry = file_pdg.createOutputNode('rop_geometry')
    #piece_folder = orig_filename + '_Pieces'
    #rop_geometry.parm('sopoutput').set(str(Path(Path(target / piece_folder).with_name('/'+node.name()+'/'+node.name()+'_`@piecevalue`')).with_suffix('.bgeo.sc')))
    #rop_geometry.parm('sopoutput').set(str(Path(target))+('\\'+piece_folder+'\\'+node.name()+'_`@piecevalue`.bgeo.sc'))
    
    dst_path = Path(target).joinpath(orig_filename+'_pieces')

    # for some reason "create intermediate folde is not working as expected, I suspect because it has an expression
    # create missing folders with python
    if not Path(dst_path).is_dir():
        try:
            Path(dst_path).mkdir(parents=True)
        except OSError:
            print ("          - Creation of the directory %s failed" % dst_path)
        else:
            print ("          - Successfully created the directory %s " % dst_path)
    
    rop_geometry.parm('sopoutput').set( str(dst_path) +'\\' +orig_filename+'_'+node.name()
           +'_piece-`padzero(2, strreplace(@piecevalue,"piece",""))`.bgeo.sc')
    
    #rop_geometry.setRenderFlag(1)

    rop.layoutChildren()
    rop.move(hou.Vector2(root_node.position()[0]-1,root_node.position()[1]-0.5))

    print ('        - Done')
    return rop, rop_geometry


def fracture_to_pieces(root, piece_count):
    print('          - Fracturing ...')

    isooffset = root.createOutputNode('isooffset')
    isooffset.parm('offset').set(isooffset_offset)

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

def write_files_with_loop(node,item,target,orig_filename,root):
    
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
    
    dst_path = Path(target).joinpath(orig_filename+'_pieces')

    # for some reason "create intermediate folde is not working as expected, I suspect because it has an expression
    # create missing folders with python
    if not Path(dst_path).is_dir():
        try:
            Path(dst_path).mkdir(parents=True)
        except OSError:
            print ("          - Creation of the directory %s failed" % dst_path)
        else:
            print ("          - Successfully created the directory %s " % dst_path)
   
    # here is the issue with / becoming \ when Path is applied on .relativePathTo( 
    #file_cache.parm('file').set(
    #    str(Path(
    #            Path(dst_path)
    #        .joinpath(orig_filename+'_'+item.name()
    #        +'_piece-`padzero(2, detail("'+file_cache.relativePathTo(metadata)+'","iteration",0))`')
    #    ).with_suffix('.bgeo.sc')
    #    ))

    # workaround
    file_cache.parm('file').set( str(dst_path) +'\\' +orig_filename+'_'+item.name()
           +'_piece-`padzero(2, detail("'+file_cache.relativePathTo(metadata)+'","iteration",0))`.bgeo.sc')

    block_end.setInput(0,file_cache)

    return block_end

def execute_all_tops():
    allNetworks = hou.node('/obj').glob('ProcessFBX*')
    for network in allNetworks:
        children = network.children()
        for node in children:
            if node.type().name().startswith('topnet'):
                print ('         - Executing TOP Network '+ str(node.path()))
                node.displayNode().executeGraph(False, False, False, False)
            
    
def processFbx2Pieces():
    global tops
    global break_pieces
    
    working_folder = default_folder
    # try to get input from the user
    tmp = hou.ui.selectFile(start_directory=default_folder, 
                title='Select Folder or File(s) For Processing', 
                collapse_sequences=False, file_type=hou.fileType.Directory, pattern='*.*',
               default_value=None, multiple_select=True, image_chooser=False,
               chooser_mode=hou.fileChooserMode.ReadAndWrite, width=0, height=0)
    if tmp:
        choices = ['Simple loop','Using TOPs']
        method_type = hou.ui.selectFromList(choices, default_choices=(0,), exclusive=True, message='Method of writing files',
                    title='Method', column_header="Choices", num_visible_rows=2, 
                    clear_on_cancel=False, width=0, height=0)
        tops=bool(method_type[0])
        print ("The chosen method is " + choices[tops])

        result, break_pieces = hou.ui.readInput('How many points would you like to use in voronoi fracture ?', 
                    buttons=('OK','Cancel'), severity=hou.severityType.Message, 
                    default_choice=0, close_choice=-1, help=None, title='Voronoi fracture points amount per model', 
                    initial_contents='10')

        if result !=-1:
            break_pieces = int(break_pieces)
        print ('Voronoi fracture points amount per model set to ' + str(break_pieces))

        print('\n\n\nSTART PROCESSING...')
        #case when multiple files are selected
        if tmp.find(';') != -1:
            tmp=tmp.split(';')
        if type(tmp) is list:
            counter=0
            for item in tmp:
                item=item.strip()
                working_folder = Path(item).parent
                target_folder = working_folder
                orig_filename = Path(item).stem
                print (" Working Folder: %s" % working_folder)
                process_fbx_to_pieces(item,target_folder,orig_filename,counter)
                counter+=1
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
                    process_fbx_to_pieces(item,target_folder,orig_filename,0)
                    print('     --------====== *** ======----------')
                else: # case when directory is chosen
                    target_folder = Path(working_folder)
                    print (" Working Folder: %s" % working_folder)

                    if any(Path(working_folder).iterdir()):
                        print("BEFORE PROCESS: listing the existing items")
                        files,count = list_fbx_iter(iter(Path(working_folder).iterdir()))
                        print ("Collected " + str(count) + " files to process.")
                        #print ("Full list: " + str(files))
                        counter=0
                        for item in files:
                            orig_filename = Path(item).stem
                            process_fbx_to_pieces(item,target_folder,orig_filename,counter)
                            counter+=1
                            print('     --------====== *** ======----------')
            except WindowsError:
                print ('Error: Path is empty or broken !')
    if tops:
        execute_all_tops()

    else: # case of dialog cancel - do not continue with the default folder
        return

    
    print("FINISHED PROCESSING.\n\n\n")


