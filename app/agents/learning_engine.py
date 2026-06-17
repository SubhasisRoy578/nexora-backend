from collections import defaultdict


class LearningEngine:

    def __init__(self):

        self.agent_scores = defaultdict(list)

        self.agent_success = defaultdict(int)

        self.agent_failures = defaultdict(int)

    # =====================================
    # EVALUATE OUTPUT
    # =====================================

    def evaluate_agent_output(
        self,
        agent_name,
        result
    ):

        score = 0

        if result:

            score += 50

        if isinstance(
            result,
            dict
        ):

            score += 30

        if len(
            str(result)
        ) > 50:

            score += 20

        self.agent_scores[
            agent_name
        ].append(score)

        self.agent_success[
            agent_name
        ] += 1

        return score

    # =====================================
    # RECORD FAILURE
    # =====================================

    def record_failure(
        self,
        agent_name
    ):

        self.agent_failures[
            agent_name
        ] += 1

    # =====================================
    # AGENT STATS
    # =====================================

    def get_agent_stats(self):

        stats = {}

        all_agents = set(
            list(
                self.agent_scores.keys()
            )
            +
            list(
                self.agent_failures.keys()
            )
        )

        for agent in all_agents:

            scores = self.agent_scores.get(
                agent,
                []
            )

            success_count = (
                self.agent_success.get(
                    agent,
                    0
                )
            )

            failure_count = (
                self.agent_failures.get(
                    agent,
                    0
                )
            )

            total_runs = (
                success_count
                +
                failure_count
            )

            average_score = 0

            best_score = 0

            if scores:

                average_score = (
                    sum(scores)
                    /
                    len(scores)
                )

                best_score = max(
                    scores
                )

            success_rate = 0

            if total_runs > 0:

                success_rate = round(
                    (
                        success_count
                        /
                        total_runs
                    ) * 100,
                    2
                )

            health = (
                "excellent"
                if success_rate >= 90
                else
                "good"
                if success_rate >= 70
                else
                "needs_improvement"
            )

            stats[agent] = {

                "executions":
                total_runs,

                "success":
                success_count,

                "failures":
                failure_count,

                "average_score":
                average_score,

                "best_score":
                best_score,

                "success_rate":
                success_rate,

                "health":
                health
            }

        return stats

    # =====================================
    # LEADERBOARD
    # =====================================

    def leaderboard(self):

        stats = self.get_agent_stats()

        leaderboard = sorted(

            stats.items(),

            key=lambda x:
            x[1]["average_score"],

            reverse=True
        )

        return leaderboard

    # =====================================
    # BEST AGENT
    # =====================================

    def best_agent(self):

        leaderboard = self.leaderboard()

        if not leaderboard:

            return None

        return {

            "agent":
            leaderboard[0][0],

            "stats":
            leaderboard[0][1]
        }

    # =====================================
    # SYSTEM STATS
    # =====================================

    def system_stats(self):

        total_success = sum(
            self.agent_success.values()
        )

        total_failures = sum(
            self.agent_failures.values()
        )

        total_executions = (
            total_success
            +
            total_failures
        )

        return {

            "total_executions":
            total_executions,

            "total_success":
            total_success,

            "total_failures":
            total_failures,

            "registered_agents":
            len(
                self.get_agent_stats()
            )
        }

    # =====================================
    # RESET LEARNING
    # =====================================

    def reset(self):

        self.agent_scores.clear()

        self.agent_success.clear()

        self.agent_failures.clear()


learning_engine = LearningEngine()