class StateManager:

    def __init__(self):

        self.active_tasks = {}

    def save_state(
        self,
        task_id,
        state
    ):

        self.active_tasks[task_id] = state

    def get_state(
        self,
        task_id
    ):

        return self.active_tasks.get(task_id)