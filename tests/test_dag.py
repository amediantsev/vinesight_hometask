import pytest

from src.dag import DAG, compute


# Example compute_* functions for testing
def compute_A() -> int:
    return 42  # arbitrary constant


def compute_B(a: int) -> int:
    return a * 2


def compute_C(a: int) -> int:
    return a + 1


def compute_D(a: int, b: int, c: int) -> int:
    return a + b + c


def compute_E(a: int, c: int, d: int) -> int:
    return a * c - d


@pytest.fixture
def example_graph() -> DAG:
    graph = DAG()
    graph.add_node("A", compute_A, [])
    graph.add_node("B", compute_B, ["A"])
    graph.add_node("C", compute_C, ["A"])
    graph.add_node("D", compute_D, ["A", "B", "C"])
    graph.add_node("E", compute_E, ["A", "C", "D"])
    return graph


def test_compute_with_input_override(example_graph):
    # Given A=5, compute D and E
    inputs = {"A": 5}
    outputs = ["D", "E"]
    result = compute(example_graph, inputs, outputs)
    # Expected values
    a = 5
    b = compute_B(a)
    c = compute_C(a)
    expected_D = compute_D(a, b, c)
    expected_E = compute_E(a, c, expected_D)
    assert result["D"] == expected_D
    assert result["E"] == expected_E


def test_compute_with_only_B_override(example_graph):
    # With only B provided, compute D using default compute_A and compute_C
    inputs = {"B": 1}
    result = compute(example_graph, inputs, ["D"])
    # A = compute_A(), C = compute_C(A)
    a = compute_A()
    c = compute_C(a)
    expected_D = compute_D(a, inputs["B"], c)
    assert result["D"] == expected_D


def test_input_override_prefers_provided_value(example_graph):
    # Both A and B provided; B should not be recomputed from A
    inputs = {"A": 1, "B": 2}
    result = compute(example_graph, inputs, ["D"])
    expected_C = compute_C(1)
    expected_D = 1 + 2 + expected_C
    assert result["D"] == expected_D


def test_compute_single_node(example_graph):
    # Compute only C
    inputs = {"A": 3}
    result = compute(example_graph, inputs, ["C"])
    assert result == {"C": compute_C(3)}


def test_no_unnecessary_computations(example_graph, monkeypatch):
    # Spy on compute_D to ensure it's only called when needed
    called = {"D": False}

    def fake_compute_D(a, b, c):
        called["D"] = True
        return compute_D(a, b, c)

    example_graph.nodes["D"] = (fake_compute_D, ["A", "B", "C"])
    # E requires D, so D should be called
    compute(example_graph, {"A": 2}, ["E"])
    assert called["D"] is True
    # Reset and compute C only; D should not be called
    called["D"] = False
    compute(example_graph, {"A": 2}, ["C"])
    assert called["D"] is False


def test_duplicate_node_registration():
    # Adding a node with an existing name should raise ValueError
    graph = DAG()
    graph.add_node("A", compute_A, [])

    with pytest.raises(ValueError) as excinfo:
        graph.add_node("A", compute_A, [])

    assert "already registered" in str(excinfo.value)


def test_missing_node_definition(example_graph):
    # Requesting an undefined node should raise KeyError
    with pytest.raises(KeyError) as excinfo:
        compute(example_graph, {}, ["Z"])
    assert str(excinfo.value) == '"Nodes [\'Z\'] are not defined in the graph."'


def test_cycle_detection():
    # Graph with a simple cycle X -> Y -> X should raise ValueError
    graph = DAG()

    dummy_return_func = lambda x: x

    graph.add_node("X", dummy_return_func, ["Y"])
    graph.add_node("Y", dummy_return_func, ["X"])

    with pytest.raises(ValueError) as excinfo:
        compute(graph, {}, ["X"])

    assert "Cycle detected" in str(excinfo.value)
