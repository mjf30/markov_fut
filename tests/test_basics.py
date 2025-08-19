from markov_fut.state_definitions import zona_por_x, acao, construir_estado

def test_zona():
    assert zona_por_x(0) == "D"
    assert zona_por_x(40) == "M"
    assert zona_por_x(80) == "A"

def test_aliases():
    # acao/comstruir_estado são aliases compatíveis
    ev = {"type":{"name":"Pass"}, "pass":{}, "team":{"id":1}, "location":[50,40]}
    assert acao(ev) == "PAS"
    assert construir_estado(ev, 1) == "P_M_PAS"
