import asyncio
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

load_dotenv(override=True)

from master.agents.teacher.teacher import TeacherAgent
from master.agents.verifier.verifier import VerifierAgent
from master.agents.common.state import AgentState
from master.agents.common.message import MessageRequest, MessageResponse, Intent, StudentAnswer
from master.agents.common.tools import ToolsRegistry


def build_pipeline_graph(
    teacher: TeacherAgent,
    verifier: VerifierAgent,
):
    builder = StateGraph(dict)

    async def teacher_draft_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        next_state = await teacher.run_draft(state, thread_id=thread_id)
        return next_state

    async def verifier_check_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        verdict, next_state = await verifier.verify(state, thread_id=thread_id)
        return {**next_state, "_pipeline_verdict": verdict}

    async def teacher_finalize_node(state: dict) -> dict:
        outputs = state.get("debate_outputs", [])
        request = state.get("request")

        lines = []
        for out in outputs:
            dr = out.draft_result
            if dr is None:
                continue
            lines.append(
                f"Câu {out.student_ans.question_id}:\n"
                f"-{'Đúng' if dr.is_correct else 'Sai'}" + (f" ({dr.score} điểm)\n" if dr.score is not None else "\n") + 
                f"-confidence={dr.confidence:.2f}\n" +
                f"-{dr.feedback}\n\n" if dr.feedback else "\n\n"
            )

        feedback = "\n".join(lines) if lines else "Teacher đã hoàn tất chấm bài."
        response = MessageResponse(
            student_id=request.student_id if request else "",
            exam_id=state.get("exam_id") or (request.exam_id if request else None),
            question_id=request.question_id if request else None,
            feedback=feedback,
        )
        print("Teacher confidence passed threshold; skip verifier/debate")
        return {**state, "response": response, "phase": "finalize", "_pipeline_verdict": "agree"}

    async def teacher_debate_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        print(f"Round {state.get('round', 0) + 1}: Verifier disagreed, Teacher debating...")
        return await teacher.run_debate(state, thread_id=thread_id)

    async def verifier_finalize_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        _, next_state = await verifier.verify(
            state,
            thread_id=f"{thread_id}-final",
        )
        return {**next_state, "_pipeline_verdict": "agree"}

    def route_after_verify(state: dict) -> str:
        verdict = state.get("_pipeline_verdict")
        if verdict == "agree":
            print(f"Round {state.get('round', 0)}: Verifier agreed")
            return "done"

        if state.get("round", 0) >= state.get("max_round", 3):
            return "force_finalize"

        return "teacher_debate"

    def route_after_teacher_draft(state: dict) -> str:
        outputs = state.get("debate_outputs", [])
        threshold = float(state.get("_teacher_confidence_threshold", 0.9))
        if not outputs:
            return "verifier_check"

        confidences = []
        for out in outputs:
            dr = getattr(out, "draft_result", None)
            if dr is None:
                return "verifier_check"
            confidences.append(float(getattr(dr, "confidence", 0.0)))

        if confidences and min(confidences) >= threshold:
            return "teacher_finalize"
        return "verifier_check"

    builder.add_node("teacher_draft", teacher_draft_node)
    builder.add_node("verifier_check", verifier_check_node)
    builder.add_node("teacher_finalize", teacher_finalize_node)
    builder.add_node("teacher_debate", teacher_debate_node)
    builder.add_node("force_finalize", verifier_finalize_node)

    builder.add_edge(START, "teacher_draft")
    builder.add_conditional_edges(
        "teacher_draft",
        route_after_teacher_draft,
        {
            "teacher_finalize": "teacher_finalize",
            "verifier_check": "verifier_check",
        },
    )
    builder.add_edge("teacher_finalize", END)
    builder.add_conditional_edges(
        "verifier_check",
        route_after_verify,
        {
            "done": END,
            "teacher_debate": "teacher_debate",
            "force_finalize": "force_finalize",
        },
    )
    builder.add_edge("teacher_debate", "verifier_check")
    builder.add_edge("force_finalize", END)

    return builder.compile()


async def run_grading_pipeline(
    request: MessageRequest,
    exam_id: str = None,
    max_rounds: int = 3,
    confidence_threshold: float = 0.9,
) -> MessageResponse:
    
    teacher = TeacherAgent()
    await teacher.setup()
    
    verifier = VerifierAgent()
    await verifier.setup()

    pipeline_graph = build_pipeline_graph(teacher, verifier)
    
    state = AgentState(
        request=request,
        student_answers=request.student_answers,
        debate_outputs=[],
        _verdicts=[],
        exam_id=exam_id,
        round=0,
        max_round=max_rounds,
        _teacher_confidence_threshold=confidence_threshold,
        _thread_id="pipeline",
    )

    config = {"configurable": {"thread_id": "pipeline"}}
    state = await pipeline_graph.ainvoke(state, config=config)
    
    return state.get("response", MessageResponse(
        student_id=request.student_id,
        exam_id=exam_id,
        feedback="Grading completed"
    ))


async def demo():
    request = MessageRequest(
        intent=Intent.REVIEW_MISTAKE,
        student_id="69dca9498a492d985a43f808",
        question_id="07931d51-d61b-5a58-bb3b-351a8edccbcd",
        student_answers=[
            StudentAnswer(
                question_id="07931d51-d61b-5a58-bb3b-351a8edccbcd",
                student_answer="B"
            )
        ]
    )
    
    print("GRADING PIPELINE DEMO")
    print("=" * 80)
    print(f"Student: {request.student_id}")
    print(f"Question: {request.question_id}")
    print(f"Answer: {request.student_answers[0].student_answer}")
    print()
    
    try:
        response = await run_grading_pipeline(request, max_rounds=3)
        
        print("RESULT")
        print("=" * 80)
        print(f"Student ID: {response.student_id}")
        print(f"Exam ID: {response.exam_id}")
        print(f"Feedback:\n{response.feedback}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await ToolsRegistry.cleanup()
if __name__ == "__main__":
    asyncio.run(demo())
