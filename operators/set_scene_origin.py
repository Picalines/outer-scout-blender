import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator

from ..api import APIClient, Transform
from ..bpy_register import bpy_register
from ..properties.scene_props import SceneProperties

ORIGIN_PARENT_SUGGESTIONS = {
    "Player": "Player_Body",
    "Player Ship": "Ship_Body",
    "Sun > Station": "SunStation_Pivot",
    "Hourglass > Ember Twin": "CaveTwin_Body",
    "Hourglass > Tower Twin": "TowerTwin_Body",
    "Hourglass > Tower Twin > ATP": "TimeLoopRing_Body",
    "Timber Hearth": "TimberHearth_Body",
    "Timber Hearth > Attlerock": "Moon_Body",
    "Brittle Hollow": "BrittleHollow_Body",
    "Brittle Hollow > Lantern": "VolcanicMoon_Body",
    "Giants Deep": "GiantsDeep_Body",
    "Giants Deep > Probe Cannon": "OrbitalProbeCannon_Body",
    "Giants Deep > Statue Island": "StatueIsland_Body",
    "Giants Deep > Bramble Island": "BrambleIsland_Body",
    "Giants Deep > Gabbro Island": "GabbroIsland_Body",
    "Giants Deep > Construction Yard Island": "ConstructionYardIsland_Body",
    "Giants Deep > Quantum Island": "QuantumIsland_Body",
    "Dark Bramble": "DarkBramble_Body",
    "Dark Bramble > Hub Dimension": "DB_HubDimension_Body",
    "Dark Bramble > Angler Nest Dimension": "DB_AnglerNestDimension_Body",
    "Dark Bramble > Cluster Dimension": "DB_ClusterDimension_Body",
    "Dark Bramble > Elsinore Dimension": "DB_Elsinore_Body",
    "Dark Bramble > Escape Pod Dimension": "DB_EscapePodDimension_Body",
    "Dark Bramble > Exit Only Dimension": "DB_ExitOnlyDimension_Body",
    "Dark Bramble > Pioneer Dimension": "DB_PioneerDimension_Body",
    "Dark Bramble > Small Nest Dimension": "DB_SmallNest_Body",
    "Dark Bramble > Vessel Dimension": "DB_VesselDimension_Body",
    "Interloper": "Comet_Body",
    "White Hole": "WhiteHole_Body",
    "White Hole > Station": "WhiteHoleStation_Body",
    "Quantum Moon": "QuantumMoon_Body",
    "Satellite": "Satellite_Body",
    "Ring World": "RingWorld_Body",
    "Dream World": "DreamWorld_Body",
}


def search_origin_parent(_self, _context, _edit_text):
    return ORIGIN_PARENT_SUGGESTIONS.keys()


@bpy_register
class SetSceneOriginOperator(Operator):
    """Sets the Outer Scout scene origin location"""

    bl_idname = "outer_scout.set_origin"
    bl_label = "Set Scene Origin"

    detect_origin_parent: BoolProperty(
        name="Detect current planet",
        description="Attach the origin to the planet you are currently on in the game",
        default=False,
    )

    origin_parent: StringProperty(
        name="Origin Parent",
        description="Attach the origin to the specified GameObject. You can specify the name of any GameObject",
        default="Timber Hearth",
        search=search_origin_parent,
        search_options={"SUGGESTION"},
    )

    origin_location: EnumProperty(
        name="Origin Location",
        items=[("CENTER", "Center", ""), ("PLAYER_FEET", "Player", ""), ("SURVEYOR_PROBE", "Scout", "")],
    )

    def draw(self, _) -> None:
        layout = self.layout
        layout.use_property_split = True

        layout.prop(self, "origin_location")
        layout.prop(self, "detect_origin_parent")

        if not self.detect_origin_parent:
            layout.prop(self, "origin_parent")

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        api_client = APIClient.from_context(context)

        if self.detect_origin_parent:
            ground_body = api_client.get_ground_body()
            if ground_body is None:
                self.report({"ERROR"}, "failed to get current ground body")
                return {"CANCELLED"}

            origin_parent = ground_body["name"]
        elif self.origin_parent in ORIGIN_PARENT_SUGGESTIONS:
            origin_parent = ORIGIN_PARENT_SUGGESTIONS[self.origin_parent]
        else:
            origin_parent = self.origin_parent

        match self.origin_location:
            case "CENTER":
                origin_position = (0, 0, 0)
                origin_rotation = (0, 0, 0, 1)

            case "PLAYER_FEET":
                player_body_object = api_client.get_object("Player_Body", origin=origin_parent)
                if not player_body_object:
                    self.report({"ERROR"}, "failed to get player location")
                    return {"CANCELLED"}

                player_transform = Transform.from_json(player_body_object["transform"])
                origin_position = tuple(player_transform.position)
                origin_rotation = tuple(player_transform.rotation)

            case "SURVEYOR_PROBE":
                probe_object = api_client.get_object("Probe_Body", origin=origin_parent)
                if not probe_object:
                    self.report({"ERROR"}, "failed to get scout location")
                    return {"CANCELLED"}

                probe_transform = Transform.from_json(probe_object["transform"])
                origin_position = tuple(probe_transform.position)
                origin_rotation = tuple(probe_transform.rotation)

        scene_properties = SceneProperties.from_context(context)
        scene_properties.origin_parent = origin_parent
        scene_properties.origin_position = origin_position
        scene_properties.origin_rotation = origin_rotation

        context.area.tag_redraw()
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        if scene_properties.has_ground_body:
            bpy.ops.outer_scout.align_ground_body()

        return {"FINISHED"}

