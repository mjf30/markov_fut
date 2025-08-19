from markov_fut.state_definitions import zona_por_x, actions_for_event, construir_estados_do_evento

def test_zona_por_x():
    assert zona_por_x(0) == "D"
    assert zona_por_x(39.9) == "D"
    assert zona_por_x(40) == "M"
    assert zona_por_x(79.9) == "M"
    assert zona_por_x(80) == "A"
    assert zona_por_x(120) == "A"

def test_actions_basic():
    assert actions_for_event({"type":{"name":"Pass"}, "pass":{}}) == ["PAS"]
    assert actions_for_event({"type":{"name":"Pass"}, "pass":{"outcome":{"name":"Out"}}}) == ["PER"]
    assert actions_for_event({"type":{"name":"Ball Receipt"}}) == ["PAS"]
    assert actions_for_event({"type":{"name":"Ball Receipt"}, "outcome":{"name":"Incomplete"}}) == ["PER"]
    assert actions_for_event({"type":{"name":"Carry"}}) == ["PAS"]
    assert actions_for_event({"type":{"name":"Shot"}}) == ["FIN"]
    assert actions_for_event({"type":{"name":"Miscontrol"}}) == ["PER"]
    assert actions_for_event({"type":{"name":"Dispossessed"}}) == ["PER"]

def test_recovers_without_gk():
    assert actions_for_event({"type":{"name":"Ball Recovery"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Interception"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Interception"}, "outcome":{"name":"Success In Play"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Duel"}, "duel":{"type":{"name":"Tackle"}}, "outcome":{"name":"Won"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Duel"}, "duel":{"type":{"name":"Aerial"}}, "outcome":{"name":"Success"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Duel"}, "duel":{"type":{"name":"50/50"}}, "outcome":{"name":"Won"}}) == ["REC"]
    assert actions_for_event({"type":{"name":"Pass"}, "pass":{"type":{"name":"Interception"}}}) == ["REC","PAS"]
    # Goal Keeper não vira REC nesta versão
    assert actions_for_event({"type":{"name":"Goal Keeper"}, "outcome":{"name":"Success In Play"}}) == []
