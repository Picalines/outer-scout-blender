from dataclasses import dataclass
from math import radians
from typing import TypedDict

from mathutils import Matrix, Quaternion, Vector

RIGHT_HANDED_TO_LEFT = Matrix(
    (
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1),
    )
)

LEFT_HANDED_TO_RIGHT = RIGHT_HANDED_TO_LEFT.inverted()

UNITY_TO_BLENDER_ROTATION = Matrix.Rotation(radians(-90), 4, "X") @ Matrix.Rotation(radians(180), 4, "Z")

BLENDER_TO_UNITY_ROTATION = UNITY_TO_BLENDER_ROTATION.inverted()


def unity_matrix_to_blender(unity_matrix: Matrix):
    return LEFT_HANDED_TO_RIGHT @ unity_matrix @ RIGHT_HANDED_TO_LEFT @ UNITY_TO_BLENDER_ROTATION


def blender_matrix_to_unity(blender_matrix: Matrix):
    return RIGHT_HANDED_TO_LEFT @ blender_matrix @ LEFT_HANDED_TO_RIGHT @ BLENDER_TO_UNITY_ROTATION


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
        rx, ry, rz, rw = json["rotation"] or (0, 0, 0, 1)
        return Transform(
            position=Vector(json["position"] or (0, 0, 0)),
            rotation=Quaternion((rw, rx, ry, rz)),
            scale=Vector(json["scale"] or (1, 1, 1)),
        )

    @staticmethod
    def from_matrix(matrix: Matrix) -> "Transform":
        return Transform(*matrix.decompose())

    def to_json(self) -> TransformJson:
        return {
            "position": tuple(self.position),
            "rotation": tuple(self.rotation),
            "scale": tuple(self.scale),
        }

    def to_matrix(self) -> Matrix:
        return Matrix.LocRotScale(self.position, self.rotation, self.scale)

