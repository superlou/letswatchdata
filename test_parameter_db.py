from parameter import ParameterDB, Parameter


def test_parameter_db_creation():
    pdb = ParameterDB()
    assert isinstance(pdb, ParameterDB)


def test_create():
    pdb = ParameterDB()
    p = pdb.create('test')
    assert isinstance(p, Parameter)


def test_get():
    pdb = ParameterDB()
    pdb.create('test')
    p = pdb.get('test')
    assert isinstance(p, Parameter)


def test_save_and_load():
    pdb = ParameterDB()
    pdb.create('test1')
    pdb.get('test1').update(0, 1)
    pdb.create('test2')
    pdb.get('test2').update(0, 5)
    pdb.get('test2').update(1, 10)

    pdb.save('tmp.pdb')

    loaded_pdb = ParameterDB.load('tmp.pdb')
    assert loaded_pdb.get('test1').points() == [(0, 1)]
    assert loaded_pdb.get('test2').points() == [(0, 5), (1, 10)]
