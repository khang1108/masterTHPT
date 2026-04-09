"""Gemini 2.5 Flash web-grounding demo.

How to run:
1) Export API key:
   export GEMINI_API_KEY="your_api_key"
2) Install SDK:
   pip install google-genai
3) Execute:
   python docs/test.py
"""

from __future__ import annotations

import os
import time
from typing import Iterable

from google import genai
from google.genai import types


def _collect_sources(grounding_chunks: Iterable[object] | None) -> list[str]:
	"""Extract web URIs from grounding chunks safely across SDK versions."""
	if not grounding_chunks:
		return []

	sources: list[str] = []
	for chunk in grounding_chunks:
		web = getattr(chunk, "web", None)
		if web and getattr(web, "uri", None):
			sources.append(web.uri)
	return sources


def main() -> None:
	api_key = "AIzaSyDi0UCHXZKxDs6LeGrp0GLFruanr4sPq6M"
	if not api_key:
		raise ValueError(
			"Missing GEMINI_API_KEY. Set it before running, e.g.\n"
			"export GEMINI_API_KEY='your_api_key'"
		)

	client = genai.Client(api_key=api_key)

	query = (
		"Hãy ghé các trang báo và cập nhật tình hình chính trị mới nhất cho tôi ở Việt Nam"
	)

	response = client.models.generate_content(
		model="gemini-2.5-flash",
		contents=query,
		config=types.GenerateContentConfig(
			tools=[
				types.Tool(google_search=types.GoogleSearch()),
				types.Tool(url_context=types.UrlContext()),
			],
			temperature=0.2,
		),
	)

	print("=== Gemini Response ===")
	print(response.text or "(No text response)")

	grounding_chunks = None
	try:
		grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks
	except (AttributeError, IndexError, TypeError):
		grounding_chunks = None

	sources = _collect_sources(grounding_chunks)
	print("\n=== Grounding Sources ===")
	if sources:
		for i, src in enumerate(dict.fromkeys(sources), start=1):
			print(f"{i}. {src}")
	else:
		print("No grounding sources found in metadata.")


if __name__ == "__main__":
    start_time = time.perf_counter()
    main()
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    print(f"Time spend: {execution_time}")