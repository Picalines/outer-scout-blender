from dataclasses import dataclass
from mathutils import Vector, Quaternion
import json


def unity_vector_to_blender(unity_vector: Vector) -> Vector:
    x, y, z = unity_vector.xyz
    return Vector((z, y, x))


def unity_quaternion_to_blender(unity_quaternion: Quaternion) -> Quaternion:
    x, y, z, w = unity_quaternion
    return Quaternion((-w, z, y, x))


def blender_vector_to_unity(blender_vector: Vector) -> Vector:
    x, y, z = blender_vector.xyz
    return Vector((z, y, x))


def blender_quaternion_to_unity(blender_quaternion: Quaternion) -> Quaternion:
    x, y, z, w = blender_quaternion
    return Quaternion((-w, z, y, x))


@dataclass(frozen=True)
class TransformModel:
    position: Vector
    rotation: Quaternion
    scale: Vector

    @staticmethod
    def from_json(json_str: str) -> 'TransformModel':
        json_array: list[list[float]] = json.loads(json_str)
        return TransformModel(
            position=Vector(json_array[0]),
            rotation=Quaternion(json_array[1]),
            scale=Vector(json_array[2]),
        )

    def unity_to_blender(self) -> 'TransformModel':
        return TransformModel(
            position=unity_vector_to_blender(self.position),
            rotation=unity_quaternion_to_blender(self.rotation),
            scale=unity_vector_to_blender(self.scale),
        )

    def blender_to_unity(self) -> 'TransformModel':
        return TransformModel(
            position=blender_vector_to_unity(self.position),
            rotation=blender_quaternion_to_unity(self.rotation),
            scale=blender_vector_to_unity(self.scale),
        )
