from bpy.types import ShaderNodeBsdfPrincipled


from typing import Any, Iterable


from bpy.types import ShaderNodeBsdfPrincipled


import bpy
from bpy.types import Panel, Operator, PropertyGroup, ShaderNodeBsdfPrincipled
from bpy.props import StringProperty, IntProperty, EnumProperty, PointerProperty, BoolProperty


def get_principled_nodes(context: bpy.types.Context) -> list[ShaderNodeBsdfPrincipled]:
    if not context.active_object:
        return []
    obj = context.active_object

    if obj and obj.active_material and obj.active_material.use_nodes and obj.active_material.node_tree:
        nodes = obj.active_material.node_tree.nodes
        items: list[ShaderNodeBsdfPrincipled] = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        return items

    return []


def get_principled_nodes_str(_, context: bpy.types.Context | None) -> list[tuple[str, str, str]]:
    if context is None:
        return []
    nodes = get_principled_nodes(context)
    return [(str(i), n.name, "") for i, n in enumerate(nodes)]


def setup_cycles(context):
    scene = context.scene
    scene.render.engine = 'CYCLES'

    # Performance Settings
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 4096
    scene.cycles.preview_samples = 1024
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.tile_size = 256

