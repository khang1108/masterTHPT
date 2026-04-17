import asyncio
import os
import json
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

load_dotenv(override=True)

from master.agents.parser.parser import ParserAgent
from master.agents.teacher.teacher import TeacherAgent
from master.agents.verifier.verifier import VerifierAgent
from master.agents.common.state import AgentState
from master.agents.common.message import MessageRequest, MessageResponse, Intent, StudentAnswer
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.tools import ToolsRegistry
from master.logging.logger import Logger

pipeline_logger = Logger("Pipeline")

_parser_agent: ParserAgent | None = None
_teacher_agent: TeacherAgent | None = None
_verifier_agent: VerifierAgent | None = None
_agent_setup_lock = asyncio.Lock()


async def _get_parser_agent() -> ParserAgent:
    global _parser_agent
    async with _agent_setup_lock:
        if _parser_agent is None:
            _parser_agent = ParserAgent()
            await _parser_agent.setup()
        return _parser_agent


async def _get_teacher_agent() -> TeacherAgent:
    global _teacher_agent
    async with _agent_setup_lock:
        if _teacher_agent is None:
            _teacher_agent = TeacherAgent()
            await _teacher_agent.setup()
        return _teacher_agent


async def _get_verifier_agent() -> VerifierAgent:
    global _verifier_agent
    async with _agent_setup_lock:
        if _verifier_agent is None:
            _verifier_agent = VerifierAgent()
            await _verifier_agent.setup()
        return _verifier_agent

def build_pipeline_graph(
    teacher: TeacherAgent,
    verifier: VerifierAgent,
    parser: ParserAgent | None = None,
):
    builder = StateGraph(dict)

    def _log_outputs(stage: str, outputs: list) -> None:
        for out in outputs:
            qid = out.student_ans.question_id
            payload = {
                "question_id": qid,
                "draft_result": out.draft_result.model_dump() if out.draft_result else None,
                "verifier_feedback": out.verifier_feedback,
                "debate_result": out.debate_result.model_dump() if out.debate_result else None,
            }
            pipeline_logger.agent_node(
                f"{stage} | {json.dumps(payload, ensure_ascii=False)}"
            )

    def _log_verdicts(stage: str, verdicts: list) -> None:
        for verdict in verdicts:
            payload = verdict.model_dump() if hasattr(verdict, "model_dump") else dict(verdict)
            pipeline_logger.agent_node(
                f"{stage} | {json.dumps(payload, ensure_ascii=False)}"
            )

    async def teacher_draft_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        next_state = await teacher.run_draft(state, thread_id=thread_id)
        _log_outputs("TEACHER_DRAFT", next_state.get("debate_outputs", []))

        request = state.get("request")
        if request and request.intent == Intent.PREPROCESS:
            outputs = next_state.get("debate_outputs", [])
        return next_state

    async def parser_ingest_node(state: dict) -> dict:
        if parser is None:
            raise RuntimeError("Parser node is enabled but parser agent is not provided.")

        thread_id = state.get("_thread_id", "pipeline-preprocess")
        file_path = state.get("_file_path")
        student_id = state.get("_student_id")
        parser_batch_size = state.get("_parser_batch_size")
        exam_id = state.get("exam_id")

        if not file_path or not student_id:
            raise ValueError("Parser graph mode requires _file_path and _student_id in state.")

        parser_request = await parser.process(
            file_path=file_path,
            student_id=student_id,
            exam_id=exam_id,
            batch_size=parser_batch_size,
            thread_id=thread_id,
        )
        if parser_request is None:
            return {
                **state,
                "response": MessageResponse(
                    student_id=student_id,
                    exam_id=exam_id,
                    feedback="Parser OCR returned empty output; request cannot be created.",
                ),
                "_stop_pipeline": True,
                "phase": "finalize",
                "_pipeline_verdict": "agree",
            }

        parser_request.intent = Intent.PREPROCESS
        preprocess_response = await teacher.run_preprocess(
            request=parser_request,
            exam_id=exam_id,
            thread_id=thread_id,
        )
        payload = preprocess_response.preprocess_payload

        if payload is None or not payload.questions:
            response = MessageResponse(
                student_id=student_id,
                exam_id=exam_id,
                question_id=parser_request.question_id,
                feedback=preprocess_response.feedback,
                preprocess_payload=payload,
            )
            return {
                **state,
                "response": response,
                "_stop_pipeline": True,
                "phase": "finalize",
                "_pipeline_verdict": "agree",
            }

        preprocess_pipeline_request = MessageRequest(
            intent=Intent.PREPROCESS,
            student_id=parser_request.student_id,
            exam_id=(payload.exam.id if payload and payload.exam else exam_id),
            student_answers=[
                StudentAnswer(question_id=(q.id or f"q_{idx}"), student_answer="")
                for idx, q in enumerate(payload.questions, start=1)
            ],
        )

        return {
            **state,
            "request": preprocess_pipeline_request,
            "questions": payload.questions,
            "student_answers": preprocess_pipeline_request.student_answers,
            "debate_outputs": [],
            "_verdicts": [],
            "exam_id": preprocess_pipeline_request.exam_id,
            "round": 0,
            "phase": "draft",
            "_stop_pipeline": False,
        }

    async def verifier_check_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        verdict, next_state = await verifier.verify(state, thread_id=thread_id)
        _log_verdicts("VERIFIER_CHECK", next_state.get("_verdicts", []))
        return {**next_state, "_pipeline_verdict": verdict}

    async def teacher_finalize_node(state: dict) -> dict:
        outputs = state.get("debate_outputs", [])
        request = state.get("request")
        is_ask_hint = bool(request and request.intent == Intent.ASK_HINT)

        lines = []
        for out in outputs:
            dr = out.draft_result
            if dr is None:
                continue
            if is_ask_hint:
                if dr.feedback:
                    lines.append(f"Câu {out.student_ans.question_id}: {dr.feedback}")
            else:
                line = (
                    f"Câu {out.student_ans.question_id}:\n"
                    f"- {'Đúng' if dr.is_correct else 'Sai'}"
                    + (f" ({dr.score} điểm)" if dr.score is not None else "")
                    + f"\n- confidence={dr.confidence:.2f}"
                )
                if dr.feedback:
                    line += f"\n- {dr.feedback}"
                lines.append(line)

        if is_ask_hint:
            feedback = (
                "\n".join(lines)
                if lines
                else "Teacher đã nhận yêu cầu gợi ý. Hãy cung cấp đáp án hiện tại để nhận gợi ý chi tiết hơn."
            )
        else:
            feedback = "\n\n".join(lines) if lines else "Teacher đã hoàn tất chấm bài."

        response = MessageResponse(
            student_id=request.student_id if request else "",
            exam_id=state.get("exam_id") or (request.exam_id if request else None),
            question_id=request.question_id if request else None,
            feedback=feedback,
        )
        pipeline_logger.agent_node(f"PIPELINE_FINALIZE | feedback={response.feedback}")
        return {**state, "response": response, "phase": "finalize", "_pipeline_verdict": "agree"}

    async def teacher_debate_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        next_state = await teacher.run_debate(state, thread_id=thread_id)
        _log_outputs("TEACHER_DEBATE", next_state.get("debate_outputs", []))
        return next_state

    async def verifier_finalize_node(state: dict) -> dict:
        thread_id = state.get("_thread_id", "pipeline")
        _, next_state = await verifier.verify(
            state,
            thread_id=thread_id,
        )
        return {**next_state, "_pipeline_verdict": "agree"}

    def route_after_verify(state: dict) -> str:
        verdict = state.get("_pipeline_verdict")
        if verdict == "agree":
            return "done"

        if state.get("round", 0) >= state.get("max_round", 3):
            return "force_finalize"

        return "teacher_debate"

    def route_after_teacher_draft(state: dict) -> str:
        request = state.get("request")
        if request and request.intent == Intent.ASK_HINT:
            return "teacher_finalize"

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

        if request and request.intent == Intent.PREPROCESS:
            # PREPROCESS: chỉ verify/debate khi teacher tự giải có confidence cao.
            if confidences and min(confidences) >= threshold:
                return "verifier_check"
            return "teacher_finalize"

        if confidences and min(confidences) >= threshold:
            return "teacher_finalize"
        return "verifier_check"

    def route_start(state: dict) -> str:
        if state.get("_start_phase") == "parser_ingest":
            return "parser_ingest"
        return "teacher_draft"

    def route_after_parser_ingest(state: dict) -> str:
        if state.get("_stop_pipeline", False):
            return "done"
        return "teacher_draft"

    builder.add_node("parser_ingest", parser_ingest_node)

    builder.add_node("teacher_draft", teacher_draft_node)
    builder.add_node("verifier_check", verifier_check_node)
    builder.add_node("teacher_finalize", teacher_finalize_node)
    builder.add_node("teacher_debate", teacher_debate_node)
    builder.add_node("force_finalize", verifier_finalize_node)

    builder.add_conditional_edges(
        START,
        route_start,
        {
            "parser_ingest": "parser_ingest",
            "teacher_draft": "teacher_draft",
        },
    )
    builder.add_conditional_edges(
        "parser_ingest",
        route_after_parser_ingest,
        {
            "teacher_draft": "teacher_draft",
            "done": END,
        },
    )
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
    request: MessageRequest | None = None,
    exam_id: str = None,
    max_rounds: int = 3,
    confidence_threshold: float = 0.9,
    thread_id: str | None = None,
    file_path: str | None = None,
    student_id: str | None = None,
    parser_batch_size: int | None = None,
) -> MessageResponse:
    if request is None:
        if not file_path or not student_id:
            raise ValueError("When request is None, both file_path and student_id are required.")

        parser = await _get_parser_agent()
        teacher = await _get_teacher_agent()
        verifier = await _get_verifier_agent()
        effective_thread_id = thread_id or f"pipeline-preprocess-{student_id}"

        pipeline_graph = build_pipeline_graph(teacher, verifier, parser=parser)
        state = AgentState(
            request=None,
            student_answers=[],
            debate_outputs=[],
            _verdicts=[],
            exam_id=exam_id,
            round=0,
            max_round=max_rounds,
            _teacher_confidence_threshold=float(confidence_threshold),
            _thread_id=effective_thread_id,
            _start_phase="parser_ingest",
            _file_path=file_path,
            _student_id=student_id,
            _parser_batch_size=parser_batch_size,
        )
        config = build_langsmith_invoke_config(
            run_name="GradingPipeline.preprocess_ingest",
            agent_role="manager",
            thread_id=effective_thread_id,
            extra_tags=["pipeline", "preprocess", "grading"],
            extra_metadata={"exam_id": exam_id, "student_id": student_id},
        )
        final_state = await pipeline_graph.ainvoke(state, config=config)
        return final_state.get(
            "response",
            MessageResponse(
                student_id=student_id,
                exam_id=exam_id,
                feedback="Grading completed",
            ),
        )

    
    teacher = await _get_teacher_agent()

    if request.intent == Intent.ASK_HINT:
        return await teacher.run_hint(request=request, exam_id=exam_id)

    if request.intent == Intent.PREPROCESS:
        effective_thread_id = thread_id or "pipeline-preprocess"
        preprocess_response = await teacher.run_preprocess(
            request=request,
            exam_id=exam_id,
            thread_id=effective_thread_id,
        )
        payload = preprocess_response.preprocess_payload

        if payload is None or not payload.questions:
            return preprocess_response

        verifier = await _get_verifier_agent()
        pipeline_graph = build_pipeline_graph(teacher, verifier)

        preprocess_pipeline_request = MessageRequest(
            intent=Intent.PREPROCESS,
            student_id=request.student_id,
            exam_id=(payload.exam.id if payload and payload.exam else exam_id),
            student_answers=[
                StudentAnswer(question_id=(q.id or f"q_{idx}"), student_answer="")
                for idx, q in enumerate(payload.questions, start=1)
            ],
        )

        state = AgentState(
            request=preprocess_pipeline_request,
            questions=payload.questions,
            student_answers=preprocess_pipeline_request.student_answers,
            debate_outputs=[],
            _verdicts=[],
            exam_id=preprocess_pipeline_request.exam_id,
            round=0,
            max_round=max_rounds,
            _teacher_confidence_threshold=float(confidence_threshold),
            _thread_id=effective_thread_id,
        )

        config = build_langsmith_invoke_config(
            run_name="GradingPipeline.preprocess_debate",
            agent_role="manager",
            thread_id=effective_thread_id,
            extra_tags=["pipeline", "preprocess", "debate"],
            extra_metadata={
                "exam_id": preprocess_pipeline_request.exam_id,
                "student_id": request.student_id,
            },
        )
        final_state = await pipeline_graph.ainvoke(state, config=config)
        final_response = final_state.get(
            "response",
            MessageResponse(
                student_id=request.student_id,
                exam_id=preprocess_pipeline_request.exam_id,
                feedback="PREPROCESS debate completed",
            ),
        )
        final_response.preprocess_payload = payload
        return final_response
    
    verifier = await _get_verifier_agent()
    effective_thread_id = thread_id or "pipeline"

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
        _thread_id=effective_thread_id,
    )

    config = build_langsmith_invoke_config(
        run_name="GradingPipeline.run",
        agent_role="manager",
        thread_id=effective_thread_id,
        extra_tags=["pipeline", "grading"],
        extra_metadata={"exam_id": exam_id, "student_id": request.student_id},
    )
    state = await pipeline_graph.ainvoke(state, config=config)
    
    return state.get("response", MessageResponse(
        student_id=request.student_id,
        exam_id=exam_id,
        feedback="Grading completed"
    ))


async def demo():
    student_id = "parser-pdf-demo"

    def find_demo_pdf() -> str:
        base_dir = os.path.dirname(__file__)
        pdf_candidates = [
            os.path.join(base_dir, name)
            for name in os.listdir(base_dir)
            if name.lower().endswith(".pdf")
        ]
        if not pdf_candidates:
            raise FileNotFoundError(
                "Không tìm thấy PDF trong thư mục master/agents để chạy demo server.py"
            )
        return sorted(pdf_candidates)[0]

    try:
        pdf_path = find_demo_pdf()

        response = await run_grading_pipeline(
            request=None,
            file_path=pdf_path,
            student_id=student_id,
            max_rounds=3,
            confidence_threshold=0.9,
        )

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await ToolsRegistry.cleanup()

if __name__ == "__main__":
    asyncio.run(demo())
