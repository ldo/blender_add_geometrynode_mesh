#+
# Blender add-on to create a mesh object with no actual innate geometry:
# instead, all its geometry is dynamically generated via a Geometry Nodes
# modifier. Requires Blender 2.93 (pre-release).
#
# Copyright 2021 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>. Licensed
# under CC-BY-SA <http://creativecommons.org/licenses/by-sa/4.0/>.
#-

import sys
import math
import enum
import bpy
from mathutils import \
    Matrix, \
    Vector

bl_info = \
    {
        "name" : "Geometry-Node Mesh",
        "author" : "Lawrence D'Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 2, 1),
        "blender" : (2, 93, 0),
        "location" : "Add > Mesh",
        "description" :
            "generates an empty mesh with a Geometry-Nodes modifier.",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Add Mesh",
    }

#+
# Useful stuff
#-

class NodeContext :
    "convenience class for assembling a nicely-laid-out node graph."

    def __init__(self, graph, location, clear = False) :
        "“graph” is the node tree for which to manage the addition of nodes." \
        " “location” is the initial location at which to start placing new nodes." \
        " clear indicates whether to get rid of any existing nodes or not."
        self.graph = graph
        self._location = [location[0], location[1]]
        if clear :
            for node in self.graph.nodes :
                self.graph.nodes.remove(node)
            #end for
        #end if
    #end __init__

    def step_across(self, width) :
        "returns the current position and advances it across by width."
        result = self._location[:]
        self._location[0] += width
        return result
    #end step_across

    def step_down(self, height) :
        "returns the current position and advances it down by height."
        result = self._location[:]
        self._location[1] -= height
        return result
     #end step_down

    @property
    def pos(self) :
        "the current position (read/write)."
        return (self._location[0], self._location[1])
    #end pos

    @pos.setter
    def pos(self, pos) :
        self._location[:] = [pos[0], pos[1]]
    #end pos

    def node(self, type, pos) :
        "creates a new node of type “type” at position “pos”, and returns it."
        node = self.graph.nodes.new(type)
        node.location = (pos[0], pos[1])
        return node
    #end node

    def link(self, frôm, to) :
        "creates a link from output “frôm” to input “to”."
        self.graph.links.new(frôm, to)
    #end link

#end NodeContext

def deselect_all(node_graph) :
    for node in node_graph.nodes :
        node.select = False
    #end for
#end deselect_all

#+
# Mainline
#-

class NODE_MESH(enum.Enum) :
    CIRCLE = ("Circle", "GeometryNodeMeshCircle")
    CONE = ("Cone", "GeometryNodeMeshCone")
    CUBE = ("Cube", "GeometryNodeMeshCube")
    CYLINDER = ("Cylinder", "GeometryNodeMeshCylinder")
    GRID = ("Grid/Plane", "GeometryNodeMeshGrid")
    ICO_SPHERE = ("Ico Sphere", "GeometryNodeMeshIcoSphere")
    LINE = ("Line", "GeometryNodeMeshLine")
    UV_SPHERE = ("UV Sphere", "GeometryNodeMeshUVSphere")

    @property
    def label(self) :
        return \
            self.value[0]
    #end label

    @property
    def typename(self) :
        return \
            self.value[1]
    #end typename

#end NODE_MESH
NODE_MESH_DEFAULT = NODE_MESH.CUBE

class AddGeometryNodeMesh(bpy.types.Operator) :
    bl_idname = "add_mesh.geometry_node_mesh"
    bl_label = "Geometry-Node Mesh"
    bl_description = "generates an empty mesh with a Geometry-Nodes modifier"
    bl_context = "objectmode"
    bl_options = {"REGISTER", "UNDO"}

    meshtype : bpy.props.EnumProperty \
      (
        default = NODE_MESH_DEFAULT.typename,
        items = tuple
          (
            (item.typename, item.label, item.label)
            for item in sorted(NODE_MESH.__members__.values(), key = lambda i : i.label)
          ),
        name = "Mesh Type"
      )
    position : bpy.props.FloatVectorProperty \
      (
        name = "position",
        description = "where to position the books (initially at the 3D cursor)",
      )

    def draw(self, context) :
        the_col = self.layout.column(align = True)
        the_col.prop(self, "meshtype", text = "Mesh Type")
    #end draw

    def action_common(self, context, redoing) :
        if redoing :
            pos = Vector(tuple(self.position))
        else :
            pos = context.scene.cursor.location.copy()
        #end if
        bpy.ops.object.select_all(action = "DESELECT")
        new_mesh_name = new_obj_name = "GeomNodeMesh"
        new_mesh = bpy.data.meshes.new(new_mesh_name)
        new_mesh_name = new_mesh.name
        # TBD some initial dummy material
        new_mesh.from_pydata([], [], []) # nothing to see here
        new_obj = bpy.data.objects.new(new_mesh_name, new_mesh)
        new_obj_name = new_obj.name
        new_obj.matrix_basis = Matrix.Translation(pos)
        geom_mod = new_obj.modifiers.new("Geometry", "NODES")
        ctx = NodeContext(geom_mod.node_group, (0, 0), clear = True)
        geom = ctx.node(self.meshtype, ctx.step_across(200))
        output = ctx.node("NodeGroupOutput", ctx.step_across(100))
        ctx.link(geom.outputs[0], output.inputs[0])
        deselect_all(ctx.graph)
        context.scene.collection.objects.link(new_obj)
        bpy.data.objects[new_obj_name].select_set(True)
        context.view_layer.objects.active = new_obj
        for this_vertex in new_mesh.vertices :
            this_vertex.select = True # usual Blender default for newly-created object
        #end for
        status = {"FINISHED"}
        return \
            status
    #end execute

    def execute(self, context) :
        return \
            self.action_common(context, True)
    #end execute

    def invoke(self, context, event) :
        return \
            self.action_common(context, False)
    #end invoke

#end AddGeometryNodeMesh

def add_invoke_item(self, context) :
    self.layout.operator \
        (AddGeometryNodeMesh.bl_idname, text = AddGeometryNodeMesh.bl_label)
#end add_invoke_item

_classes_ = \
    (
        AddGeometryNodeMesh,
    )

def register() :
    for ċlass in _classes_ :
        bpy.utils.register_class(ċlass)
    #end for
    bpy.types.VIEW3D_MT_mesh_add.append(add_invoke_item)
#end register

def unregister() :
    bpy.types.VIEW3D_MT_mesh_add.remove(add_invoke_item)
#end unregister

if __name__ == "__main__" :
    register()
#end if
