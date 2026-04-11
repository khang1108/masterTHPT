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
from master.common.message import ExamQuestion
import uuid
import asyncio

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    exam_data: List[ExamQuestion]
    success_criteria: str
    verifier_feedback: Optional[str]
    success_criteria_met: bool
    needs_user_input: bool
    debate_round: int

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Phản hồi chi tiết về lỗi sai của Teacher")
    success_criteria_met: bool = Field(description="Tiêu chí thành công đã được đáp ứng")
    needs_user_input: bool = Field(description="Đánh dấu True nếu cần sự can thiệp, làm rõ thêm từ con người")

class Debate:
    def __init__(self):
        self.teacher_llm_with_tools = None
        self.verifier_llm_with_output = None
        self.tools = None
        self.graph = None
        self.debate_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await get_all_tools()
        teacher_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
        self.teacher_llm_with_tools = teacher_llm.bind_tools(self.tools)
        verifier_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
        self.verifier_llm_with_output = verifier_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()


    # ------------------------------ TEACHER ------------------------------
    def teacher(self, state: State) -> Dict[str, Any]:
        system_message = f"""Bạn là một Chuyên gia Giáo dục / Giáo viên AI (Teacher Agent) giàu kinh nghiệm và vô cùng cẩn thận. 
        Nhiệm vụ chính của bạn là xử lý các câu hỏi, phân tích chi tiết và đưa ra câu trả lời hoặc bản đánh giá chính xác nhất.

        DỮ LIỆU BÀI THI (EXAM DATA) BẠN CẦN XỬ LÝ LÀ:
        {state.get('exam_data', 'Không có dữ liệu')}

        NGUYÊN TẮC LÀM VIỆC CỦA BẠN:
        1. Tuân thủ tuyệt đối "Tiêu chí thành công" (Success Criteria) mà hệ thống yêu cầu: "{state.get('success_criteria', 'Không có tiêu chí cụ thể')}"
        2. Bám sát vào dữ liệu bài thi được cung cấp ở trên.
        3. Bạn có quyền truy cập vào các công cụ (tools). Đừng ngần ngại sử dụng công cụ để tra cứu thông tin nếu cần thiết.
        4. Cấu trúc câu trả lời phải rõ ràng, chuyên nghiệp và đi thẳng vào trọng tâm.
        """

        if state.get("verifier_feedback"):
            system_message += f"""
            CẢNH BÁO TỪ VERIFIER (VÒNG PHẢN BIỆN TRƯỚC):
            Bạn đã nhận được phản hồi sau từ Người kiểm duyệt: 
            "{state['verifier_feedback']}"
            
            YÊU CẦU: Hãy phân tích kỹ lỗi sai, tiếp thu ý kiến và SỬA ĐỔI HOÀN TOÀN câu trả lời của bạn. Tuyệt đối không lặp lại thiếu sót cũ.
            """

        found_system_message = False
        messages = state["messages"]
        
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.teacher_llm_with_tools.invoke(messages)

        return {
            "messages": [response],
        }

    def teacher_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "verifier"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Teacher: {text}\n"
        return conversation


    # ------------------------------ VERIFIER ------------------------------
    def verifier(self, state: State) -> State:
        last_response = state["messages"][-1].content

        system_message = """Bạn là một Người đánh giá (Verifier/Evaluator) có nhiệm vụ xác định xem một tác vụ đã được Teacher (Giáo viên AI) xử lý thành công hay chưa.
        Hãy đánh giá câu trả lời gần nhất của Teacher dựa trên các tiêu chí được giao. Đưa ra nhận xét (feedback) của bạn, kèm theo quyết định xem "Tiêu chí thành công" (success criteria) đã đạt được hay chưa, và liệu có cần thêm thông tin từ người dùng không."""

        user_message = f"""Bạn đang đánh giá cuộc hội thoại giữa Người dùng (User) và Giáo viên (Teacher). Bạn sẽ quyết định hành động tiếp theo dựa trên câu trả lời gần nhất của Teacher.

        Toàn bộ cuộc hội thoại với Teacher (bao gồm yêu cầu ban đầu của người dùng và tất cả các phản hồi) là:
        {self.format_conversation(state["messages"])}

        Tiêu chí thành công (Success Criteria) cho nhiệm vụ này là:
        {state["success_criteria"]}

        Và câu trả lời cuối cùng từ Teacher mà bạn đang đánh giá là:
        {last_response}

        YÊU CẦU DÀNH CHO BẠN:
        1. Đưa ra nhận xét (feedback) chi tiết.
        2. Quyết định xem câu trả lời này đã đáp ứng tiêu chí thành công chưa.
        3. Quyết định xem có cần người dùng can thiệp thêm không (ví dụ: Teacher đang đặt câu hỏi ngược lại, cần làm rõ yêu cầu, hoặc có vẻ đang bị mắc kẹt và không thể tự trả lời).

        LƯU Ý QUAN TRỌNG: 
        - Teacher có quyền truy cập vào công cụ để ghi file. Nếu Teacher nói rằng họ đã tạo/ghi một file, bạn có thể mặc định tin tưởng là họ đã làm điều đó.
        - Nhìn chung, hãy linh động và tin tưởng nếu Teacher nói đã thực hiện xong một hành động. Tuy nhiên, BẠN PHẢI TỪ CHỐI (đánh giá chưa đạt) nếu cảm thấy câu trả lời còn hời hợt và Teacher cần phải đào sâu, làm chi tiết hơn nữa.
        """

        if state["verifier_feedback"]:
            user_message += f"""
        CẢNH BÁO LẶP LỖI:
        Lưu ý rằng trong lần thử trước của Teacher, bạn đã đưa ra nhận xét này: "{state['verifier_feedback']}"
        Nếu bạn thấy Teacher vẫn đang lặp lại những lỗi y hệt, hãy cân nhắc đánh giá là chưa đạt hoặc yêu cầu người dùng can thiệp.
        """

        verifier_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        verifier_result = self.verifier_llm_with_output.invoke(verifier_messages)
        new_state = {
            "messages": [
                HumanMessage(content=f"Phản hồi từ Verifier: {verifier_result.feedback}")
            ],
            "verifier_feedback": verifier_result.feedback,
            "success_criteria_met": verifier_result.success_criteria_met,
            "needs_user_input": verifier_result.needs_user_input,
            "debate_round": state.get("debate_round", 1) + 1,
        }
        return new_state

    def verifier_route(self, state: State) -> str:
        if state["success_criteria_met"] or state.get("debate_round", 1) > 3 or state.get("needs_user_input"):
            return "END"
        else:
            return "teacher"

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("teacher", self.teacher)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("verifier", self.verifier)

        # Add edges
        graph_builder.add_conditional_edges(
            "teacher", self.teacher_router, {"tools": "tools", "verifier": "verifier"}
        )
        graph_builder.add_edge("tools", "teacher")
        graph_builder.add_conditional_edges(
            "verifier", self.verifier_route, {"teacher": "teacher", "END": END}
        )
        graph_builder.add_edge(START, "teacher")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, questions: str, success_criteria, history):
        config = {"configurable": {"thread_id": self.debate_id}}

        human_message = HumanMessage(content=f"Đây là các câu hỏi cần xử lý:\n{questions}")

        state = {
            "messages": [human_message],
            "exam_data": questions,
            "success_criteria": success_criteria or "Câu trả lời phải rõ ràng và chính xác",
            "verifier_feedback": None,
            "success_criteria_met": False,
            "needs_user_input": False,
            "debate_round": 1,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": questions}
        reply = {"role": "teacher", "content": result["messages"][-2].content}
        feedback = {"role": "verifier", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
