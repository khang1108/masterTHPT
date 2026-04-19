from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from dotenv import load_dotenv

from master.agents import BaseAgent
from master.agents.common.state import AgentState
from master.common.message import Solution
from master.agents.common.message import MessageResponse, Intent
from master.agents.common.tools import ToolsRegistry
from master.agents.teacher.teacher import EvaluateBatch
from master.agents.common.llm_client import LLMClient
from master.agents.common.prompt import (
    verifier_prompt,
    verifier_system_prompt,
    verifier_counter_evidence_prompt,
    verifier_tool_research_prompt,
)

import json
import os
import re

load_dotenv(override=True)
BATCH_SIZE = 3


class VerifierAgent(ToolsRegistry, BaseAgent):
    def __init__(self):
        super().__init__(agent_role="Verifier")
        self.system_prompt = verifier_system_prompt()
        self._llm = None
        self._llm_with_output = None
        self._memory = MemorySaver()
        self.graph = None

    async def setup(self):
        self.logger.agent_node("Verifier setup started")
        llm = LLMClient.chat_model(
            provider="openai_compatible",
            base_url=os.getenv("FPT_BASE_URL"),
            api_key=os.getenv("FPT_API_KEY"),
            model=os.getenv("VERIFIER_MODEL"),
            max_tokens=8192,
            temperature=0.7,
        )
        await self.setup_tools(llm)
        self._llm_with_output = self._llm.with_structured_output(EvaluateBatch)
        self.logger.agent_node("Verifier setup completed")

    def verifier_router(self, state: AgentState) -> str:
        request = state["request"]
        intent = request.intent
        current_phase = state.get("phase", "draft")
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)
        is_agreed = state.get("is_agreed") or []

        if current_phase == "END":
            return "END"
        if current_phase == "teacher":
            if round_now >= max_round:
                return "END"
            if not request.parser_output:
                return "END"
            if is_agreed and all(is_agreed) and intent == Intent.REVIEW_MISTAKE.value:
                return "END"
        return "teacher"

    def format_conversation(self, state: AgentState) -> str:
        teacher_feedback = state.get("teacher_feedback") or []
        verifier_feedback = state.get("verifier_feedback") or []

        if not isinstance(teacher_feedback, list):
            teacher_feedback = [teacher_feedback]
        if not isinstance(verifier_feedback, list):
            verifier_feedback = [verifier_feedback]

        conversation_lines = ["Conversation history:", ""]
        for i, t_feedback in enumerate(teacher_feedback):
            teacher_text = t_feedback.content if hasattr(t_feedback, "content") else str(t_feedback)
            
            if isinstance(teacher_text, list):
                teacher_text = json.dumps(teacher_text, ensure_ascii=False)
            
            conversation_lines.append(f"Round {i + 1}")
            conversation_lines.append(f"Teacher feedback: {teacher_text}")
            if i < len(verifier_feedback):
                verifier_text = verifier_feedback[i].content if hasattr(verifier_feedback[i], "content") else str(verifier_feedback[i])
                
                if isinstance(verifier_text, list):
                    verifier_text = json.dumps(verifier_text, ensure_ascii=False)
                conversation_lines.append(f"Verifier feedback: {verifier_text}")
            conversation_lines.append("")

        return "\n".join(conversation_lines)

    async def _run_batch(self, state: AgentState) -> AgentState:
        request = state["request"]
        intent = request.intent
        round_now = state.get("round", 0)
        max_round = state.get("max_round", 3)

        is_agreed = []
        solutions = []
        confidence = []
        feedback = []
        item_list = request.parser_output or []
        teacher_feedback = state.get("teacher_feedback") or []
        id_to_index = {item.get("question_id"): idx for idx, item in enumerate(item_list)} if item_list else {}
        remaining_items = []
        db_inserted = 0
        db_saved_total_before = state.get("db_saved_total", 0) or 0
        state_is_agreed = state.get("is_agreed", []) or []
        state_discrimination_a = state.get("discrimination_a", []) or []
        state_difficulty_b = state.get("difficulty_b", []) or []
        state_solutions = state.get("solutions", []) or []
        has_prior_verifier_feedback = bool(state.get("verifier_feedback"))
        solution_by_id = {}

        latest_teacher_feedback = teacher_feedback[-1].content if teacher_feedback and hasattr(teacher_feedback[-1], "content") else (teacher_feedback[-1] if teacher_feedback else "")
        if isinstance(latest_teacher_feedback, list):
            latest_teacher_feedback = json.dumps(latest_teacher_feedback, ensure_ascii=False)

        for solution in state_solutions:
            if hasattr(solution, "question_id") and hasattr(solution, "solution"):
                solution_by_id[solution.question_id] = solution.solution
            elif isinstance(solution, dict):
                question_id = solution.get("question_id")
                if question_id:
                    solution_by_id[question_id] = solution.get("solution")

        for i in range(0, len(item_list), BATCH_SIZE):
            batch = item_list[i:i + BATCH_SIZE]
            batch_saved = 0
            question_ids = [item.get("question_id") for item in batch]

            skip_verify = [
                question_id
                for question_id in question_ids
                if (
                    has_prior_verifier_feedback
                    and id_to_index.get(question_id) is not None
                    and id_to_index[question_id] < len(state_is_agreed)
                    and state_is_agreed[id_to_index[question_id]]
                )
            ]

            if intent == Intent.PREPROCESS.value and skip_verify:
                batch_map = {item.get("question_id"): item for item in batch}
                for ids in skip_verify:
                    item = batch_map.get(ids)
                    if not item:
                        continue

                    item_index = id_to_index.get(ids)
                    discrimination_a = (
                        state_discrimination_a[item_index]
                        if item_index is not None and item_index < len(state_discrimination_a)
                        else None
                    )
                    difficulty_b = (
                        state_difficulty_b[item_index]
                        if item_index is not None and item_index < len(state_difficulty_b)
                        else None
                    )
                    correct_answer = solution_by_id.get(ids)
                    question_type = (item.get("type") or "").strip().lower()
                    normalized_correct_answer = None

                    # Normalize correct answer
                    if question_type == "true_false":
                        expected_count = len(item.get("options") or [])
                        answer_text = str(correct_answer or "").strip().upper()
                        tokens = [token.strip() for token in answer_text.split(",") if token.strip()]
                        if tokens and all(token in {"T", "F"} for token in tokens):
                            if expected_count == 0 or len(tokens) == expected_count:
                                normalized_correct_answer = ", ".join(tokens)
                            else:
                                normalized_correct_answer = correct_answer
                        else:
                            normalized_correct_answer = correct_answer
                    elif question_type == "multiple_choice":
                        answer_text = str(correct_answer or "").strip().upper()
                        if answer_text in {"A", "B", "C", "D"}:
                            normalized_correct_answer = answer_text
                        else:
                            match = re.search(r"[A-D]", answer_text)
                            normalized_correct_answer = match.group(0) if match else correct_answer
                    elif question_type in {"short_ans", "short_answer"}:
                        answer_text = str(correct_answer or "").strip()
                        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", answer_text):
                            normalized_correct_answer = answer_text
                        else:
                            normalized_correct_answer = correct_answer
                    else:
                        normalized_correct_answer = correct_answer

                    data = {
                        "question_id": item.get("question_id"),
                        "question_index": item["question_index"],
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": normalized_correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": discrimination_a,
                        "difficulty_b": difficulty_b,
                    }

                    await self.insert_data("masterthpt", "questions", [data])
                    db_inserted += 1
                    batch_saved += 1

                self.logger.agent_node(f"Verifier batch {i // BATCH_SIZE + 1}: saved {batch_saved} skipped-verify questions to database")

            need_verify = [item for item in batch if item.get("question_id") not in skip_verify]
            remaining_items.extend(need_verify)
            if not need_verify:
                continue

            batch_input_json = json.dumps(need_verify, ensure_ascii=False, indent=2)
            conversation = self.format_conversation(state)
            prompt = verifier_prompt(batch_input_json)
            prompt += conversation

            try:
                research_evidence, _, research_source = await self.run_counter_evidence_then_tool(counter_prompt=verifier_counter_evidence_prompt(batch_input_json, conversation), tool_prompt=verifier_tool_research_prompt(batch_input_json, conversation), messages_key="Verifier_feedback")
            except Exception as error:
                research_evidence = ""
                research_source = "none"
                self.logger.warning(f"Verifier research failed for batch {i // BATCH_SIZE + 1}: {error}")

            if research_evidence:
                prompt += f"\nRESEARCH_EVIDENCE ({research_source}, prioritize in reasoning/feedback):\n{research_evidence}\nIf RESEARCH_EVIDENCE exists, mention the strongest evidence briefly in reasoning or feedback."
            responses: EvaluateBatch = await self._llm_with_output.ainvoke(self.build_messages(prompt))

            response_by_id = {r.question_id: r for r in responses.results}
            missing = [item for item in need_verify if item.get("question_id") not in response_by_id]
            retry_count = 0
            while missing and retry_count < 2:
                retry_count += 1
                self.logger.agent_node(f"Verifier retry {retry_count}: {len(missing)} missing items")
                retry_json = json.dumps(missing, ensure_ascii=False, indent=2)
                retry_prompt = verifier_prompt(retry_json)
                retry_prompt += conversation
                if research_evidence:
                    retry_prompt += f"\nRESEARCH_EVIDENCE ({research_source}, prioritize in reasoning/feedback):\n{research_evidence}\nIf RESEARCH_EVIDENCE exists, mention the strongest evidence briefly in reasoning or feedback."
                retry_responses: EvaluateBatch = await self._llm_with_output.ainvoke(self.build_messages(retry_prompt))
                for result in retry_responses.results:
                    response_by_id[result.question_id] = result
                missing = [item for item in need_verify if item.get("question_id") not in response_by_id]

            if intent == Intent.PREPROCESS.value and need_verify:
                done_items = []
                for item in need_verify:
                    item_id = item.get("question_id")
                    response = response_by_id.get(item_id)
                    is_last_round = round_now + 1 >= max_round
                    is_done = is_last_round or (response and response.agree)
                    if is_done:
                        done_items.append((item, response))

                done_ids = {item.get("question_id") for item, _ in done_items}
                remaining_items = [item for item in remaining_items if item.get("question_id") not in done_ids]

                for item, response in done_items:
                    item_id = item.get("question_id")
                    item_index = id_to_index.get(item_id)

                    raw_correct_answer = response.correct_answer if response else solution_by_id.get(item_id)
                    question_type = (item.get("type") or "").strip().lower()
                    normalized_correct_answer = None

                    if question_type == "true_false":
                        expected_count = len(item.get("options") or [])
                        answer_text = str(raw_correct_answer or "").strip().upper()
                        tokens = [token.strip() for token in answer_text.split(",") if token.strip()]
                        if tokens and all(token in {"T", "F"} for token in tokens):
                            if expected_count == 0 or len(tokens) == expected_count:
                                normalized_correct_answer = ", ".join(tokens)
                            else:
                                normalized_correct_answer = raw_correct_answer
                        else:
                            normalized_correct_answer = raw_correct_answer
                    elif question_type == "multiple_choice":
                        answer_text = str(raw_correct_answer or "").strip().upper()
                        if answer_text in {"A", "B", "C", "D"}:
                            normalized_correct_answer = answer_text
                        else:
                            match = re.search(r"[A-D]", answer_text)
                            normalized_correct_answer = match.group(0) if match else raw_correct_answer
                    elif question_type in {"short_ans", "short_answer"}:
                        answer_text = str(raw_correct_answer or "").strip()
                        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", answer_text):
                            normalized_correct_answer = answer_text
                        else:
                            normalized_correct_answer = raw_correct_answer
                    else:
                        normalized_correct_answer = raw_correct_answer

                    disc_a = response.discrimination_a if response else state_discrimination_a[item_index] if item_index is not None and item_index < len(state_discrimination_a) else None
                    diff_b = response.difficulty_b if response else state_difficulty_b[item_index] if item_index is not None and item_index < len(state_difficulty_b) else None

                    data = {
                        "question_id": item_id,
                        "question_index": item.get("question_index"),
                        "type": item.get("type"),
                        "content": item.get("content"),
                        "options": item.get("options"),
                        "correct_answer": normalized_correct_answer,
                        "has_image": item.get("has_image"),
                        "image_url": item.get("image_url"),
                        "discrimination_a": disc_a,
                        "difficulty_b": diff_b,
                    }
                    await self.insert_data("masterthpt", "questions", [data])
                    db_inserted += 1
                    batch_saved += 1

                if done_items:
                    self.logger.agent_node(f"Verifier batch {i // BATCH_SIZE + 1}: saved {len(done_items)} verified questions to database")

            for ids in skip_verify:
                state.setdefault("response", []).append(MessageResponse(student_id=request.student_id, exam_id=request.exam_id, question_id=ids, feedback=f"Câu trả lời đúng là {latest_teacher_feedback}"))

            for item in need_verify:
                item_id = item.get("question_id")
                state.setdefault("response", []).append(MessageResponse(student_id=request.student_id, exam_id=request.exam_id, question_id=item_id, feedback=f"Câu trả lời đúng là {latest_teacher_feedback}"))

            for item in need_verify:
                item_id = item.get("question_id")
                result = response_by_id.get(item_id)
                if result:
                    is_agreed.append(result.agree)
                    confidence.append(result.confidence)
                    if result.correct_answer is not None and str(result.correct_answer).strip() != "":
                        solutions.append(Solution(question_id=result.question_id, solution=str(result.correct_answer).strip()))
                    feedback.append(AIMessage(content=f"Ở câu {result.question_id}: {result.feedback} vì {result.reasoning}"))
                else:
                    is_agreed.append(False)
                    confidence.append(0.0)
                    feedback.append(AIMessage(content=f"Ở câu {item_id}: Không có phản hồi từ Verifier LLM"))

            self.logger.agent_node(
                f"Verifier batch {i // BATCH_SIZE + 1} summary: "
                f"{len(response_by_id)}/{len(need_verify)} responses, "
                f"{batch_saved} questions saved this batch, "
                f"{db_inserted} saved this round so far"
            )

        request.parser_output = remaining_items
        db_saved_total = db_saved_total_before + db_inserted
        self.logger.agent_node(
            f"Verifier round {round_now} summary: "
            f"{db_inserted} questions saved this round, "
            f"{db_saved_total} total questions saved to database so far, "
            f"{len(remaining_items)} remaining"
        )
        return {
            "request": request,
            "phase": "teacher",
            "is_agreed": is_agreed,
            "round": round_now + 1,
            "max_round": max_round,
            "confidence": confidence,
            "solutions": solutions,
            "verifier_feedback": feedback,
            "db_saved_total": db_saved_total,
        }

    async def verifier(self, state: AgentState) -> AgentState:
        self.logger.agent_node("Verifier debate started")
        next_state = await self._run_batch(state)
        self.logger.agent_node("Verifier debate completed")
        return next_state

    async def run(self, input: str) -> str:
        return "Use run_draft() or run_debate() instead."
