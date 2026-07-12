# ai-latex-cv-builder

AI-assisted LaTeX CV tailoring for Overleaf-style resumes.

It rewrites selected CV sections from a job description and compiles the result with your existing template.

## What It Does

1. Reads CV section `.tex` files.
2. Sends job description + current sections to the model.
3. Writes rewritten sections to a preview folder (`--dry-run`) or stages for build.
4. Compiles PDF via `latexmk`.

Current behavior is intentionally flexible: the app performs a single-pass rewrite and does not enforce strict line-length/keyword/metric constraints.

## Commands

The CLI supports 3 commands:

1. `tailor`
2. `build`
3. `run`

### `tailor`

Rewrite sections only.

```bash
python -m ai_latex_cv_builder --config config/project.yaml tailor --job job.txt
```

Preview mode (recommended first):

```bash
python -m ai_latex_cv_builder --config config/project.yaml tailor --job job.txt --dry-run
```

### `build`

Compile current LaTeX state to PDF (no AI call).

```bash
python -m ai_latex_cv_builder --config config/project.yaml build
```

### `run`

Rewrite then compile in one step:

```bash
python -m ai_latex_cv_builder --config config/project.yaml run --job job.txt
```

Build from an already reviewed preview:

```bash
python -m ai_latex_cv_builder --config config/project.yaml run --preview-dir output/preview-YYYYMMDD-HHMMSS
```

## Config

Start from:

```bash
cp config/project.example.yaml config/project.yaml
```

Main settings:

1. `latex_project_root`: root of the LaTeX CV project.
2. `main_tex_file`: main entry file (for example `main.tex` or `cv.tex`).
3. `section_files`: files AI can rewrite.
4. `latex_engine`: usually `xelatex`.
5. `output_dir`: where PDF/previews are written.

Compatibility note: config keys like `min_keyword_matches`, `min_metric_bullets`, and `max_experience_bullet_chars` may still exist in sample YAML, but they are currently not enforced in the relaxed rewrite flow.

### Unknown section names / custom templates

Set `section_files: []` to auto-discover section-like `.tex` files.

## Credentials

AI commands (`tailor`, `run`) require `OPENAI_API_KEY` (or `OPENAI_ADMIN_KEY`).

Local:

```bash
export OPENAI_API_KEY='<your-openai-api-key>'
```

Docker (inline):

```bash
docker compose run --rm -e OPENAI_API_KEY='<your-openai-api-key>' ai-cv --config config/project.docker.example.yaml tailor --job job.txt --dry-run
```

Important: `-e OPENAI_API_KEY` only forwards an existing host variable. If it is unset on host, container gets no key.

## Docker Usage

Build image:

```bash
docker compose build
```

Compile only:

```bash
docker compose run --rm ai-cv --config config/project.docker.example.yaml build
```

Tailor preview:

```bash
docker compose run --rm -e OPENAI_API_KEY='<your-openai-api-key>' ai-cv --config config/project.docker.example.yaml tailor --job job.txt --dry-run
```

Build from preview:

```bash
docker compose run --rm ai-cv --config config/project.docker.example.yaml run --preview-dir output/preview-YYYYMMDD-HHMMSS
```

Mount model used by default in this repo:

1. Repo mounted to `/app`
2. External CV mounted to `/cv`

## Project Files

1. `src/ai_latex_cv_builder/cli.py`: command routing.
2. `src/ai_latex_cv_builder/pipeline.py`: section read/write, preview flow, staging/build orchestration.
3. `src/ai_latex_cv_builder/ai_writer.py`: OpenAI request/response handling.
4. `src/ai_latex_cv_builder/latex.py`: `latexmk` PDF compilation.
5. `prompts/rewrite_sections.md`: model rewrite instructions.

## Notes

1. `build` does not require an API key.
2. `tailor --dry-run` is safest for review before applying changes.
3. Keep your local Overleaf directory structure intact (fonts/includes).
4. Review generated content for truthfulness before sharing.
