from dataclasses import dataclass
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


def left_matrix_to_right(left_matrix: Matrix):
    return LEFT_HANDED_TO_RIGHT @ left_matrix @ RIGHT_HANDED_TO_LEFT


def right_matrix_to_left(right_matrix: Matrix):
    return RIGHT_HANDED_TO_LEFT @ right_matrix @ LEFT_HANDED_TO_RIGHT


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

    def to_json(self, *, position=True, rotation=True, scale=True, parent: str | None = None) -> TransformJson:
        json: TransformJson = {}

        if position:
            json["position"] = tuple(self.position)

        if rotation:
            rw, rx, ry, rz = self.rotation
            json["rotation"] = (rx, ry, rz, rw)

        if scale:
            json["scale"] = tuple(self.scale)

        if parent is not None:
            json["parent"] = parent

        return json

    def to_matrix(self) -> Matrix:
        return Matrix.LocRotScale(self.position, self.rotation, self.scale)

    def to_left_matrix(self) -> Matrix:
        return right_matrix_to_left(self.to_matrix())

    def to_right_matrix(self) -> Matrix:
        return left_matrix_to_right(self.to_matrix())

    def to_left(self) -> "Transform":
        return Transform.from_matrix(self.to_left_matrix())

    def to_right(self) -> "Transform":
        return Transform.from_matrix(self.to_right_matrix())
