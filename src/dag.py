from typing import Any, Callable, Dict, List, Tuple, Set


class DAG:
    def __init__(self):
        # nodes: node name -> tuple(compute_func, list of dependency names)
        self.nodes: Dict[str, Tuple[Callable[..., Any], List[str]]] = {}

    def add_node(self, name: str, func: Callable[..., Any], dependencies: List[str]) -> None:
        """
        Register a node in the DAG.

        :param name: Name of the node to register
        :param func: Callable that computes the node's value from its dependencies
        :param dependencies: List of node names that this node depends on
        :raises ValueError: If a node with the same name is already registered
        """
        if name in self.nodes:
            raise ValueError(f"Node '{name}' is already registered")
        self.nodes[name] = (func, dependencies)


def compute(graph: DAG, inputs: Dict[str, Any], outputs: List[str]) -> Dict[str, Any]:
    """
    Compute the specified output nodes in the given DAG.

    Args:
        graph (DAG): The DAG instance containing node definitions and their dependencies.
        inputs (Dict[str, Any]): Mapping of node names to provided values; these values
            override any computed values for those nodes.
        outputs (List[str]): List of node names to compute and return.

    Returns:
        Dict[str, Any]: Mapping of requested output node names to their computed values.

    Raises:
        KeyError: If a requested output or required dependency is undefined.
        ValueError: If a cycle is detected in the graph dependencies.
    """
    # Validate requested outputs before any computation
    unknown_nodes = {*inputs.keys(), *outputs} - graph.nodes.keys()
    if unknown_nodes:
        raise KeyError(f"Nodes {list(unknown_nodes)} are not defined in the graph.")

    cache: Dict[str, Any] = dict(inputs)
    visiting: Set[str] = set()

    def _eval(node: str) -> Any:
        # Return provided or cached value if available
        if node in cache:
            return cache[node]

        if node in visiting:
            raise ValueError(f"Cycle detected at node '{node}'")

        visiting.add(node)
        func, deps = graph.nodes[node]

        # Evaluate dependencies first
        args = [_eval(dep) for dep in deps]

        # Compute and cache the value
        value = func(*args)
        cache[node] = value

        visiting.remove(node)
        return value

    return {out: _eval(out) for out in outputs}
