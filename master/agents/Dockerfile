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
        "beautifulsoup4>=4.12.0" \
        "PyMuPDF>=1.24.0" && \
    python -m playwright install chromium

COPY . /app/master/agents

RUN find /app/master/agents -type d -name "__pycache__" -prune -exec rm -rf '{}' +

RUN python - <<'PY'
from pathlib import Path

files = {
    "/app/master/__init__.py": "",
    "/app/master/common/__init__.py": "",
    "/app/master/common/tools.py": """import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(override=True)


def _clean_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip("\\"'")
    return cleaned or None


class MongoDBTools:
    _mongo_client = None

    @classmethod
    def _mongo_uri(cls) -> str | None:
        return _clean_env_value(os.getenv("MONGO_URI"))

    @classmethod
    def get_mongo_client(cls):
        if cls._mongo_client is None:
            mongo_uri = cls._mongo_uri()
            if not mongo_uri:
                raise RuntimeError("MONGO_URI is not configured.")
            cls._mongo_client = AsyncIOMotorClient(mongo_uri)
        return cls._mongo_client

    def _on_mongo_event(self, message: str) -> None:
        return None

    def _collection(self, database_name: str, collection_name: str):
        client = self.get_mongo_client()
        return client[database_name][collection_name]

    async def get_data(self, database_name: str, collection_name: str, query: dict, limit: int = 10):
        self._on_mongo_event(
            f"mongo:get_data:start db={database_name} collection={collection_name} limit={limit} query_keys={len(query)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.find(query).to_list(length=limit)
        self._on_mongo_event(
            f"mongo:get_data:done db={database_name} collection={collection_name} result={len(result)}"
        )
        return result

    async def get_one(self, database_name: str, collection_name: str, query: dict):
        self._on_mongo_event(
            f"mongo:get_one:start db={database_name} collection={collection_name} query_keys={len(query)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.find_one(query)
        self._on_mongo_event(
            f"mongo:get_one:done db={database_name} collection={collection_name} found={result is not None}"
        )
        return result

    async def insert_data(self, database_name: str, collection_name: str, documents: list[dict]):
        if not documents:
            self._on_mongo_event(
                f"mongo:insert_data:skip_empty db={database_name} collection={collection_name}"
            )
            return
        self._on_mongo_event(
            f"mongo:insert_data:start db={database_name} collection={collection_name} documents={len(documents)}"
        )
        collection = self._collection(database_name, collection_name)
        await collection.insert_many(documents)
        self._on_mongo_event(
            f"mongo:insert_data:done db={database_name} collection={collection_name} documents={len(documents)}"
        )

    async def insert_one(self, database_name: str, collection_name: str, document: dict):
        self._on_mongo_event(
            f"mongo:insert_one:start db={database_name} collection={collection_name} keys={len(document)}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.insert_one(document)
        self._on_mongo_event(
            f"mongo:insert_one:done db={database_name} collection={collection_name}"
        )
        return result.inserted_id

    async def update_one(self, database_name: str, collection_name: str, query: dict, update: dict, upsert: bool = False):
        self._on_mongo_event(
            f"mongo:update_one:start db={database_name} collection={collection_name} query_keys={len(query)} update_keys={len(update)} upsert={upsert}"
        )
        collection = self._collection(database_name, collection_name)
        result = await collection.update_one(query, update, upsert=upsert)
        self._on_mongo_event(
            f"mongo:update_one:done db={database_name} collection={collection_name} matched={result.matched_count} modified={result.modified_count} upserted={result.upserted_id is not None}"
        )
        return result.modified_count

    async def upsert_one(self, database_name: str, collection_name: str, query: dict, payload: dict):
        return await self.update_one(
            database_name,
            collection_name,
            query,
            {"$set": payload},
            upsert=True,
        )
""",
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


logger = Logger("master")
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
    "/app/docker_entrypoint.py": """import json

from fastapi import FastAPI, HTTPException

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
async def invoke(payload: dict | str):
    try:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Request body phải là JSON object hợp lệ, không phải chuỗi JSON bị stringify hai lần.",
                ) from exc

        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=400,
                detail="Request body phải là JSON object.",
            )

        request = MessageRequest.model_validate(payload)
        response = await run_manager_orchestrator(
            request,
            exam_id=request.exam_id,
        )
        return response.model_dump(mode="json", exclude_none=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
