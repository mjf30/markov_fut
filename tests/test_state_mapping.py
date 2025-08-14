from markov_futebol.state_definitions import zona_por_x, acao

def test_zona_por_x():
    assert zona_por_x(0) == "D"
    assert zona_por_x(39.9) == "D"
    assert zona_por_x(40) == "M"
    assert zona_por_x(79.9) == "M"
    assert zona_por_x(80) == "A"
    assert zona_por_x(120) == "A"

def test_acao_pass():
    evt = {"type": {"name": "Pass"}, "pass": {}}
    assert acao(evt) == "PAS"
    evt2 = {"type": {"name": "Pass"}, "pass": {"outcome": {"name": "Incomplete"}}}
    assert acao(evt2) == "PER"
