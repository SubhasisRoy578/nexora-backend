from collections import defaultdict


class AgentMetrics:

    def __init__(self):

        self.agent_scores = defaultdict(list)

    def record_score(
        self,
        agent_name: str,
        score: float
    ):

        self.agent_scores[
            agent_name
        ].append(score)

    def get_average_score(
        self,
        agent_name: str
    ):

        scores = self.agent_scores.get(
            agent_name,
            []
        )

        if not scores:
            return 0

        return sum(scores) / len(scores)

    def get_best_agent(self):

        if not self.agent_scores:
            return None

        best_agent = max(
            self.agent_scores.keys(),
            key=lambda x:
            self.get_average_score(x)
        )

        return {
            "agent": best_agent,
            "score":
            self.get_average_score(
                best_agent
            )
        }

    def get_all_scores(self):

        result = {}

        for agent in self.agent_scores:

            result[agent] = {
                "average":
                self.get_average_score(
                    agent
                ),
                "executions":
                len(
                    self.agent_scores[
                        agent
                    ]
                )
            }

        return result


agent_metrics = AgentMetrics()