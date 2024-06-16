from dataclasses import dataclass

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator

from ..api import APIClient, Transform
from ..bpy_register import bpy_register
from ..properties.scene_props import SceneProperties
from ..utils import operator_do


@dataclass
class ParentSuggestion:
    object_name: str
    ow_scene: str


ORIGIN_PARENT_SUGGESTIONS = {
    "Player": ParentSuggestion("Player_Body", ow_scene="SolarSystem"),
    "Player Ship": ParentSuggestion("Ship_Body", ow_scene="SolarSystem"),
    "Sun > Station": ParentSuggestion("SunStation_Body", ow_scene="SolarSystem"),
    "Hourglass > Ember Twin": ParentSuggestion("CaveTwin_Body", ow_scene="SolarSystem"),
    "Hourglass > Tower Twin": ParentSuggestion("TowerTwin_Body", ow_scene="SolarSystem"),
    "Hourglass > Tower Twin > ATP": ParentSuggestion("TimeLoopRing_Body", ow_scene="SolarSystem"),
    "Timber Hearth": ParentSuggestion("TimberHearth_Body", ow_scene="SolarSystem"),
    "Timber Hearth > Attlerock": ParentSuggestion("Moon_Body", ow_scene="SolarSystem"),
    "Brittle Hollow": ParentSuggestion("BrittleHollow_Body", ow_scene="SolarSystem"),
    "Brittle Hollow > Lantern": ParentSuggestion("VolcanicMoon_Body", ow_scene="SolarSystem"),
    "Giants Deep": ParentSuggestion("GiantsDeep_Body", ow_scene="SolarSystem"),
    "Giants Deep > Probe Cannon": ParentSuggestion("OrbitalProbeCannon_Body", ow_scene="SolarSystem"),
    "Giants Deep > Statue Island": ParentSuggestion("StatueIsland_Body", ow_scene="SolarSystem"),
    "Giants Deep > Bramble Island": ParentSuggestion("BrambleIsland_Body", ow_scene="SolarSystem"),
    "Giants Deep > Gabbro Island": ParentSuggestion("GabbroIsland_Body", ow_scene="SolarSystem"),
    "Giants Deep > Construction Yard Island": ParentSuggestion("ConstructionYardIsland_Body", ow_scene="SolarSystem"),
    "Giants Deep > Quantum Island": ParentSuggestion("QuantumIsland_Body", ow_scene="SolarSystem"),
    "Dark Bramble": ParentSuggestion("DarkBramble_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Hub Dimension": ParentSuggestion("DB_HubDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Angler Nest Dimension": ParentSuggestion("DB_AnglerNestDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Cluster Dimension": ParentSuggestion("DB_ClusterDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Elsinore Dimension": ParentSuggestion("DB_Elsinore_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Escape Pod Dimension": ParentSuggestion("DB_EscapePodDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Exit Only Dimension": ParentSuggestion("DB_ExitOnlyDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Pioneer Dimension": ParentSuggestion("DB_PioneerDimension_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Small Nest Dimension": ParentSuggestion("DB_SmallNest_Body", ow_scene="SolarSystem"),
    "Dark Bramble > Vessel Dimension": ParentSuggestion("DB_VesselDimension_Body", ow_scene="SolarSystem"),
    "Interloper": ParentSuggestion("Comet_Body", ow_scene="SolarSystem"),
    "White Hole": ParentSuggestion("WhiteHole_Body", ow_scene="SolarSystem"),
    "White Hole > Station": ParentSuggestion("WhiteHoleStation_Body", ow_scene="SolarSystem"),
    "Quantum Moon": ParentSuggestion("QuantumMoon_Body", ow_scene="SolarSystem"),
    "Satellite": ParentSuggestion("Satellite_Body", ow_scene="SolarSystem"),
    "Ring World": ParentSuggestion("RingWorld_Body", ow_scene="SolarSystem"),
    "Dream World": ParentSuggestion("DreamWorld_Body", ow_scene="SolarSystem"),
    "Vessel": ParentSuggestion("Vessel_Body", ow_scene="EyeOfTheUniverse"),
    "Eye Of The Universe": ParentSuggestion("EyeOfTheUniverse_Body", ow_scene="EyeOfTheUniverse"),
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
        items=[
            ("BODY_CENTER", "Body Center", ""),
            ("PLAYER_FEET", "Player", ""),
            ("SURVEYOR_PROBE", "Scout", ""),
        ],
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

    @operator_do
    def execute(self, context):
        scene_props = SceneProperties.from_context(context)
        api_client = APIClient.from_context(context)

        if self.detect_origin_parent:
            origin_parent = api_client.get_ground_body().then()["name"]
            ow_scene = api_client.get_environment().then()["outerWildsScene"]
        elif self.origin_parent in ORIGIN_PARENT_SUGGESTIONS:
            suggestion = ORIGIN_PARENT_SUGGESTIONS[self.origin_parent]
            origin_parent = suggestion.object_name
            ow_scene = suggestion.ow_scene
        else:
            origin_parent = self.origin_parent
            ow_scene = scene_props.outer_wilds_scene

        match self.origin_location:
            case "BODY_CENTER":
                origin_position = (0, 0, 0)
                origin_rotation = (0, 0, 0, 1)

            case "PLAYER_FEET":
                player_body_object = api_client.get_object("Player_Body", origin=origin_parent).then()

                player_transform = Transform.from_json(player_body_object["transform"])
                origin_position = tuple(player_transform.position)
                origin_rotation = tuple(player_transform.rotation)

            case "SURVEYOR_PROBE":
                probe_object = api_client.get_object("Probe_Body", origin=origin_parent).then()

                probe_transform = Transform.from_json(probe_object["transform"])
                origin_position = tuple(probe_transform.position)
                origin_rotation = tuple(probe_transform.rotation)

        scene_props.outer_wilds_scene = ow_scene
        scene_props.origin_parent = origin_parent
        scene_props.origin_position = origin_position
        scene_props.origin_rotation = origin_rotation

        context.area.tag_redraw()
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

