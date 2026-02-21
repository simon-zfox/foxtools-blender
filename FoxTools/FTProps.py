import bpy
from bpy.types import Context, PropertyGroup
from bpy.props import PointerProperty, StringProperty, IntProperty, EnumProperty, BoolProperty
from . import helpers


class FTProps(PropertyGroup):

    base_name: StringProperty(default="Asset")

    res_x: IntProperty(default=512, min=1)
    res_y: IntProperty(default=512, min=1)

    principled_choice: EnumProperty(
        name="Source Principled",
        items=helpers.get_principled_nodes_str)

    baked_view: BoolProperty(default=True)

    @staticmethod
    def getprop(context: Context) -> 'FTProps':
        return getattr(context.scene, "FoxToolsProp")

    @staticmethod
    def setprop():
        setattr(bpy.types.Scene, "FoxToolsProp", PointerProperty(type=FTProps))

    @staticmethod
    def delprop():
        delattr(bpy.types.Scene, "FoxToolsProp")
