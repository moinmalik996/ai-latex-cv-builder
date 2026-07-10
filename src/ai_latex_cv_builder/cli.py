from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .config import ProjectConfig
from .latex import compile_pdf
from .pipeline import build_from_preview, tailor_and_build, tailor_only


def _read_job_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Job description file is empty: {path}")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI-assisted LaTeX CV builder")
    parser.add_argument(
        "--config",
        default="config/project.yaml",
        help="Path to project yaml config",
    )
    parser.add_argument(
        "--prompt-template",
        default="prompts/rewrite_sections.md",
        help="Prompt template path",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    tailor = sub.add_parser("tailor", help="Rewrite configured section files only")
    tailor.add_argument("--job", required=True, help="Path to job description text file")
    tailor.add_argument("--dry-run", action="store_true", help="Write preview only")

    build = sub.add_parser("build", help="Compile current LaTeX project to PDF")

    run = sub.add_parser("run", help="Rewrite sections then compile PDF, or build from preview")
    run.add_argument(
        "--preview-dir",
        required=False,
        help="Existing dry-run preview directory to apply and compile exactly as reviewed",
    )
    run.add_argument("--job", required=False, help="Path to job description text file")
    run.add_argument("--dry-run", action="store_true", help="Write preview only")

    return parser


def main() -> None:
    load_dotenv()

    args = build_parser().parse_args()
    config = ProjectConfig.from_yaml(Path(args.config))
    prompt_template = Path(args.prompt_template)

    if args.command == "tailor":
        job = _read_job_description(Path(args.job))
        preview = tailor_only(config, prompt_template, job, dry_run=args.dry_run)
        if preview:
            print(f"Dry run preview written to: {preview}")
        else:
            print("Sections staged in build worktree.")
        return

    if args.command == "build":
        pdf = compile_pdf(config)
        print(f"PDF generated: {pdf}")
        return

    if args.command == "run":
        if args.preview_dir:
            pdf = build_from_preview(config, Path(args.preview_dir))
            print(f"PDF generated from preview: {pdf}")
            return

        if not args.job:
            raise ValueError("--job is required when --preview-dir is not provided.")

        job = _read_job_description(Path(args.job))
        pdf = tailor_and_build(config, prompt_template, job, dry_run=args.dry_run)
        print(f"PDF generated: {pdf}")
        return

    raise RuntimeError(f"Unknown command: {args.command}")
