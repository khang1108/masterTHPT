from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tools import get_all_tools
from master.common import ExamData, AgentMessage
from master.agents import BaseAgent

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    exam_data: ExamData                         # The exam data that the Teacher Agent needs to process, including sections and questions
    success_criteria: str                       # The specific criteria that the Teacher Agent needs to meet in its response, such as accuracy, completeness, or clarity
    verifier_feedback: Optional[str]            # Feedback from the Verifier Agent on the Teacher Agent's previous response, which can be used to improve future responses
    success_criteria_met: bool                  # A boolean flag indicating whether the Teacher Agent's response met the success criteria, which can be used to determine if further iterations are needed
    needs_user_input: bool                      # A boolean flag indicating whether the Teacher Agent needs additional input or clarification from the user to proceed, which can help guide the interaction and ensure that the Teacher Agent has all the necessary information to provide an accurate response
    debate_round: int                           # The current round of the debate, which can be used to track the progress of the discussion and ensure that all participants have an opportunity to contribute

class TeacherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Teacher Agent",
            description="Chuyên gia Giáo dục / Giáo viên AI giàu kinh nghiệm và vô cùng cẩn thận, xử lý các câu hỏi, phân tích chi tiết và đưa ra câu trả lời hoặc bản đánh giá chính xác nhất.",
            system_prompt="Bạn là một Chuyên gia Giáo dục / Giáo viên AI giàu kinh nghiệm và vô cùng cẩn thận. Nhiệm vụ chính của bạn là xử lý các câu hỏi, phân tích chi tiết và đưa ra câu trả lời hoặc bản đánh giá chính xác nhất."
        )
        self.teacher_llm_with_tools = None
        self.tools = None
        self.browser = None
        self.playwright = None
        self.memory = MemorySaver()

    async def setup(self):
        self.tools, self.browser, self.playwright = await get_all_tools()
        teacher_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
        self.teacher_llm_with_tools = teacher_llm.bind_tools(self.tools)

        await self.build_graph()

    # ------------------------------ TEACHER ------------------------------
    def teacher(self, state: State) -> Dict[str, Any]:
        self.system_prompt += f"\n\nDỮ LIỆU BÀI THI (EXAM DATA) BẠN CẦN XỬ LÝ LÀ:\n{state.get('exam_data', 'Không có dữ liệu')}"
        self.system_prompt += f"\n\nTIÊU CHÍ THÀNH CÔNG (SUCCESS CRITERIA) BẠN CẦN ĐÁP ỨNG LÀ:\n{state.get('success_criteria', 'Không có tiêu chí thành công')}"
        self.system_prompt += f"\n\nNGUYÊN TẮC LÀM VIỆC CỦA BẠN: \
                \n1. Phân tích kỹ lưỡng từng câu hỏi trong dữ liệu bài thi, đảm bảo hiểu rõ yêu cầu và ngữ cảnh của mỗi câu hỏi. \
                \n2. Cung cấp câu trả lời chi tiết, chính xác và đầy đủ cho từng câu hỏi, dựa trên kiến thức chuyên môn và dữ liệu đã được cung cấp.\
                \n3. Nếu có phản hồi từ Verifier Agent, hãy sử dụng phản hồi đó để cải thiện câu trả lời của bạn trong các vòng tiếp theo, nếu cần phản biện lại thì cần dùng các tools được cung cấp để tìm bằng chứng.\
                \n4. Đảm bảo rằng câu trả lời của bạn đáp ứng đầy đủ các tiêu chí thành công đã được xác định.\
                \n5. Nếu cần thêm thông tin hoặc làm rõ từ người dùng, hãy đánh dấu rõ ràng và yêu cầu sự can thiệp của con người."
        
        if state.get('verifier_feedback'):
            self.system_prompt += f"\n\nPHẢN HỒI TỪ VERIFIER AGENT:\n{state['verifier_feedback']}"

        found_system_message = False
        messages = state["messages"]

        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = self.system_prompt
                found_system_message = True
        if not found_system_message:
            messages = [SystemMessage(content=self.system_prompt)] + messages

        response = self.teacher_llm_with_tools(messages)

        return {"messages": [response]}
        