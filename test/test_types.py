from practicebank import types, exceptions

from pytest import raises

def test_add_child_raises_if_child_is_of_improper_type():
    prob = types.Problem()
    another_problem = types.Problem()

    with raises(exceptions.IllegalChild):
        prob.add_child(another_problem)


def test_iterate_over_children():
    prob_1 = types.Problem()

    prob_1.add_child(types.NormalText("hello"))
    prob_1.add_child(types.NormalText("world"))

    prob_2 = types.Problem()

    prob_2.add_child(types.NormalText("hello"))
    prob_2.add_child(types.NormalText("world"))

    assert list(prob_1.children()) == list(prob_2.children())


def test_equality_is_evaluated_recursively():
    prob_1 = types.Problem()

    prob_1.add_child(types.NormalText("hello"))
    prob_1.add_child(types.NormalText("world"))

    prob_2 = types.Problem()

    prob_2.add_child(types.NormalText("hello"))
    prob_2.add_child(types.NormalText("world"))

    assert list(prob_1.children()) == list(prob_2.children())
