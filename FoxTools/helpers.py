import bpy
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, IntProperty, EnumProperty, PointerProperty, BoolProperty


def get_principled_nodes(self, context):
    items = []
    obj = context.active_object
    if obj and obj.active_material and obj.active_material.use_nodes:
        nodes = obj.active_material.node_tree.nodes
        principled = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        for i, node in enumerate(principled):
            items.append((str(i), node.name, ""))
    return items


def setup_cycles(context):
    scene = context.scene
    scene.render.engine = 'CYCLES'

    # Performance Settings
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 4096
    scene.cycles.preview_samples = 1024
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.tile_size = 256


def cleanup_previous_bake(mat):
    nodes = mat.node_tree.nodes
    images_to_remove = []

    for node in list(nodes):

        # Bake Frame entfernen
        if node.type == 'FRAME' and node.label == "BAKE_BLOCK":
            for child in list(node.children):
                if child.type == "TEX_IMAGE" and child.image:
                    images_to_remove.append(child.image)
                nodes.remove(child)
            nodes.remove(node)

        # Mix Shader Switch entfernen
        if node.type == "MIX_SHADER" and "is_bake_switch" in node:
            nodes.remove(node)

    # Alte Images löschen wenn unbenutzt
    for img in images_to_remove:
        if img.users == 0:
            bpy.data.images.remove(img)
