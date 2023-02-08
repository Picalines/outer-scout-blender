from bpy.types import Context
from bpy.props import EnumProperty

from ..preferences import OWRecorderPreferences
from ..api import APIClient


class GroundBodySelectionHelper:
    ground_body: EnumProperty(
        name='Ground Body',
        items=[
            ('CURRENT', 'Current', 'Make request to SceneRecorder mod API'),
            ('Ship_Body', 'Player Ship', ''),
            ('SunStation_Pivot', 'Sun > Station', ''),
            ('CaveTwin_Body', 'Hourglass > Ember Twin', ''),
            ('TowerTwin_Body', 'Hourglass > Tower Twin', ''),
            ('TimberHearth_Body', 'Timber Hearth', ''),
            ('Moon_Body', 'Timber Hearth > Attlerock', ''),
            ('BrittleHollow_Body', 'Brittle Hollow', ''),
            ('VolcanicMoon_Body', 'Brittle Hollow > Lantern', ''),
            ('GiantsDeep_Body', 'Giants Deep', ''),
            ('OrbitalProbeCannon_Body', 'Giants Deep > Probe Cannon', ''),
            ('StatueIsland_Body', 'Giants Deep > Statue Island', ''),
            ('BrambleIsland_Body', 'Giants Deep > Bramble Island', ''),
            ('GabbroIsland_Body', 'Giants Deep > Gabbro Island', ''),
            ('ConstructionYardIsland_Body', 'Giants Deep > Construction Yard Island', ''),
            ('QuantumIsland_Body', 'Giants Deep > Quantum Island', ''),
            ('DarkBramble_Body', 'Dark Bramble', ''),
            ('DB_HubDimension_Body', 'Dark Bramble > Hub Dimension', ''),
            ('DB_AnglerNestDimension_Body', 'Dark Bramble > Angler Nest Dimension', ''),
            ('DB_ClusterDimension_Body', 'Dark Bramble > Cluster Dimension', ''),
            ('DB_Elsinore_Body', 'Dark Bramble > Elsinore Dimension', ''),
            ('DB_EscapePodDimension_Body', 'Dark Bramble > Escape Pod Dimension', ''),
            ('DB_ExitOnlyDimension_Body', 'Dark Bramble > Exit Only Dimension', ''),
            ('DB_PioneerDimension_Body', 'Dark Bramble > Pioneer Dimension', ''),
            ('DB_SmallNest_Body', 'Dark Bramble > Small Nest Dimension', ''),
            ('DB_VesselDimension_Body', 'Dark Bramble > Vessel Dimension', ''),
            ('Comet_Body', 'Interloper', ''),
            ('WhiteHole_Body', 'White Hole', ''),
            ('WhiteHoleStation_Body', 'White Hole > Station', ''),
            ('QuantumMoon_Body', 'Quantum Moon', ''),
            ('Satellite_Body', 'Satellite', ''),
            ('RingWorld_Body', 'Ring World', ''),
            ('DreamWorld_Body', 'Dream World', ''),
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
