from langgraph.checkpoint.memory import MemorySaver
from master.agents import BaseAgent
from master.agents.debate import Debate

class VerifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Verifier Agent",
            description="Chuyên gia Đánh giá / Giám khảo AI giàu kinh nghiệm, có khả năng đánh giá chính xác và công bằng các câu trả lời của Teacher Agent dựa trên tiêu chí đã được xác định.",
            system_prompt="Bạn là một Chuyên gia Đánh giá / Giám khảo AI giàu kinh nghiệm. Nhiệm vụ chính của bạn là đánh giá chính xác và công bằng các câu trả lời của Teacher Agent dựa trên tiêu chí đã được xác định."
        )

        self.verifier_llm_with_tools = None
        self.verifier_llm_with_output = None
        self.tools = None
        self.browser = None
        self.playwright = None
        self.graph = None
        self.memory = MemorySaver()
        self._debate: Debate | None = None

    async def setup(self):
        # Same graph as Teacher (teacher ↔ tools ↔ verifier); see ``Debate``.
        self._debate = Debate()
        await self._debate.setup()
        self.tools = self._debate.tools
        self.browser = self._debate.browser
        self.playwright = self._debate.playwright
        self.verifier_llm_with_output = self._debate.verifier_llm_with_output
        self.verifier_llm_with_tools = None
        self.memory = self._debate.memory
        self.graph = self._debate.graph

    async def run(self, input: str) -> str:
        raise NotImplementedError(
            "After setup(), use self.graph.ainvoke(...) or master.agents.debate.Debate.run_superstep."
        )