from typing import Generic, TypeVar, Type, Callable, Iterable, Any

from bpy.types import NodeTree, Node, NodeSocket, NodeLink

TNode = TypeVar("TNode", bound=Node)


def create_node(node_tree: NodeTree, node_type: Type[TNode]) -> TNode:
    return node_tree.nodes.new(type=node_type.__name__)


class NodeBuilderOutputConnection:
    def __init__(self, builder: "NodeBuilder", output: int | str) -> None:
        self.builder = builder
        self.output = output


class NodeBuilder(Generic[TNode]):
    def __init__(
        self,
        node_type: Type[TNode],
        *,
        output: int | str = 0,
        init: Callable[[TNode], None] | Iterable[Callable[[TNode], None]] | None = None,
        **inputs: Any | "NodeBuilder"
    ):
        super().__init__()
        self.node_type = node_type
        self.output = output
        self.init_node = init
        self.built_node: None | TNode = None

        self.inputs: dict[int | str, Any | NodeBuilder] = {}
        for key, value in inputs.items():
            if key.startswith("_"):
                key = key[1:]
            if key.isdecimal():
                key = int(key)
            self.inputs[key] = value

    def connect_output(self, output: int | str):
        return NodeBuilderOutputConnection(self, output)

    def build(self, node_tree: NodeTree) -> TNode:
        if self.built_node is not None:
            return self.built_node

        self.built_node = create_node(node_tree, self.node_type)

        if callable(self.init_node):
            self.init_node(self.built_node)

        if isinstance(self.init_node, Iterable):
            for init_node in self.init_node:
                init_node(self.built_node)

        for input_key, value in self.inputs.items():
            if isinstance(value, NodeBuilderOutputConnection):
                if value.builder.built_node is None:
                    raise ValueError()

                node_tree.links.new(
                    value.builder.built_node.outputs[value.output],
                    self.built_node.inputs[input_key],
                )
                continue

            if isinstance(value, NodeBuilder):
                connected_node: Node = value.build(node_tree)
                node_tree.links.new(
                    connected_node.outputs[value.output],
                    self.built_node.inputs[input_key],
                )
                continue

            if isinstance(input_key, int) or input_key in self.built_node.inputs.keys():
                self.built_node.inputs[input_key].default_value = value
            else:
                setattr(self.built_node, input_key, value)

        return self.built_node


def arrange_nodes(node_tree: NodeTree):
    def iterate_nodes(
        node: Node, visited: set[Node] = set(), level_y: int = 0, level_x: int = 0
    ):
        yield (node, level_y, level_x)
        visited.add(node)

        linked_inputs = (input for input in node.inputs if input.is_linked)

        socket: NodeSocket
        y_offset = 0
        for socket in linked_inputs:
            link: NodeLink
            for link in socket.links:
                next_node = link.from_node if link.from_node != node else link.to_node

                if next_node not in visited:
                    yield from iterate_nodes(
                        next_node, visited, level_y + y_offset, level_x + 1
                    )
                    y_offset += 1

    margin_x = 50
    margin_y = 300

    output_nodes = list(
        node for node in node_tree.nodes if any(node.inputs) and not any(node.outputs)
    )
    primary_output_node = output_nodes[0]

    location_y = 0
    for node in output_nodes:
        node.location = (0, location_y)
        location_y -= node.dimensions.y + margin_y

    nodes = list(iterate_nodes(primary_output_node))

    max_node_width = max(node.width for node, _, _ in nodes)
    max_node_height = max(node.height for node, _, _ in nodes)

    for node, level_y, level_x in nodes:
        node.location = (
            -level_x * (max_node_width + margin_x),
            -level_y * (max_node_height + margin_y),
        )
