import pytest

from core import db, states


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    c.execute("INSERT INTO jobs (id, channel, status, created_at, updated_at) VALUES ('j1', 'k1', 'queued', 'x', 'x')")
    return c


def test_full_happy_path(conn):
    for s in states.PIPELINE[1:] + [states.APPROVED, states.SCHEDULED, states.PUBLISHED]:
        states.transition(conn, "j1", s)
    assert db.get_job(conn, "j1")["status"] == states.PUBLISHED


def test_cannot_skip_steps(conn):
    with pytest.raises(states.InvalidTransition):
        states.transition(conn, "j1", states.KEYFRAMES_READY)


def test_published_is_terminal(conn):
    for s in states.PIPELINE[1:] + [states.APPROVED, states.SCHEDULED, states.PUBLISHED]:
        states.transition(conn, "j1", s)
    with pytest.raises(states.InvalidTransition):
        states.mark_attention(conn, "j1", "x")


def test_attention_and_resume(conn):
    states.transition(conn, "j1", states.RESEARCHING)
    states.mark_attention(conn, "j1", "bütçe")
    job = db.get_job(conn, "j1")
    assert (job["status"], job["prev_status"], job["attention_reason"]) == (states.NEEDS_ATTENTION, states.RESEARCHING, "bütçe")
    assert states.resume(conn, "j1") == states.RESEARCHING
    assert db.get_job(conn, "j1")["attention_reason"] is None


def test_revision_rewinds_only_to_production_states(conn):
    for s in states.PIPELINE[1:] + [states.NEEDS_REVISION]:
        states.transition(conn, "j1", s)
    with pytest.raises(states.InvalidTransition):
        states.transition(conn, "j1", states.QUEUED)
    states.transition(conn, "j1", states.KEYFRAMES_READY)
