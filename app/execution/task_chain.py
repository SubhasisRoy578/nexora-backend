class TaskChain:

    def __init__(self):

        self.tasks = []

    def add_task(
        self,
        task_name,
        task_data
    ):

        self.tasks.append({
            "task": task_name,
            "data": task_data
        })

    def get_tasks(self):

        return self.tasks