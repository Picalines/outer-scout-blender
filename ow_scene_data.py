from typing import TypedDict, TypeVar, Type
import json

from bpy.types import Context, Object, Scene
from mathutils import Vector, Quaternion

from .utils import iter_recursive


TTypedDict = TypeVar('TTypedDict', bound=TypedDict)


class RecorderSettingsData(TypedDict):
    outputDir: str
    framerate: int
    width: int
    height: int
    hdri_face_size: int
    hide_player_model: bool
    hdri_in_feet: bool


class TransformData(TypedDict):
    position: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    scale: tuple[float, float, float]


class GameObjectData(TypedDict):
    name: str
    transform: TransformData


class PlayerData(TypedDict):
    transform: TransformData


class CameraData(TypedDict):
    fov: float
    near_clip_plane: float
    far_clip_plane: float
    transform: TransformData


class OWSceneData(TypedDict):
    recorded_frames: int
    recorder_settings: RecorderSettingsData
    player: PlayerData
    ground_body: GameObjectData
    player_camera: CameraData
    background_camera: CameraData
    depth_camera: CameraData


class PlainMeshData(TypedDict):
    transform: TransformData
    game_object_path: str


class StreamedMeshData(TypedDict):
    transform: TransformData
    asset_path: str

class OWMeshesData(TypedDict):
    plain_meshes: list[PlainMeshData]
    streamed_meshes: list[StreamedMeshData]


def unity_vector_to_blender(unity_vector: tuple[float, float, float]):
    x, y, z = unity_vector
    return (z, y, x)


def unity_quaternion_to_blender(unity_quaternion: tuple[float, float, float]):
    x, y, z, w = unity_quaternion
    return (-w, z, y, x)


def unity_transform_to_blender(unity_transform: TransformData):
    return TransformData(
        position=unity_vector_to_blender(unity_transform['position']),
        rotation=unity_quaternion_to_blender(unity_transform['rotation']),
        scale=unity_transform['scale'])


def load_ow_json_data(path: str, typed_dict_type: Type[TTypedDict]) -> TTypedDict:
    with open(path, 'rb') as file:
        meshes_data: typed_dict_type = json.loads(file.read())

    for _, value in iter_recursive(meshes_data):
        if isinstance(value, dict) and 'transform' in value:
            value['transform'] = unity_transform_to_blender(value['transform'])

    return meshes_data


def apply_transform_data(object: Object, transform_data: TransformData):
    object.location = Vector(transform_data['position'])
    object.scale = Vector(transform_data['scale'])
    object.rotation_mode = 'QUATERNION'
    object.rotation_quaternion = Quaternion(transform_data['rotation'])


def apply_scene_settings(context: Context, scene: Scene, ow_data: OWSceneData):
    scene.frame_end = ow_data['recorded_frames']
    scene.render.fps = ow_data['recorder_settings']['framerate']
    scene.render.resolution_x = ow_data['recorder_settings']['width']
    scene.render.resolution_y = ow_data['recorder_settings']['height']
    scene.render.film_transparent = True
    context.view_layer.use_pass_z = True
