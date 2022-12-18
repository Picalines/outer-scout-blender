from typing import TypedDict
import json

from bpy.types import Context, Object, Scene
from mathutils import Vector, Quaternion


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


def load_ow_scene_data(path: str) -> OWSceneData:
    with open(path, 'rb') as file:
        scene_data: OWSceneData = json.loads(file.read())

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

    for data in scene_data.values():
        if isinstance(data, dict) and 'transform' in data:
            data['transform'] = unity_transform_to_blender(data['transform'])

    return scene_data


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
