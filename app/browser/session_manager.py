active_sessions = {}

def create_session(
    session_id
):

    active_sessions[session_id] = {
        "history": []
    }

def add_session_history(
    session_id,
    action
):

    active_sessions[
        session_id
    ]["history"].append(action)

def get_session(
    session_id
):

    return active_sessions.get(
        session_id
    )