"""Knowledge-graph extraction utilities for textbook ingestion."""

from .extract_pipeline import (
    ExtractionConfig,
    MarkdownChunk,
    build_chat_model,
    build_extraction_message_payload,
    chunk_markdown_corpus,
    chunk_markdown_file,
    export_graph_json,
    extract_corpus_graph,
    extract_graph_for_chunk,
    list_markdown_files,
    merge_graph_documents,
)
from .fpt_client import FPTChatConfig, call_fpt_chat, extract_graph_for_chunk_fpt
from .knowledge_graph import Edge, KnowledgeGraph, Node

__all__ = [
    "ExtractionConfig",
    "MarkdownChunk",
    "FPTChatConfig",
    "KnowledgeGraph",
    "Node",
    "Edge",
    "build_chat_model",
    "build_extraction_message_payload",
    "call_fpt_chat",
    "chunk_markdown_corpus",
    "chunk_markdown_file",
    "export_graph_json",
    "extract_corpus_graph",
    "extract_graph_for_chunk",
    "extract_graph_for_chunk_fpt",
    "list_markdown_files",
    "merge_graph_documents",
]

try:
    from .model import ExtractionDocument, KnowledgeEdge, KnowledgeNode
except ModuleNotFoundError:
    ExtractionDocument = None
    KnowledgeEdge = None
    KnowledgeNode = None
else:
    __all__.extend(["ExtractionDocument", "KnowledgeEdge", "KnowledgeNode"])
