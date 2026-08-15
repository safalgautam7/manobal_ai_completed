from app import db


def test_sessions_are_created_and_reused(settings):
    sid = db.get_or_create_session(None, "user-1")
    assert sid
    sid2 = db.get_or_create_session(sid, "user-1")
    assert sid2 == sid


def test_session_is_isolated_per_user(settings):
    sid_a = db.get_or_create_session(None, "user-a")
    sid_b = db.get_or_create_session(None, "user-b")
    assert sid_a != sid_b

    # user-b cannot claim user-a's session
    other = db.get_or_create_session(sid_a, "user-b")
    assert other != sid_a


def test_messages_roundtrip_in_order(settings):
    sid = db.get_or_create_session(None, "user-1")
    db.append_message(sid, "user", "hello")
    db.append_message(sid, "bot", "hi there")
    db.append_message(sid, "user", "how are you")

    msgs = db.get_recent_messages(sid, 10)
    assert [m["role"] for m in msgs] == ["user", "bot", "user"]
    assert msgs[0]["content"] == "hello"
    assert msgs[2]["content"] == "how are you"


def test_recent_messages_limit(settings):
    sid = db.get_or_create_session(None, "user-1")
    for i in range(10):
        db.append_message(sid, "user", str(i))
    msgs = db.get_recent_messages(sid, 4)
    assert [m["content"] for m in msgs] == ["6", "7", "8", "9"]


def test_emotion_counts_per_user(settings):
    db.save_emotion("user-a", "joy", 0.9)
    db.save_emotion("user-a", "joy", 0.8)
    db.save_emotion("user-a", "sadness", 0.7)
    db.save_emotion("user-b", "anger", 0.6)

    assert db.get_emotion_counts("user-a") == {"joy": 2, "sadness": 1}
    assert db.get_emotion_counts("user-b") == {"anger": 1}
    assert db.get_emotion_counts() == {"joy": 2, "sadness": 1, "anger": 1}