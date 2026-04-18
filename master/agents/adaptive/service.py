"""Adaptive-learning service that combines KG context, BKT, and ability updates."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from master.agents.common.agent_logging import log_agent_event
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.message import ExamQuestion

from .ability import AbilityParameters, update_theta
from .bkt import BKTEngine, BKTParams
from .cat import (
    RecommendationWeights,
    difficulty_match_score,
    novelty_score,
    prerequisite_readiness_score,
    priority_match_score,
    topic_coverage_score,
    weakness_alignment_score,
)
from .graph import AdaptiveGraph
from .profile_builder import AdaptiveAttempt, create_profile, push_recent_history
from .question_gen import QuestionRecommendation


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    """Remove duplicates from an iterable while preserving encounter order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class AdaptiveService:
    """High-level adaptive service for profile updates and question ranking."""

    def __init__(
        self,
        *,
        graph_data_dir: str | Path | None = None,
        adaptive_graph: AdaptiveGraph | None = None,
        ability_params: AbilityParameters | None = None,
        bkt_params: BKTParams | None = None,
        weights: RecommendationWeights | None = None,
    ) -> None:
        """Wire together the adaptive components used by the service.

        Args:
            graph_data_dir: Optional path to KG exports when building a new
                ``AdaptiveGraph`` internally.
            adaptive_graph: Optional injected graph facade, useful in tests.
            ability_params: Optional override for IRT-like ability updates.
            bkt_params: Optional override for per-topic BKT updates.
            weights: Optional override for ranking-score weights.
        """

        self.graph = adaptive_graph or AdaptiveGraph(graph_data_dir=graph_data_dir)
        self.ability_params = ability_params or AbilityParameters()
        self.bkt = BKTEngine(params=bkt_params)
        self.weights = weights or RecommendationWeights()
        log_agent_event(
            "adaptive.service",
            "initialized",
            extra={
                "graph": type(self.graph).__name__,
                "bkt": type(self.bkt).__name__,
            },
            mode="completed",
        )

    @staticmethod
    def default_graph_data_dir() -> Path:
        """Return the default graph-export directory."""

        return AdaptiveGraph.default_outputs_dir()

    def create_profile(
        self,
        student_id: str,
        *,
        initial_theta: float = 0.0,
        initial_mastery: dict[str, float] | None = None,
    ) -> LearnerProfile:
        """Create an empty adaptive profile for a learner."""

        profile = create_profile(
            student_id,
            initial_theta=initial_theta,
            initial_mastery=initial_mastery,
        )
        log_agent_event(
            "adaptive.service",
            "create_profile",
            extra={"student_id": student_id},
            mode="progress",
        )
        return profile

    def normalize_attempt_topics(self, attempt: AdaptiveAttempt) -> list[str]:
        """Map attempt topic tags to KG ids where possible.

        Args:
            attempt: Normalized graded interaction.

        Returns:
            Canonical KG topic ids when resolution succeeds, otherwise the raw
            topic strings are preserved.
        """

        return self.graph.canonical_or_raw_topics(attempt.covered_topics())

    def update_profile(
        self,
        profile: LearnerProfile,
        attempt: AdaptiveAttempt,
    ) -> tuple[LearnerProfile, dict]:
        """Update the learner profile from one graded attempt.

        Args:
            profile: Learner profile to update in place.
            attempt: One normalized graded interaction.

        Returns:
            A tuple of ``(profile, summary)`` where the profile contains the new
            persistent state and the summary captures per-attempt diagnostics.
        """

        normalized_topics = self.normalize_attempt_topics(attempt)
        ability_update = update_theta(
            theta=profile.theta,
            difficulty=attempt.difficulty_b,
            is_correct=attempt.is_correct,
            params=self.ability_params,
            discrimination=attempt.discrimination_a,
        )
        profile.theta = ability_update.theta
        profile.total_attempts += 1
        if attempt.is_correct:
            profile.total_correct += 1

        updated_mastery: dict[str, float] = {}
        for topic in normalized_topics:
            prior_mastery = profile.mastery_for_topic(topic)
            next_mastery = self.bkt.update_mastery(prior_mastery, attempt.is_correct)
            profile.topic_mastery[topic] = next_mastery
            profile.topic_attempts[topic] = profile.topic_attempts.get(topic, 0) + 1
            if attempt.is_correct:
                profile.topic_correct[topic] = profile.topic_correct.get(topic, 0) + 1
            else:
                profile.topic_correct.setdefault(topic, 0)
            updated_mastery[topic] = next_mastery

        push_recent_history(
            profile,
            question_id=attempt.question_id,
            topics=normalized_topics,
        )

        summary = {
            "question_id": attempt.question_id,
            "is_correct": attempt.is_correct,
            "theta": profile.theta,
            "expected_correct_probability": ability_update.expected_correct_probability,
            "updated_topics": updated_mastery,
            "weak_topics": profile.weak_topics(),
            "strong_topics": profile.strong_topics(),
        }
        log_agent_event(
            "adaptive.service",
            "update_profile",
            extra={
                "student_id": profile.student_id,
                "question_id": attempt.question_id,
                "is_correct": attempt.is_correct,
                "topics": len(normalized_topics),
            },
            mode="progress",
        )
        return profile, summary

    def update_profile_from_attempts(
        self,
        profile: LearnerProfile,
        attempts: Sequence[AdaptiveAttempt],
    ) -> tuple[LearnerProfile, list[dict]]:
        """Replay a history of attempts into a learner profile.

        Args:
            profile: Learner profile to update in place.
            attempts: Ordered graded attempts to replay.

        Returns:
            A tuple of the updated profile and one summary dict per attempt.
        """

        summaries: list[dict] = []
        for attempt in attempts:
            profile, summary = self.update_profile(profile, attempt)
            summaries.append(summary)
        log_agent_event(
            "adaptive.service",
            "update_profile_from_attempts",
            extra={"student_id": profile.student_id, "attempts": len(attempts)},
            mode="completed",
        )
        return profile, summaries

    def _coerce_question(self, question: ExamQuestion | dict) -> ExamQuestion:
        """Normalize a candidate question into the shared ``ExamQuestion`` schema."""

        if isinstance(question, ExamQuestion):
            return question
        return ExamQuestion.model_validate(question)

    def _priority_topics(self, profile: LearnerProfile) -> list[str]:
        """Derive the current prioritized topic list from weak topics and KG gaps.

        Args:
            profile: Current learner profile.

        Returns:
            Ordered topic ids that should be emphasized by the selector.
        """

        weak_topics = profile.weak_topics()
        contexts = self.graph.learning_targets(
            weak_topics,
            mastery_scores=profile.topic_mastery,
        )
        prioritized = [
            context.resolved_topic or context.topic
            for context in contexts
        ]
        return _dedupe_preserve_order([*prioritized, *weak_topics])

    def recommend_questions(
        self,
        profile: LearnerProfile,
        questions: Sequence[ExamQuestion | dict],
        *,
        limit: int = 5,
        exclude_question_ids: Iterable[str] | None = None,
    ) -> list[QuestionRecommendation]:
        """Rank a question bank and return the most suitable next questions.

        Args:
            profile: Current learner profile.
            questions: Question bank or candidate subset to score.
            limit: Maximum number of ranked recommendations to return.
            exclude_question_ids: Optional set of question ids that should not
                be selected again.

        Returns:
            Ranked recommendation objects sorted from best to worst match.
        """

        excluded = set(exclude_question_ids or [])
        priority_topics = self._priority_topics(profile)
        recommendations: list[QuestionRecommendation] = []

        for raw_question in questions:
            question = self._coerce_question(raw_question)
            if question.question_id in excluded:
                continue

            canonical_topics = self.graph.canonical_or_raw_topics(question.topic_tags)
            estimated_probability, difficulty_score = difficulty_match_score(
                theta=profile.theta,
                difficulty=question.difficulty_b,
                discrimination=question.difficulty_a,
            )
            weakness_score = weakness_alignment_score(
                topics=canonical_topics,
                profile=profile,
            )
            novelty = novelty_score(
                question_id=question.question_id,
                topics=canonical_topics,
                profile=profile,
            )
            prerequisite_score = prerequisite_readiness_score(
                topics=canonical_topics,
                profile=profile,
                adaptive_graph=self.graph,
            )
            coverage_score = topic_coverage_score(
                topics=canonical_topics,
                profile=profile,
            )
            priority_score = priority_match_score(
                topics=canonical_topics,
                priority_topics=priority_topics,
                adaptive_graph=self.graph,
            )

            final_score = (
                self.weights.priority_match * priority_score
                + self.weights.weakness_alignment * weakness_score
                + self.weights.difficulty_match * difficulty_score
                + self.weights.novelty * novelty
                + self.weights.prerequisite_readiness * prerequisite_score
                + self.weights.topic_coverage * coverage_score
            )

            target_topic = None
            if canonical_topics:
                target_topic = min(
                    canonical_topics,
                    key=lambda topic: profile.mastery_for_topic(topic),
                )

            reasons: list[str] = []
            if target_topic:
                mastery = profile.mastery_for_topic(target_topic)
                reasons.append(
                    f"Tap trung vao chu de yeu {self.graph.label_for(target_topic)} (mastery={mastery:.2f})."
                )
            if difficulty_score >= 0.75:
                reasons.append(
                    f"Do kho phu hop voi kha nang hien tai (xac suat dung uoc tinh {estimated_probability:.2f})."
                )
            if prerequisite_score >= 0.65 and target_topic:
                prerequisite_labels = self.graph.prerequisite_labels(target_topic)
                if prerequisite_labels:
                    reasons.append(
                        "Tien quyet da san sang tuong doi: "
                        + ", ".join(prerequisite_labels[:3])
                        + "."
                    )
            if novelty >= 0.80:
                reasons.append("Noi dung khong bi lap lai voi lich su gan day.")

            prerequisite_topics = self.graph.prerequisite_topics(target_topic or "")
            recommendations.append(
                QuestionRecommendation(
                    question_id=question.question_id,
                    score=final_score,
                    target_topic=target_topic,
                    target_label=self.graph.label_for(target_topic) if target_topic else None,
                    estimated_correct_probability=estimated_probability,
                    topic_tags=canonical_topics,
                    prerequisite_topics=prerequisite_topics,
                    prerequisite_labels=self.graph.knowledge_graph.labels_for(
                        prerequisite_topics
                    ),
                    reasons=reasons,
                )
            )

        recommendations.sort(key=lambda item: item.score, reverse=True)
        result = recommendations[:limit]
        log_agent_event(
            "adaptive.service",
            "recommend_questions",
            extra={
                "student_id": profile.student_id,
                "candidates": len(questions),
                "selected": len(result),
                "limit": limit,
            },
            mode="progress",
        )
        return result

    def select_questions(
        self,
        profile: LearnerProfile,
        questions: Sequence[ExamQuestion | dict],
        *,
        limit: int = 5,
        exclude_question_ids: Iterable[str] | None = None,
    ) -> list[ExamQuestion]:
        """Return the underlying question objects for the top recommendations.

        Args:
            profile: Current learner profile.
            questions: Question bank or candidate subset to score.
            limit: Maximum number of question objects to return.
            exclude_question_ids: Optional set of question ids to skip.

        Returns:
            The original question objects corresponding to the top-ranked
            recommendation ids.
        """

        ranked = self.recommend_questions(
            profile,
            questions,
            limit=limit,
            exclude_question_ids=exclude_question_ids,
        )
        selected_ids = [recommendation.question_id for recommendation in ranked]
        question_map = {
            self._coerce_question(question).question_id: self._coerce_question(question)
            for question in questions
        }
        return [
            question_map[question_id]
            for question_id in selected_ids
            if question_id in question_map
        ]
