from parameter import Parameter


def test_parameter_creation():
    p = Parameter('test')
    assert p is not None


def test_parameter_update():
    p = Parameter('test')
    p.update(0, 10)
    p.update(1, 11)
    p.update(2, 12)

    assert p.t_series == [0, 1, 2]
    assert p.v_series == [10, 11, 12]


def test_parameter_points():
    p = Parameter('test')
    p.update(0, 10)
    p.update(1, 11)
    p.update(2, 12)

    assert p.points() == [(0, 10), (1, 11), (2, 12)]
