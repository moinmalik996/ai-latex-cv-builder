from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from .config import ProjectConfig


@dataclass
class RewriteResult:
	files: dict[str, str]
	required_keywords: list[str]


STOPWORDS = {
	"a",
	"an",
	"and",
	"are",
	"as",
	"at",
	"be",
	"by",
	"for",
	"from",
	"has",
	"have",
	"in",
	"into",
	"is",
	"it",
	"its",
	"of",
	"on",
	"or",
	"our",
	"that",
	"the",
	"their",
	"this",
	"to",
	"we",
	"will",
	"with",
	"you",
	"your",
	"about",
	"across",
	"ability",
	"building",
	"candidate",
	"day",
	"experience",
	"familiarity",
	"focus",
	"good",
	"looking",
	"makes",
	"role",
	"skills",
	"software",
	"stand",
	"strong",
	"team",
	"what",
	"work",
	"working",
}


def _tokenize(text: str) -> list[str]:
	return re.findall(r"[a-z][a-z0-9+./-]{1,}", text.lower())


def _extract_required_keywords(job_description: str, limit: int = 20) -> list[str]:
	scores: Counter[str] = Counter()

	lines = [line.strip() for line in job_description.splitlines() if line.strip()]
	for line in lines:
		# Slightly boost descriptive bullet-like lines where requirements are usually listed.
		weight = 2 if len(line.split()) >= 6 else 1
		tokens = [t for t in _tokenize(line) if t not in STOPWORDS and len(t) >= 3]

		for token in tokens:
			scores[token] += weight

		# Capture dynamic phrase-level requirements like "error handling" or "provider selection".
		for i in range(len(tokens) - 1):
			bigram = f"{tokens[i]} {tokens[i + 1]}"
			scores[bigram] += weight + 0.5

	# Boost explicit technical terms that appear as acronyms or mixed-case tokens in JD text.
	for raw in re.findall(r"\b[A-Z][A-Za-z0-9+./-]{1,}\b", job_description):
		scores[raw.lower()] += 3

	# Prefer phrases first, then single words, both ranked by score.
	phrases = sorted(
		[k for k in scores if " " in k],
		key=lambda k: (-scores[k], k),
	)
	words = sorted(
		[k for k in scores if " " not in k],
		key=lambda k: (-scores[k], k),
	)

	ordered = phrases + words
	selected: list[str] = []
	for kw in ordered:
		if kw not in selected:
			selected.append(kw)
		if len(selected) >= limit:
			break

	return selected


def _keyword_in_text(keyword: str, text: str) -> bool:
	escaped = re.escape(keyword.lower().strip())
	if not escaped:
		return False
	pattern = re.compile(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])")
	return bool(pattern.search(text.lower()))


def _split_keywords_by_source_presence(
	required_keywords: list[str],
	current_sections: dict[str, str],
) -> tuple[list[str], list[str]]:
	combined = "\n".join(current_sections.values()).lower()
	present = [kw for kw in required_keywords if _keyword_in_text(kw, combined)]
	missing = [kw for kw in required_keywords if kw not in present]
	return present, missing


def _build_input(
	job_description: str,
	current_sections: dict[str, str],
	rewrite_feedback: str | None = None,
) -> str:
	required_keywords = _extract_required_keywords(job_description)
	present_keywords, missing_keywords = _split_keywords_by_source_presence(
		required_keywords,
		current_sections,
	)
	payload = {
		"job_description": job_description,
		"required_keywords": required_keywords,
		"keywords_present_in_source_cv": present_keywords,
		"keywords_missing_in_source_cv": missing_keywords,
		"current_sections": [
			{"path": path, "content": content} for path, content in current_sections.items()
		],
	}
	if rewrite_feedback:
		payload["rewrite_feedback"] = rewrite_feedback
	return json.dumps(payload, ensure_ascii=False)


def rewrite_sections(
	config: ProjectConfig,
	prompt_template_path: Path,
	job_description: str,
	current_sections: dict[str, str],
	rewrite_feedback: str | None = None,
) -> RewriteResult:
	system_prompt = prompt_template_path.read_text(encoding="utf-8")
	required_keywords = _extract_required_keywords(job_description)

	if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_ADMIN_KEY"):
		raise ValueError(
			"Missing OpenAI credentials. Set OPENAI_API_KEY (or OPENAI_ADMIN_KEY) before running tailor/run. "
			"Example: export OPENAI_API_KEY='your_key' and rerun, or pass it directly in Docker: "
			"docker compose run --rm -e OPENAI_API_KEY='your_key' ai-cv ..."
		)

	client = OpenAI()
	response = client.responses.create(
		model=config.model,
		temperature=config.temperature,
		max_output_tokens=config.max_output_tokens,
		input=[
			{"role": "system", "content": system_prompt},
			{
				"role": "user",
				"content": _build_input(job_description, current_sections, rewrite_feedback),
			},
		],
	)

	raw = response.output_text.strip()
	parsed = json.loads(raw)

	files = {}
	for item in parsed.get("files", []):
		path = item.get("path")
		content = item.get("content")
		if not path or content is None:
			continue
		files[path] = content

	if not files:
		raise ValueError("Model returned no file updates.")

	return RewriteResult(files=files, required_keywords=required_keywords)
