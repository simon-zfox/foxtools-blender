# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from .AutoBakeCleanup import AutoBakeCleanup
from .UIPanel import VIEW3D_PT_NPanel, UIToggleBakeView
from .AutoBake import AutoBake
from .FTProps import FTProps


bl_info = {
    "name": "FoxTools",
    "author": "zfox-simon",
    "description": "",
    "blender": (5, 0, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}


classes: tuple = (
    FTProps,
    AutoBake,
    AutoBakeCleanup,
    UIToggleBakeView,
    VIEW3D_PT_NPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    FTProps.setprop()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    FTProps.delprop()
