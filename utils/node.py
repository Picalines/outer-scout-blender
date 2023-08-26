from dataclasses import dataclass
from typing import Any, Callable, Type, TypeVar

from bpy.types import Node, NodeLink, NodeSocket, NodeTree

TNode = TypeVar("TNode", bound=Node)


def create_node(node_tree: NodeTree, node_type: Type[TNode]) -> TNode:
    return node_tree.nodes.new(type=node_type.__name__)


class NodeBuilderOutputConnection:
    def __init__(self, builder: "NodeBuilder", output: int | str) -> None:
        self.builder = builder
        self.output = output


class NodeBuilder:
    built_node: Node | None = None

    @dataclass
    class DeferredConnection:
        self_input_key: int | str
        builder_to_connect: "NodeBuilder"
        output_key_to_connect: int | str | None

    _node_tree: NodeTree | None
    _node_type: Type[Node] | None
    _main_output: int | str
    _attrs: dict[str, Any]
    _default_inputs: dict[int | str, Any]
    _default_outputs: dict[int | str, Any]
    _deferred_inits: list[Callable[[Node], None]]
    _deferred_connections: list[DeferredConnection]

    def __init__(self, node_tree: NodeTree = None, node_type: Type[Node] = None):
        super().__init__()

        self._node_tree = node_tree
        self._node_type = node_type

        self._main_output = 0
        self._attrs = {}
        self._default_inputs = {}
        self._default_outputs = {}
        self._deferred_inits = []
        self._deferred_connections = []

    def sibling_builder(self, node_type: Type[Node]) -> "NodeBuilder":
        return NodeBuilder(self._node_tree, node_type)

    def set_main_output(self, output_key: int | str):
        self._assert_not_built()
        self._main_output = output_key

    def set_attr(self, attr_name: str, attr_value: Any):
        self._assert_not_built()
        self._attrs[attr_name] = attr_value

    def set_input_value(self, input_key: int | str, default_value: Any):
        self._assert_not_built()
        self._default_inputs[input_key] = default_value

    def set_output_value(self, output_key: int | str, default_value: Any):
        self._assert_not_built()
        self._default_outputs[output_key] = default_value

    def defer_init(self, init: Callable[[Node], None]):
        self._assert_not_built()
        self._deferred_inits.append(init)

    def defer_connect(self, self_input_key: int | str, builder: "NodeBuilder", builder_output_key: int | str = None):
        self._assert_not_built()
        self._deferred_connections.append(self.DeferredConnection(self_input_key, builder, builder_output_key))

    def build_input(self, self_input_key: int | str, new_node_type: Type[Node]) -> "NodeBuilder":
        self._assert_not_built()
        input_builder = self.sibling_builder(new_node_type)
        self.defer_connect(self_input_key, input_builder)
        return input_builder

    def __enter__(self) -> "NodeBuilder":
        self._assert_not_built()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._assert_not_built()

        if self._node_tree is None:
            raise ValueError(f"{NodeBuilder.__name__} exited without the node tree attribute")

        if self._node_type is None:
            raise ValueError(f"{NodeBuilder.__name__} exited without the node type attribute")

        node = create_node(self._node_tree, self._node_type)

        for attr_name, attr_value in self._attrs.items():
            setattr(node, attr_name, attr_value)

        for input_key, default_input in self._default_inputs.items():
            node.inputs[input_key].default_value = default_input

        for output_key, default_output in self._default_outputs.items():
            node.outputs[output_key].default_value = default_output

        for deferred_init in self._deferred_inits:
            deferred_init(node)

        if not exc_type:
            for connection in self._deferred_connections:
                node_to_connect = connection.builder_to_connect.built_node
                if node_to_connect is None:
                    raise ValueError(f"{self.defer_connect.__name__} method used on busy {NodeBuilder.__name__}")

                self._node_tree.links.new(
                    node_to_connect.outputs[
                        connection.output_key_to_connect
                        if connection.output_key_to_connect is not None
                        else connection.builder_to_connect._main_output
                    ],
                    node.inputs[connection.self_input_key],
                )

        self.built_node = node

    def _assert_not_built(self):
        if self.built_node is not None:
            raise ValueError(f"cannot use {self.__class__.__name__} builder method when it's finished")


def arrange_nodes(node_tree: NodeTree):
    def iterate_nodes(node: Node, visited: set[Node] = set(), level_y: int = 0, level_x: int = 0):
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
                    yield from iterate_nodes(next_node, visited, level_y + y_offset, level_x + 1)
                    y_offset += 1

    margin_x = 50
    margin_y = 300

    output_nodes = list(node for node in node_tree.nodes if any(node.inputs) and not any(node.outputs))
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


class PostfixNodeBuilder(NodeBuilder):
    @dataclass
    class MappingOptions:
        symbol: str
        node: Type[Node] | NodeBuilder
        connect: list[int | str]
        attrs: dict[str, Any]
        inputs: dict[int | str, Any]
        outputs: dict[int | str, Any]

    _postfix_expression: list[str]
    _symbol_mappings: dict[str, MappingOptions] = {}

    def __init__(self, node_tree: NodeTree, postfix_expression: list[str]):
        super().__init__(node_tree, None)

        self._postfix_expression = postfix_expression

    def map_new(
        self,
        symbol: str,
        node_type: Type[Node],
        connect: list[int | str] = None,
        attrs: dict[str, Any] = None,
        inputs: dict[int | str, Any] = None,
        outputs: dict[int | str, Any] = None,
    ):
        self._assert_not_built()

        connect = connect if connect is not None else []
        attrs = attrs if attrs is not None else {}
        inputs = inputs if inputs is not None else {}
        outputs = outputs if outputs is not None else {}

        self._symbol_mappings[symbol] = self.MappingOptions(symbol, node_type, connect, attrs, inputs, outputs)

    def map_connect(self, symbol: str, node_builder: NodeBuilder):
        self._assert_not_built()

        self._symbol_mappings[symbol] = self.MappingOptions(symbol, node_builder, [], {}, {}, {})

    def __enter__(self) -> "PostfixNodeBuilder":
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        expr_stack: list[NodeBuilder] = []

        for symbol in self._postfix_expression:
            mapping = self._symbol_mappings[symbol]

            if isinstance(mapping.node, type):
                with NodeBuilder(self._node_tree, mapping.node) as node_builder:
                    for attr_name, attr_value in mapping.attrs.items():
                        node_builder.set_attr(attr_name, attr_value)

                    for input_key, input_value in mapping.inputs.items():
                        node_builder.set_input_value(input_key, input_value)

                    for output_key, output_value in mapping.outputs.items():
                        node_builder.set_output_value(output_key, output_value)

                    if not exc_type:
                        for input_key in mapping.connect:
                            try:
                                builder_from_stack = expr_stack.pop()
                            except IndexError:
                                raise ValueError(f"not enough nodes on {PostfixNodeBuilder.__name__} stack")

                            node_builder.defer_connect(input_key, builder_from_stack, builder_from_stack._main_output)
            else:
                node_builder = mapping.node

            expr_stack.append(node_builder)

        if len(expr_stack) != 1:
            raise ValueError(
                f"invalid postfix expression in {PostfixNodeBuilder.__name__}: expected a single element left on stack"
            )

        top_expr_node = expr_stack[0]

        self._node_type = top_expr_node._node_type
        self.built_node = top_expr_node.built_node
