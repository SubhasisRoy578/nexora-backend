from app.agents.dynamic_agent import (
    DynamicAgent
)

class AgentFactory:

    def __init__(self):

        self.dynamic_agents = {}

    def create_agent(
        self,
        name: str,
        specialty: str
    ):

        if name not in self.dynamic_agents:

            self.dynamic_agents[name] = (
                DynamicAgent(
                    name=name,
                    specialty=specialty
                )
            )

        return self.dynamic_agents[name]

    def get_agent(
        self,
        name: str
    ):

        return self.dynamic_agents.get(
            name
        )

    def list_agents(self):

        return list(
            self.dynamic_agents.keys()
        )


agent_factory = AgentFactory()