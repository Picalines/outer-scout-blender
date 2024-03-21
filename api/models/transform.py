from dataclasses import dataclass
from typing import TypedDict

from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix, Quaternion, Vector

UNITY_TO_BLENDER = axis_conversion(from_forward="-Z", from_up="Y", to_forward="Y", to_up="Z")
BLENDER_TO_UNITY = axis_conversion(from_forward="Y", from_up="Z", to_forward="-Z", to_up="Y")


def unity_transform_to_blender(unity_matrix: Matrix) -> Matrix:
    return UNITY_TO_BLENDER.to_4x4() @ unity_matrix


def blender_transform_to_unity(blender_matrix: Matrix) -> Matrix:
    return BLENDER_TO_UNITY.to_4x4() @ blender_matrix


def unity_vector_to_blender(unity_vector: Vector | tuple[float, float, float]) -> Vector:
    return UNITY_TO_BLENDER @ Vector(unity_vector)


def unity_quaternion_to_blender(unity_quaternion: Quaternion | tuple[float, float, float, float]) -> Quaternion:
    w, x, y, z = unity_quaternion
    return UNITY_TO_BLENDER.to_quaternion() @ Quaternion((w, x, y, z))


def blender_vector_to_unity(blender_vector: Vector | tuple[float, float, float]) -> Vector:
    return BLENDER_TO_UNITY @ Vector(blender_vector)


def blender_quaternion_to_unity(blender_quaternion: Quaternion | tuple[float, float, float, float]) -> Quaternion:
    x, y, z, w = BLENDER_TO_UNITY.to_quaternion() @ blender_quaternion
    return Quaternion((x, y, z, w))


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
    def from_json(json: TransformJson) -> "Transform":
        return Transform(
            position=Vector(json["position"] or (0, 0, 0)),
            rotation=Quaternion(json["rotation"] or (0, 0, 0, 1)),
            scale=Vector(json["scale"] or (1, 1, 1)),
        )

    @staticmethod
    def from_matrix(matrix: Matrix) -> "Transform":
        return Transform(*matrix.decompose())

    def unity_to_blender(self) -> "Transform":
        return Transform(
            position=unity_vector_to_blender(self.position),
            rotation=unity_quaternion_to_blender(self.rotation),
            scale=unity_vector_to_blender(self.scale),
        )

    def blender_to_unity(self) -> "Transform":
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

