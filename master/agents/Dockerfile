# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    fonts-liberation \
    git \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxshmfence1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel && \
    pip install \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.30.0" \
        "pydantic>=2.0.0" \
        "pydantic-settings>=2.0.0" \
        "httpx>=0.27.0" \
        "google-generativeai>=0.8.0" \
        "python-dotenv>=1.0.0" \
        "python-multipart>=0.0.9" \
        "langchain-core>=0.3.0" \
        "langchain-google-genai>=2.0.0" \
        "langchain-openai>=0.2.0" \
        "litellm>=1.63.0" \
        "langgraph>=0.2.0" \
        "langchain-community>=0.3.0" \
        "langchain-experimental>=0.3.0" \
        "langsmith>=0.1.95" \
        "motor>=3.6.0" \
        "playwright>=1.40.0" \
        "typing_extensions>=4.0.0" \
        "Pillow>=10.0.0" \
        "PyMuPDF>=1.24.0" && \
    python -m playwright install chromium

COPY . /app/master/agents

RUN find /app/master/agents -type d -name "__pycache__" -prune -exec rm -rf '{}' +

RUN python - <<'PY'
from pathlib import Path

files = {
    "/app/master/__init__.py": "",
    "/app/master/common/__init__.py": "",
    "/app/master/common/message.py": """from pydantic import BaseModel


class GradeResult(BaseModel):
    exam_id: str
    student_id: str
    session_id: str
    total_questions: int
    total_correct: int
    total_score: float


class Solution(BaseModel):
    question_id: str
    solution: str
""",
    "/app/master/logging/__init__.py": "",
    "/app/master/logging/logger.py": """import logging
import sys


class Logger:
    def __init__(self, name: str, level: str = "INFO", **_: object):
        self.name = name
        self.logger = logging.getLogger(f"master.{name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("[%(levelname)s] [%(name)s] %(message)s"))
            self.logger.addHandler(handler)
        self.logger.setLevel(level)
        self.logger.propagate = False

    def _emit(self, level: int, message: str) -> None:
        self.logger.log(level, message)

    def debug(self, message: str) -> None:
        self._emit(logging.DEBUG, message)

    def info(self, message: str) -> None:
        self._emit(logging.INFO, message)

    def warning(self, message: str) -> None:
        self._emit(logging.WARNING, message)

    def error(self, message: str) -> None:
        self._emit(logging.ERROR, message)

    def critical(self, message: str) -> None:
        self._emit(logging.CRITICAL, message)

    def progress(self, message: str) -> None:
        self.info(message)

    def completed(self, message: str) -> None:
        self.info(message)

    def success(self, message: str) -> None:
        self.info(message)

    def agent_node(self, message: str) -> None:
        self.info(message)

    def tools_node(self, message: str) -> None:
        self.info(message)
""",
    "/app/master/data/__init__.py": "",
    "/app/master/data/knowledge/__init__.py": """from .knowledge_graph import KnowledgeGraph

__all__ = ["KnowledgeGraph"]
""",
    "/app/master/data/knowledge/knowledge_graph.py": """import json
import re
import unicodedata
from pathlib import Path


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]+", "_", without_accents.upper()).strip("_")


class KnowledgeGraph:
    def __init__(self, data_dir=None):
        self.nodes = {}
        self.alias_to_id = {}
        if data_dir is not None:
            self.load_from_directory(data_dir)

    def load_from_directory(self, data_dir):
        directory = Path(data_dir)
        if not directory.exists():
            return False
        preferred = directory / "merged_graph_all.json"
        files = [preferred] if preferred.exists() else sorted(directory.glob("merged_graph*.json"))
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for raw_node in payload.get("nodes", []):
                node_id = str(raw_node.get("id", "")).strip()
                if not node_id:
                    continue
                self.nodes[node_id] = raw_node
                for candidate in (node_id, raw_node.get("label", "")):
                    alias = _normalize(str(candidate))
                    if alias:
                        self.alias_to_id.setdefault(alias, node_id)
        return True

    def resolve_concept_id(self, concept):
        if not concept:
            return None
        if concept in self.nodes:
            return concept
        return self.alias_to_id.get(_normalize(str(concept)))

    def get_kc_metadata(self, kc_id):
        resolved = self.resolve_concept_id(kc_id)
        if not resolved:
            return None
        return self.nodes.get(resolved)

    def get_prerequisites(self, kc_id, depth=-1):
        return []

    def labels_for(self, values):
        labels = []
        for value in values:
            metadata = self.get_kc_metadata(value) or {}
            labels.append(metadata.get("label", value))
        return labels

    def get_related_kcs(self, kc_id):
        return []

    def find_knowledge_gaps(self, concepts, mastery_scores=None, threshold=0.6):
        mastery_scores = mastery_scores or {}
        return [
            concept
            for concept in concepts
            if mastery_scores.get(concept, 0.0) < threshold
        ]
""",
    "/app/docker_entrypoint.py": """from fastapi import FastAPI, HTTPException

from master.agents.common.message import MessageRequest
from master.agents.manager.orchestrator import run_manager_orchestrator


app = FastAPI(title="MASTER Agent Service")


@app.get("/")
async def root():
    return {"service": "master-agents", "status": "200"}


@app.get("/health")
async def health():
    return {"service": "master-agents", "status": "200"}


@app.post("/")
@app.post("/invoke")
async def invoke(payload: dict):
    try:
        request = MessageRequest.model_validate(payload)
        response = await run_manager_orchestrator(
            request,
            exam_id=request.exam_id,
        )
        return response.model_dump(mode="json", exclude_none=True)
    except Exception as exc:
        raise HTTPException(status_code=200, detail=str(exc)) from exc


@app.on_event("shutdown")
async def shutdown():
    from master.agents.common.tools import ToolsRegistry

    await ToolsRegistry.cleanup()
""",
}

for raw_path, content in files.items():
    path = Path(raw_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
PY

RUN mkdir -p /app/logs

EXPOSE 8001

CMD ["uvicorn", "docker_entrypoint:app", "--host", "0.0.0.0", "--port", "8001"]
