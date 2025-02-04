from collections import namedtuple

import pytest

from hypertunity.domain import Domain, Sample, DomainNotIterableError, DomainSpecificationError


def test_valid():
    with pytest.raises(TypeError):
        Domain({{"b": lambda x: x}, [0, 0.1]})
    with pytest.raises(DomainSpecificationError):
        Domain({1: {"b": [2, 3]}, "c": [0, 0.1]})
    with pytest.raises(DomainSpecificationError):
        Domain({"a": {"b": (1, 2, 3, 4)}, "c": [0, 0.1]})
    with pytest.raises(DomainSpecificationError):
        Domain({"a": {"b": lambda x: x}, "c": [0, 0.1]})
    with pytest.raises(ValueError):
        # this one should fail from the ast.literal_eval parsing
        Domain('{"a": {"b": lambda x: x}, "c": [0, 0.1]}')
    Domain({"a": {"b": {0, 1}}, "c": [0, 0.1]})
    Domain('{"a": {"b": {0, 1}}, "c": [0, 0.1]}')


def test_eq():
    d1 = Domain({"a": {"b": [2, 3]}, "c": [0, 0.1]})
    d2 = Domain({"a": {"b": [2, 3]}, "c": [0, 0.1]})
    assert d1 == d2


def test_flatten():
    dom = Domain({"a": {"b": [0, 1]}, "c": [0, 0.1]})
    assert dom.flatten() == {("a", "b"): [0, 1], ("c",): [0, 0.1]}


def test_addition():
    domain_all = Domain({"a": [1, 2], "b": {"c": {1, 2, 3}, "d": {"o1", "o2"}}, "e": {3, 4, 5}})
    domain_1 = Domain({"a": [1, 2], "b": {"c": {1, 2, 3}}})
    domain_2 = Domain({"b": {"d": {"o1", "o2"}}})
    domain_3 = Domain({"e": {3, 4, 5}})
    assert domain_1 + domain_2 + domain_3 == domain_all
    with pytest.raises(ValueError):
        _ = domain_1 + domain_1


def test_serialisation():
    domain = Domain({"a": [1, 2], "b": {"c": {1, 2, 3}, "d": {"o1", "o2"}}})
    serialised = domain.serialise()
    deserialised = Domain.deserialise(serialised)
    assert deserialised == domain


def test_as_dict():
    dict_domain = {"a": {"b": [2, 3]}, "c": [0, 0.1]}
    domain = Domain(dict_domain)
    assert domain.as_dict() == dict_domain


def test_as_namedtuple():
    domain = Domain({"a": {"b": {2, 3, 4}}, "c": [0, 0.1]})
    nt = domain.as_namedtuple()
    assert nt.a == namedtuple("_", "b")({2, 3, 4})
    assert nt.a.b == {2, 3, 4}
    assert nt.c == [0, 0.1]


def test_from_list():
    lst = [(("a", "b"), {2, 3, 4}), (("c",), {0, 0.1}), (("d", "e", "f"), {0, 1}), (("d", "g"), {2, 3})]
    domain_true = Domain({"a": {"b": {2, 3, 4}}, "c": {0, 0.1}, "d": {"e": {"f": {0, 1}}, "g": {2, 3}}})
    domain_from_list = Domain.from_list(lst)
    assert domain_true == domain_from_list
    assert lst == list(domain_true.flatten().items())


def test_iter():
    with pytest.raises(DomainNotIterableError):
        list(iter(Domain({"a": {"b": {2, 3, 4}}, "c": [0, 0.1]})))
    discrete_domain = Domain({"a": {"b": {2, 3, 4}, "j": {"d": {5, 6}, "f": {"g": {7}}}}, "c": {"op1", 0.1}})
    all_samples = set(iter(discrete_domain))
    assert all_samples == {
        Sample({'a': {'b': 2, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 3, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 4, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 2, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 3, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 4, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 'op1'}),
        Sample({'a': {'b': 2, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 0.1}),
        Sample({'a': {'b': 3, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 0.1}),
        Sample({'a': {'b': 4, 'j': {'d': 5, 'f': {'g': 7}}}, 'c': 0.1}),
        Sample({'a': {'b': 2, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 0.1}),
        Sample({'a': {'b': 3, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 0.1}),
        Sample({'a': {'b': 4, 'j': {'d': 6, 'f': {'g': 7}}}, 'c': 0.1})
    }


def test_sampling():
    domain = Domain({"a": {"b": {2, 3, 4}}, "c": [0, 0.1]})
    for i in range(10):
        sample = domain.sample()
        assert sample["a"]["b"] in {2, 3, 4} and 0. <= sample["c"] <= 0.1


def test_split_by_type():
    domain = Domain({"x": [1, 2], "y": {-3, 2, 5}, "z": {"small", 1, 0.1}})
    discr, cat, cont = domain.split_by_type()
    assert sum(domain.split_by_type(), Domain({})) == domain
    assert discr == Domain({"y": {-3, 2, 5}})
    assert cat == Domain({"z": {"small", 1, 0.1}})
    assert cont == Domain({"x": [1, 2]})
