"""
Founder Copilot backend regression tests.
Covers: root, /founder/analyze, /founder/profile, /founder/report,
/founder/chat (SSE streaming), and /founder/chat/{sid} history.
"""
import os
import json
import uuid
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session_id():
    return f"TEST_{uuid.uuid4()}"


@pytest.fixture(scope="module")
def sample_idea_payload(session_id):
    return {
        "session_id": session_id,
        "idea": "AI-powered B2B SaaS for Indian MSMEs to automate GST invoicing and reconciliation with vernacular support",
        "target_market": "Indian MSMEs tier 2 and tier 3",
        "business_model": "B2B SaaS",
        "founders_count": 2,
        "state": "Karnataka",
        "stage": "mvp",
        "dpiit_registered": True,
        "funding_goal": "seed VC raise",
    }


# ------ 1. Health ------
def test_root_ok():
    r = requests.get(f"{API}/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("service") == "founder-copilot"


# ------ 2. Analyze ------
def test_analyze_returns_full_report(sample_idea_payload, session_id):
    r = requests.post(f"{API}/founder/analyze", json=sample_idea_payload, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["session_id"] == session_id
    rep = data["report"]
    # validation
    v = rep["validation"]
    for k in ["market_signal", "feasibility", "competition", "overall", "signals", "top_priority"]:
        assert k in v, f"missing {k}"
    assert 0 <= v["overall"] <= 100
    assert v["top_priority"].get("area") and v["top_priority"].get("action")
    # funding
    f = rep["funding"]
    assert "schemes" in f and isinstance(f["schemes"], list) and len(f["schemes"]) > 0
    sc = f["schemes"][0]
    for k in ["name", "amount", "fit_score", "status", "url"]:
        assert k in sc
    # entity
    e = rep["entity"]
    for k in ["entity", "rationale", "doc_checklist"]:
        assert k in e
    assert isinstance(e["doc_checklist"], list) and len(e["doc_checklist"]) > 0
    # gtm
    g = rep["gtm"]
    for k in ["tactics", "first_100_users_plan", "north_star_metric", "cadence"]:
        assert k in g
    # growth
    gr = rep["growth"]
    assert "opportunities" in gr and len(gr["opportunities"]) > 0
    op = gr["opportunities"][0]
    assert "url" in op and "fit_score" in op


# ------ 3. Report GET ------
def test_report_persisted(session_id):
    r = requests.get(f"{API}/founder/report/{session_id}")
    assert r.status_code == 200
    doc = r.json()
    assert doc["session_id"] == session_id
    assert "report" in doc


def test_report_unknown_returns_404():
    r = requests.get(f"{API}/founder/report/TEST_nonexistent_{uuid.uuid4()}")
    assert r.status_code == 404


# ------ 4. Profile GET ------
def test_profile_known(session_id):
    r = requests.get(f"{API}/founder/profile/{session_id}")
    assert r.status_code == 200
    d = r.json()
    assert d.get("known") is True
    assert "summary" in d and len(d["summary"]) > 0


def test_profile_unknown():
    r = requests.get(f"{API}/founder/profile/TEST_unknown_{uuid.uuid4()}")
    assert r.status_code == 200
    d = r.json()
    assert d.get("known") is False


# ------ 5. Chat SSE ------
def _consume_sse(resp):
    deltas = []
    done = False
    tool_call = False
    error = None
    for raw in resp.iter_lines():
        if not raw:
            continue
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        try:
            obj = json.loads(payload)
        except Exception:
            continue
        if "delta" in obj:
            deltas.append(obj["delta"])
        if obj.get("done"):
            done = True
        if obj.get("tool_call"):
            tool_call = True
        if obj.get("error"):
            error = obj["error"]
    return "".join(deltas), done, tool_call, error


def test_chat_empty_returns_400(session_id):
    r = requests.post(f"{API}/founder/chat", json={"session_id": session_id, "message": "   "})
    assert r.status_code == 400


def test_chat_grounded_streaming(session_id):
    r = requests.post(
        f"{API}/founder/chat",
        json={"session_id": session_id, "message": "Given my idea, what entity type did you recommend and why?"},
        stream=True,
        timeout=120,
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
    text, done, tool_call, error = _consume_sse(r)
    assert error is None, f"stream error: {error}"
    assert done is True
    assert len(text) > 20
    # grounded — should mention entity or Indian context
    lowered = text.lower()
    assert any(k in lowered for k in ["pvt ltd", "opc", "llp", "private limited", "one person", "limited liability"]), \
        f"assistant answer not grounded in entity report: {text[:400]}"


def test_chat_second_turn_remembers(session_id):
    r = requests.post(
        f"{API}/founder/chat",
        json={"session_id": session_id, "message": "what did you recommend for my entity again?"},
        stream=True,
        timeout=120,
    )
    assert r.status_code == 200
    text, done, _, error = _consume_sse(r)
    assert error is None
    assert done
    lowered = text.lower()
    assert any(k in lowered for k in ["pvt ltd", "private limited", "opc", "llp"]), text[:400]


def test_chat_tool_call_growth(session_id):
    r = requests.post(
        f"{API}/founder/chat",
        json={"session_id": session_id, "message": "find me more hackathons I can apply to"},
        stream=True,
        timeout=180,
    )
    assert r.status_code == 200
    text, done, tool_call, error = _consume_sse(r)
    assert error is None, error
    assert done
    assert len(text) > 20


def test_chat_history_persisted(session_id):
    r = requests.get(f"{API}/founder/chat/{session_id}")
    assert r.status_code == 200
    d = r.json()
    msgs = d.get("messages", [])
    assert len(msgs) >= 4  # at least 2 user + 2 assistant turns from previous tests
    roles = [m["role"] for m in msgs]
    assert "user" in roles and "assistant" in roles
