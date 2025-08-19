
from markov_fut.segmentation import build_transitions_for_match

def _ev(idx, team, poss, etype, x=60, ptype=None):
    e = {
        "index": idx, "period": 1, "minute": 0, "second": idx,
        "team": {"id": team}, "possession_team": {"id": poss},
        "type": {"name": etype}, "location": [x,40],
    }
    if etype == "Pass" and ptype:
        e["pass"] = {"type": {"name": ptype}}
    return e

def test_turnover_live():
    events = [_ev(1,1,1,"Pass",65), _ev(2,2,2,"Ball Recovery",66)]
    t = build_transitions_for_match(events, my_team_id=1)
    assert ("P_M_PER","S_M_REC") in t
