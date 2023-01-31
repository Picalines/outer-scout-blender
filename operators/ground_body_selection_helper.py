from bpy.types import Context
from bpy.props import EnumProperty

from ..preferences import OWRecorderPreferences
from ..api import APIClient


class GroundBodySelectionHelper:
    ground_body: EnumProperty(
        name="Ground Body",
        items=[
            ('CURRENT', 'Current', 'Make request to SceneRecorder mod API'),
            ('BrittleHollow_Body', 'BrittleHollow', ''),
            ('Comet_Body', 'Comet', ''),
            ('DarkBramble_Body', 'DarkBramble', ''),
            ('DB_AnglerNestDimension_Body', 'DB_AnglerNestDimension', ''),
            ('DB_ClusterDimension_Body', 'DB_ClusterDimension', ''),
            ('DB_Elsinore_Body', 'DB_Elsinore', ''),
            ('DB_EscapePodDimension_Body', 'DB_EscapePodDimension', ''),
            ('DB_ExitOnlyDimension_Body', 'DB_ExitOnlyDimension', ''),
            ('DB_HubDimension_Body', 'DB_HubDimension', ''),
            ('DB_PioneerDimension_Body', 'DB_PioneerDimension', ''),
            ('DB_SmallNest_Body', 'DB_SmallNest', ''),
            ('DB_VesselDimension_Body', 'DB_VesselDimension', ''),
            ('DreamWorld_Body', 'DreamWorld', ''),
            ('GiantsDeep_Body', 'GiantsDeep', ''),
            ('Moon_Body', 'Moon', ''),
            ('OrbitalProbeCannon_Body', 'OrbitalProbeCannon', ''),
            ('Probe_Body', 'Probe', ''),
            ('QuantumMoon_Body', 'QuantumMoon', ''),
            ('RingWorld_Body', 'RingWorld', ''),
            ('Satellite_Body', 'Satellite', ''),
            ('Ship_Body', 'Ship', ''),
            ('StaticRing_Body', 'StaticRing', ''),
            ('SunStation_Pivot', 'SunStation', ''),
            ('Sun_Body', 'Sun', ''),
            ('TimberHearth_Body', 'TimberHearth', ''),
            ('VolcanicMoon_Body', 'VolcanicMoon', ''),
            ('WhiteHole_Body', 'WhiteHole', ''),
        ],
    )

    def get_ground_body_name(self, context: APIClient | OWRecorderPreferences | Context) -> str | None:
        if self.ground_body != 'CURRENT':
            return self.ground_body

        if isinstance(context, Context):
            preferences = OWRecorderPreferences.from_context(context)
            context = APIClient(preferences)

        if isinstance(context, OWRecorderPreferences):
            context = APIClient(context)

        return context.get_ground_body_name()

    def invoke(self, context: Context, _):
        return context.window_manager.invoke_props_dialog(self)
