
from __future__ import annotations
from tests._util import get_modules, ev, normalize_probs

pkg, seg, viz = get_modules()

def assert_true(cond, msg="expected condition to hold"):
    if not cond: raise AssertionError(msg)

def assert_eq(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or f"expected {a} == {b}")

def assert_in(x, col, msg=None):
    if x not in col:
        raise AssertionError(msg or f"{x} not in collection")

def assert_not_in(x, col, msg=None):
    if x in col:
        raise AssertionError(msg or f"{x} unexpectedly in collection")

def test_1_turnover_live_P_to_S():
    events = [
        ev(1,1,1,"Pass",55),
        ev(2,2,2,"Ball Recovery",57),
        ev(3,2,2,"Pass",72),
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    assert_in(("P_M_PER","S_M_REC"), t, "turnover vivo P->S não gerou PER/REC")
    # não houve STOP; deve haver aresta S_M_REC->S_A_PAS
    assert_in(("S_M_REC","S_A_PAS"), t)

def test_2_stop_cuts_chain():
    events = [
        ev(1,1,1,"Pass",30),
        ev(2,1,1,"Foul Committed"),
        ev(3,2,2,"Pass",30, ptype="Free Kick"),  # reinício S
        ev(4,2,2,"Pass",45),
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    # não deve ligar através da parada (1 -> 3)
    assert_not_in(("P_D_PAS","S_D_PAS"), t, "ligou através de STOP")
    # mas deve ligar 3 -> 4
    assert_in(("S_D_PAS","S_M_PAS"), t)

def test_3_restart_begins_new_segment():
    events = [
        ev(1,1,1,"Out"),
        ev(2,1,1,"Pass",35, ptype="Throw-in"),   # reinício P
        ev(3,1,1,"Pass",48),
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    # sem ligação 1->2, mas com 2->3
    assert_not_in(("P_D_PAS","P_D_PAS"), t)  # sanity
    assert_in(("P_D_PAS","P_M_PAS"), t)

def test_4_multiple_turnovers_in_live_segment():
    events = [
        ev(1,1,1,"Pass",60),
        ev(2,2,2,"Ball Recovery",61),    # P->S
        ev(3,1,1,"Ball Recovery",62),    # S->P
        ev(4,1,1,"Pass",70),
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    assert_in(("P_M_PER","S_M_REC"), t, "faltou P->S")
    assert_in(("S_M_PER","P_M_REC"), t, "faltou S->P")

def test_5_shot_then_recovery_does_not_overwrite_FIN():
    events = [
        ev(1,1,1,"Shot",78),             # FIN
        ev(2,2,2,"Ball Recovery",62),    # posse muda viva
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    assert_in(("P_A_FIN","S_M_REC"), t)
    # o lado P não deve virar PER
    assert_not_in(("P_A_PER","S_M_REC"), t)

def test_6_self_loop_counted_when_same_state_repeats():
    events = [
        ev(1,1,1,"Pass",65),
        ev(2,1,1,"Pass",65),  # mesmo estado P_M_PAS
        ev(3,1,1,"Pass",72),  # mesmo prefixo, outra zona (não loop)
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    assert_in(("P_M_PAS","P_M_PAS"), t, "esperava self-loop em passes consecutivos na mesma zona")

def test_7_cut_on_stop_false_glues_across():
    events = [
        ev(1,1,1,"Pass",30),
        ev(2,1,1,"Out"),                     # STOP
        ev(3,1,1,"Pass",35, ptype="Throw-in")# reinício P
    ]
    t = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=False, coerce_turnovers=True)
    # com cut_on_stop=False, vai colar 1->3
    assert_in(("P_D_PAS","P_D_PAS"), t)

def test_8_visualize_smoke_and_threshold_alias(tmp_path):
    # monta probs básicos a partir de um cenário simples
    events = [
        ev(1,1,1,"Pass",55),
        ev(2,2,2,"Ball Recovery",57),
        ev(3,2,2,"Pass",72),
        ev(4,2,2,"Shot",80),
    ]
    counts = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    probs, out_tot = normalize_probs(counts)
    out = tmp_path / "fullcheck_graph.png"
    # threshold= (alias) deve ser aceito
    viz.plot_graph(probs, str(out), threshold=0.0, topk_per_node=None, mirror_s=True, counts=counts, min_count=0)
    assert out.exists(), "plot não gerou arquivo"

def test_9_prob_rows_sum_to_1():
    events = [
        ev(1,1,1,"Pass",55),
        ev(2,2,2,"Ball Recovery",57),
        ev(3,2,2,"Pass",72),
        ev(4,2,2,"Shot",80),
    ]
    counts = seg.build_transitions_for_match(events, my_team_id=1, cut_on_stop=True, coerce_turnovers=True)
    probs, out_tot = normalize_probs(counts)
    # soma ~1 por origem (apenas nas linhas com saída)
    from collections import defaultdict
    row = defaultdict(float)
    for (a,b), p in probs.items():
        row[a] += p
    for a, s in row.items():
        assert abs(s - 1.0) < 1e-8, f"soma de probs da linha {a} = {s}, esperava 1.0"

TESTS = [
    test_1_turnover_live_P_to_S,
    test_2_stop_cuts_chain,
    test_3_restart_begins_new_segment,
    test_4_multiple_turnovers_in_live_segment,
    test_5_shot_then_recovery_does_not_overwrite_FIN,
    test_6_self_loop_counted_when_same_state_repeats,
    test_7_cut_on_stop_false_glues_across,
    test_8_visualize_smoke_and_threshold_alias,
    test_9_prob_rows_sum_to_1,
]
