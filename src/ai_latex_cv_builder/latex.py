from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import ProjectConfig


def _engine_flag(engine: str) -> str:
    e = engine.lower().strip()
    if e == "xelatex":
        return "-xelatex"
    if e == "lualatex":
        return "-lualatex"
    if e == "pdflatex":
        return "-pdf"
    raise ValueError(f"Unsupported latex_engine: {engine}")


def compile_pdf(config: ProjectConfig) -> Path:
    config.build_work_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "latexmk",
        _engine_flag(config.latex_engine),
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory=" + str(config.build_work_dir),
        config.main_tex_file,
    ]

    completed = subprocess.run(
        cmd,
        cwd=config.latex_project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "LaTeX build failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )

    built_pdf = config.build_work_dir / Path(config.main_tex_file).with_suffix(".pdf").name
    if not built_pdf.exists():
        raise FileNotFoundError(f"Expected PDF not found: {built_pdf}")

    final_pdf = config.output_dir / config.pdf_name
    shutil.copy2(built_pdf, final_pdf)
    return final_pdf
