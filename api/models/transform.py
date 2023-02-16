from dataclasses import dataclass
from math import radians
from mathutils import Vector, Quaternion, Matrix
import json

from bpy.types import Object


def unity_vector_to_blender(unity_vector: Vector) -> Vector:
    x, y, z = unity_vector.xyz
    return Vector((z, y, x))


def unity_quaternion_to_blender(unity_quaternion: Quaternion) -> Quaternion:
    x, y, z, w = unity_quaternion
    return Quaternion((-w, z, y, x)) @ Quaternion((0, 1, 0), radians(90))


def blender_vector_to_unity(blender_vector: Vector) -> Vector:
    x, y, z = blender_vector.xyz
    return Vector((z, y, x))


def blender_quaternion_to_unity(blender_quaternion: Quaternion) -> Quaternion:
    w, x, y, z = blender_quaternion
    return Quaternion((z, w, x, y)) @ Quaternion((0, 1, 0), radians(-90))


TransformModelJSON = list[list[float]]


@dataclass(frozen=True)
class TransformModel:
    position: Vector
    rotation: Quaternion
    scale: Vector

    @staticmethod
    def from_json(json: TransformModelJSON) -> "TransformModel":
        return TransformModel(
            position=Vector(json[0]),
            rotation=Quaternion(json[1]),
            scale=Vector(json[2]),
        )

    @staticmethod
    def from_json_str(json_str: str) -> "TransformModel":
        json_array: TransformModelJSON = json.loads(json_str)
        return TransformModel.from_json(json_array)

    @staticmethod
    def from_matrix(matrix: Matrix) -> "TransformModel":
        return TransformModel(*matrix.decompose())

    def unity_to_blender(self) -> "TransformModel":
        return TransformModel(
            position=unity_vector_to_blender(self.position),
            rotation=unity_quaternion_to_blender(self.rotation),
            scale=unity_vector_to_blender(self.scale),
        )

    def blender_to_unity(self) -> "TransformModel":
        return TransformModel(
            position=blender_vector_to_unity(self.position),
            rotation=blender_quaternion_to_unity(self.rotation),
            scale=blender_vector_to_unity(self.scale),
        )

    def to_json(self) -> TransformModelJSON:
        return [
            [*self.position],
            [*self.rotation],
            [*self.scale],
        ]

    def to_json_str(self) -> str:
        return json.dumps(self.to_json())

    def to_matrix(self) -> Matrix:
        return Matrix.LocRotScale(self.position, self.rotation, self.scale)

    def apply_local(self, object: Object):
        object.location = self.position
        object.scale = self.scale
        object.rotation_mode = "QUATERNION"
        object.rotation_quaternion = self.rotation
