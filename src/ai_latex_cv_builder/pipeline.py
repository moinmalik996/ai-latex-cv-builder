from __future__ import annotations

from datetime import datetime
import shutil
import re
from pathlib import Path
from dataclasses import replace

from .ai_writer import rewrite_sections
from .config import ProjectConfig
from .latex import compile_pdf


SECTION_DISCOVERY_SIGNAL_PATTERN = re.compile(
    r"\\(cvsection|section|cventry|cvparagraph|begin\s*\{cvitems\})",
    re.IGNORECASE,
)


class RewriteValidationError(ValueError):
    def __init__(self, message: str, code: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _brace_delta_ignoring_comments(content: str) -> int:
    # Track unescaped { and } while ignoring commented text after unescaped %.
    delta = 0
    for line in content.splitlines():
        in_comment = False
        i = 0
        while i < len(line):
            ch = line[i]
            prev = line[i - 1] if i > 0 else ""
            if not in_comment and ch == "%" and prev != "\\":
                in_comment = True
                i += 1
                continue
            if in_comment:
                i += 1
                continue

            if ch == "{" and prev != "\\":
                delta += 1
            elif ch == "}" and prev != "\\":
                delta -= 1
                if delta < 0:
                    return delta
            i += 1
    return delta


def _sanitize_tex_content(rel_path: str, content: str) -> str:
    delta = _brace_delta_ignoring_comments(content)
    if delta < 0:
        raise RewriteValidationError(
            f"Rewritten file has unmatched closing braces: {rel_path}",
            code="unmatched_closing_brace",
            details={"path": rel_path, "brace_delta": delta},
        )
    if delta == 0:
        return content

    suffix = "}" * delta
    if content.endswith("\n"):
        return content + suffix
    return content + "\n" + suffix


def _sanitize_rewritten_sections(rewritten: dict[str, str]) -> dict[str, str]:
    sanitized: dict[str, str] = {}
    for rel_path, content in rewritten.items():
        sanitized[rel_path] = _sanitize_tex_content(rel_path, content)
    return sanitized


def _discover_section_files(config: ProjectConfig) -> list[str]:
    discovered: list[str] = []
    main_tex = config.main_tex_file.strip().lstrip("./")
    for file_path in sorted(config.latex_project_root.rglob("*.tex")):
        rel = file_path.relative_to(config.latex_project_root).as_posix()
        if rel == main_tex:
            continue
        content = file_path.read_text(encoding="utf-8")
        if SECTION_DISCOVERY_SIGNAL_PATTERN.search(content):
            discovered.append(rel)

    if not discovered:
        raise ValueError(
            "No editable section files were discovered. "
            "Set section_files in config explicitly for this CV layout."
        )
    return discovered


def _resolve_section_files(config: ProjectConfig) -> list[str]:
    if config.section_files:
        return config.section_files
    return _discover_section_files(config)


def _read_sections(config: ProjectConfig) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel_path in _resolve_section_files(config):
        file_path = config.latex_project_root / rel_path
        out[rel_path] = file_path.read_text(encoding="utf-8")
    return out


def _write_sections(config: ProjectConfig, rewritten: dict[str, str]) -> None:
    for rel_path, content in rewritten.items():
        target = config.latex_project_root / rel_path
        target.write_text(content, encoding="utf-8")


def _create_worktree(config: ProjectConfig) -> Path:
    worktree_root = config.build_work_dir / "worktree"
    if worktree_root.exists():
        shutil.rmtree(worktree_root)
    shutil.copytree(config.latex_project_root, worktree_root)
    return worktree_root


def _write_preview(output_dir: Path, rewritten: dict[str, str]) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    preview_root = output_dir / f"preview-{ts}"
    for rel_path, content in rewritten.items():
        target = preview_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return preview_root


def _apply_preview(preview_root: Path, config: ProjectConfig) -> None:
    if not preview_root.exists():
        raise FileNotFoundError(f"Preview directory not found: {preview_root}")

    for source in preview_root.rglob("*"):
        if not source.is_file():
            continue
        relative_path = source.relative_to(preview_root)
        target = config.latex_project_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _validate_rewrites(
    config: ProjectConfig,
    current: dict[str, str],
    rewritten: dict[str, str],
    required_keywords: list[str],
    expected_paths: list[str],
) -> None:
    missing_paths = [path for path in expected_paths if path not in rewritten]
    if missing_paths:
        raise RewriteValidationError(
            "Model response is missing updates for configured files: " + ", ".join(missing_paths)
            ,
            code="missing_paths",
            details={"missing_paths": missing_paths},
        )


def _rewrite_once(
    config: ProjectConfig,
    prompt_template: Path,
    job_description: str,
) -> dict[str, str]:
    current = _read_sections(config)
    expected_paths = list(current.keys())
    result = rewrite_sections(
        config=config,
        prompt_template_path=prompt_template,
        job_description=job_description,
        current_sections=current,
        rewrite_feedback=None,
    )
    candidate_files = {path: result.files[path] for path in expected_paths if path in result.files}
    _validate_rewrites(config, current, candidate_files, result.required_keywords, expected_paths)
    return _sanitize_rewritten_sections(candidate_files)


def tailor_only(config: ProjectConfig, prompt_template: Path, job_description: str, dry_run: bool) -> Path | None:
    rewritten = _rewrite_once(config, prompt_template, job_description)

    if dry_run:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        return _write_preview(config.output_dir, rewritten)

    worktree_root = _create_worktree(config)
    staged_config = replace(config, latex_project_root=worktree_root)
    _write_sections(staged_config, rewritten)
    return None


def tailor_and_build(
    config: ProjectConfig,
    prompt_template: Path,
    job_description: str,
    dry_run: bool,
) -> Path:
    rewritten = _rewrite_once(config, prompt_template, job_description)

    if dry_run:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        preview = _write_preview(config.output_dir, rewritten)
        raise RuntimeError(
            f"Dry run complete. Review preview files at: {preview}. "
            "Run without --dry-run to apply and build PDF."
        )

    worktree_root = _create_worktree(config)
    staged_config = replace(config, latex_project_root=worktree_root)
    _write_sections(staged_config, rewritten)
    return compile_pdf(staged_config)


def build_from_preview(
    config: ProjectConfig,
    preview_dir: Path,
) -> Path:
    worktree_root = _create_worktree(config)
    staged_config = replace(config, latex_project_root=worktree_root)
    _apply_preview(preview_dir, staged_config)
    return compile_pdf(staged_config)
