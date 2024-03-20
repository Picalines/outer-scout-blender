from dataclasses import dataclass
from math import radians
from typing import Self, TypedDict

from mathutils import Matrix, Quaternion, Vector


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


class TransformJson(TypedDict, total=False):
    parent: str | None
    position: tuple[float, float, float] | None
    rotation: tuple[float, float, float, float] | None
    scale: tuple[float, float, float] | None


@dataclass(frozen=True)
class Transform:
    position: Vector
    rotation: Quaternion
    scale: Vector

    @staticmethod
    def from_json(json: TransformJson) -> Self:
        return Transform(
            position=Vector(json["position"] or (0, 0, 0)),
            rotation=Quaternion(json["rotation"] or (0, 0, 0, 1)),
            scale=Vector(json["scale"] or (1, 1, 1)),
        )

    @staticmethod
    def from_matrix(matrix: Matrix) -> Self:
        return Transform(*matrix.decompose())

    def unity_to_blender(self) -> Self:
        return Transform(
            position=unity_vector_to_blender(self.position),
            rotation=unity_quaternion_to_blender(self.rotation),
            scale=unity_vector_to_blender(self.scale),
        )

    def blender_to_unity(self) -> Self:
        return Transform(
            position=blender_vector_to_unity(self.position),
            rotation=blender_quaternion_to_unity(self.rotation),
            scale=blender_vector_to_unity(self.scale),
        )

    def to_json(self) -> TransformJson:
        return {
            "position": tuple(self.position),
            "rotation": tuple(self.rotation),
            "scale": tuple(self.scale),
        }

