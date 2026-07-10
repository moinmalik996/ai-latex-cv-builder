from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ProjectConfig:
    latex_project_root: Path
    main_tex_file: str
    section_files: list[str]
    latex_engine: str
    build_work_dir: Path
    output_dir: Path
    pdf_name: str
    model: str
    temperature: float
    max_output_tokens: int
    min_keyword_matches: int
    min_experience_keyword_matches: int
    min_missing_keyword_matches: int
    min_metric_bullets: int
    max_experience_bullet_chars: int

    @classmethod
    def from_yaml(cls, config_path: Path) -> "ProjectConfig":
        with config_path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        if not raw:
            raise ValueError(f"Config file is empty: {config_path}")

        base = config_path.parent
        project_root = (base / raw["latex_project_root"]).resolve()
        build_work_dir = (base / raw.get("build_work_dir", ".build")).resolve()
        output_dir = (base / raw.get("output_dir", "../output")).resolve()

        return cls(
            latex_project_root=project_root,
            main_tex_file=raw.get("main_tex_file", "main.tex"),
            section_files=raw.get("section_files", []),
            latex_engine=raw.get("latex_engine", "xelatex"),
            build_work_dir=build_work_dir,
            output_dir=output_dir,
            pdf_name=raw.get("pdf_name", "cv_tailored.pdf"),
            model=raw.get("model", "gpt-4o-mini"),
            temperature=float(raw.get("temperature", 0.2)),
            max_output_tokens=int(raw.get("max_output_tokens", 3500)),
            min_keyword_matches=int(raw.get("min_keyword_matches", 5)),
            min_experience_keyword_matches=int(raw.get("min_experience_keyword_matches", 4)),
            min_missing_keyword_matches=int(raw.get("min_missing_keyword_matches", 2)),
            min_metric_bullets=int(raw.get("min_metric_bullets", 2)),
            max_experience_bullet_chars=int(raw.get("max_experience_bullet_chars", 120)),
        )
