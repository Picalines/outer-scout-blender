from dataclasses import dataclass
from typing import Any, Callable, Type, TypeVar

from bpy.types import (
    Node,
    NodeLink,
    NodeSocket,
    NodeTree,
    NodeTreeInterface,
    NodeTreeInterfaceItem,
    NodeTreeInterfaceSocket,
)

TNode = TypeVar("TNode", bound=Node)


def create_node(node_tree: NodeTree, node_type: Type[TNode]) -> TNode:
    return node_tree.nodes.new(type=node_type.__name__)


class NodeTreeInterfaceBuilder:

    @dataclass
    class Socket:
        type: type
        index: int
        description: str
        default_value: Any | None
        min_value: float | None
        max_value: float | None
        hide_value: bool

    _interface: NodeTreeInterface
    _input_sockets: dict[str, Socket]
    _output_sockets: dict[str, Socket]

    def __init__(self, interface: NodeTreeInterface):
        super().__init__()

        self._interface = interface
        self._input_sockets = {}
        self._output_sockets = {}

    def add_input(
        self,
        name: str,
        socket_type: type,
        *,
        description="",
        default_value: Any | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        hide_value: bool = False,
    ):
        index = len(self._input_sockets)
        self._input_sockets[name] = self.Socket(
            socket_type, index, description, default_value, min_value, max_value, hide_value
        )

    def add_output(
        self,
        name: str,
        socket_type: type,
        *,
        description="",
        default_value: Any | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        hide_value: bool = False,
    ):
        index = len(self._output_sockets)
        self._output_sockets[name] = self.Socket(
            socket_type, index, description, default_value, min_value, max_value, hide_value
        )

    def __enter__(self) -> "NodeTreeInterfaceBuilder":
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        items: list[tuple[str, NodeTreeInterfaceItem]] = self._interface.items_tree.items()

        missing_inputs = list(self._input_sockets.keys())
        missing_outputs = list(self._output_sockets.keys())

        # The point is to keep the old sockets, not rebuild the interface every time.
        # Otherwise, node connections in the user's shader will be deleted

        for item_name, item in items:
            if not isinstance(item, NodeTreeInterfaceSocket):
                continue

            sockets_dict = self._input_sockets if item.in_out == "INPUT" else self._output_sockets
            missing_socket_list = missing_inputs if item.in_out == "INPUT" else missing_outputs

            if item_name not in sockets_dict or item_name not in missing_socket_list:
                self._interface.remove(item)
                continue

            missing_socket_list.remove(item_name)
            self._apply_socket(item, sockets_dict[item_name])

        for missing_input_name in missing_inputs:
            item = self._interface.new_socket(missing_input_name, in_out="INPUT")
            self._apply_socket(item, self._input_sockets[missing_input_name])

        for missing_output_name in missing_outputs:
            item = self._interface.new_socket(missing_output_name, in_out="OUTPUT")
            self._apply_socket(item, self._output_sockets[missing_output_name])

        self._apply_sockets_order()

    def _apply_socket(self, item: NodeTreeInterfaceSocket, socket: Socket):
        item.socket_type = socket.type.__name__
        item.description = socket.description

        item = item.type_recast()

        if socket.default_value is not None:
            item.default_value = socket.default_value

        if socket.min_value is not None:
            item.min_value = socket.min_value

        if socket.max_value is not None:
            item.max_value = socket.max_value

        item.hide_value = socket.hide_value

    def _apply_sockets_order(self):
        items: list[tuple[str, NodeTreeInterfaceItem]] = self._interface.items_tree.items()

        for item_name, item in items:
            if not isinstance(item, NodeTreeInterfaceSocket):
                continue

            sockets_dict = self._input_sockets if item.in_out == "INPUT" else self._output_sockets
            socket = sockets_dict[item_name]
            socket_index = socket.index if item.in_out == "OUTPUT" else len(self._output_sockets) + socket.index

            self._interface.move(item, socket_index)


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
            raise ValueError(f"{self.__class__.__name__} exited without the node tree attribute")

        if self._node_type is None:
            raise ValueError(f"{self.__class__.__name__} exited without the node type attribute")

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
                    raise ValueError(f"{self.defer_connect.__name__} method used on busy {self.__class__.__name__}")

                self._node_tree.links.new(
                    node_to_connect.outputs[
                        (
                            connection.output_key_to_connect
                            if connection.output_key_to_connect is not None
                            else connection.builder_to_connect._main_output
                        )
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

        linked_input_sockets = list(input for input in node.inputs if input.is_linked)

        max_level_y = level_y
        socket_i = 0
        for socket in linked_input_sockets:
            socket: NodeSocket
            for link in socket.links:
                link: NodeLink
                connected_node = link.from_node if link.from_node != node else link.to_node
                if connected_node in visited:
                    continue

                inner_level_y = yield from iterate_nodes(connected_node, visited, max_level_y + socket_i, level_x + 1)

                max_level_y = max(max_level_y, inner_level_y)
                socket_i += 1

        return max_level_y

    margin_x = 50
    margin_y = 250

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
                                raise ValueError(f"not enough nodes on {self.__class__.__name__} stack")

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
