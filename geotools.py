import hou as hou


def print_shape_types():
    editor = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    shapes = editor.nodeShapes()
    print shapes


def generate_house():
    # Get scene root node
    # obj = hou.node('/obj/')

    try:
        selected_nodes = hou.selectedNodes()  # By selection
        for node in selected_nodes:
            print (node.type())
            if node.type().name() != "geo":
                print ("Error: Wrong node type (" + str(node.type().name()) + ") is selected!")
                return
            else:
                # Base
                base = node.createNode("box")
                base.setName("base")

                base.parm('ty').setExpression('ch("scale")*ch("sizey")*0.5')

                # Roof
                roof = node.createNode("box")
                roof.setName("roof")

                roof.parm('ty').setExpression('bbox("../base",D_YMAX)+ch("scale")*ch("sizey")*0.5')

                # select roof polygons to collapse
                collapse_group = node.createNode("groupcreate")
                collapse_group.setInput(0, roof)
                collapse_group.parm('groupname').set('collapse')
                collapse_group.parm('basegroup').set('5')

                xform = node.createNode('xform')
                xform.setInput(0, collapse_group)

                #print([(parm.name(), parm.eval()) for parm in xform.parms()])

                #  is there a difference ???
                xform.parm('group').setExpression('chs("'+xform.relativePathTo(collapse_group)+'/groupname")')
                #xform.parm('group').set('`chs("'+xform.relativePathTo(collapse_group)+'/groupname")`')

                xform.parm('sx').set(0)
                xform.parm('sz').set(0)


                # OUTPUTS

                base_final = node.createNode('null')
                base_final.setName("OUT_BASE")
                base_final.setColor(hou.Color(0, 0, 0))
                base_final.setUserData('nodeshape', "circle")
                base_final.setInput(0, base)

                roof_final = node.createNode('null')
                roof_final.setName("OUT_ROOF")
                roof_final.setColor(hou.Color(0, 0, 0))
                roof_final.setUserData('nodeshape', "circle")
                roof_final.setInput(0, xform)

                # Merge everything
                merge = node.createNode("merge")
                merge.setNextInput(base_final)
                merge.setNextInput(roof_final)

                # Output
                output = node.createNode('output')
                output.setInput(0, merge)
                output.setDisplayFlag(True)
                output.setRenderFlag(True)

                # Auto-arrange nodes
                node.layoutChildren()

    except IndexError:
        print ("Error: Nothing is selected!")