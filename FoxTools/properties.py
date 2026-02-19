from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, EnumProperty, BoolProperty
from . import helpers


class FoxToolsProperties(PropertyGroup):

    base_name: StringProperty(default="Asset")

    res_x: IntProperty(default=2048, min=1)
    res_y: IntProperty(default=2048, min=1)

    principled_choice: EnumProperty(
        name="Source Principled", items=helpers.get_principled_nodes
    )

    baked_view: BoolProperty(default=True)
