# ai-latex-cv-builder

AI-assisted LaTeX CV tailoring for Awesome-CV.

This repository is set up for a public-friendly workflow:
- the real CV template lives in [cv-template](cv-template)
- only `cv/summary.tex` and `cv/experience.tex` are rewritten
- the rest of the CV stays exactly as authored
- the final PDF is compiled from `cv-template/cv.tex`

## Why I Built This

When applying for jobs, I had the same repetitive process each time:

1. Paste the job description and my CV PDF into ChatGPT.
2. Ask for stronger keywords and role-matched statements.
3. Manually copy those updates into my Overleaf LaTeX files.
4. Rebuild the PDF and upload it for the application.

That workflow worked, but it was slow and repetitive.

This project is my way of partially automating that process. It rewrites only the sections I usually tailor most (`summary` and `experience`) and then rebuilds the full CV PDF.

It is not intended to be 100% automatic or perfect. I still review what AI generates before final submission, but this saves time and reduces repetitive manual edits.

## Quick Start

1. Copy the local config and env files:

```bash
make setup
```

2. Put your OpenAI key in [.env](.env).

3. Build the PDF:

```bash
make build
```

4. Tailor the CV with the sample job description:

```bash
make tailor JOB=job.sample.txt
```

5. Review the preview and compile the final PDF:

```bash
make run JOB=job.sample.txt
```

## What It Does

1. Reads the current `cv-template/cv/summary.tex` and `cv-template/cv/experience.tex` files.
2. Sends the job description plus those two section files to the model.
3. Writes rewritten sections to a preview folder when `--dry-run` is used.
4. Stages the rewritten sections back into the original `cv-template` tree.
5. Compiles the full PDF from `cv-template/cv.tex` with `latexmk`.

## Commands

### `tailor`
Rewrite the two targeted sections only.

```bash
python -m ai_latex_cv_builder --config config/project.yaml tailor --job job.sample.txt --dry-run
```

### `build`
Compile the current LaTeX template to PDF.

```bash
python -m ai_latex_cv_builder --config config/project.yaml build
```

### `run`
Rewrite the sections and compile the PDF in one step.

```bash
python -m ai_latex_cv_builder --config config/project.yaml run --job job.sample.txt
```

Build from an already reviewed preview:

```bash
python -m ai_latex_cv_builder --config config/project.yaml run --preview-dir output/preview-YYYYMMDD-HHMMSS
```

## Config

Copy the example config:

```bash
cp config/project.example.yaml config/project.yaml
```

The default config points to the bundled template in [cv-template](cv-template):

1. `latex_project_root: ../cv-template`
2. `main_tex_file: cv.tex`
3. `section_files: [cv/summary.tex, cv/experience.tex]`

If you want to use your own CV, copy that folder somewhere else and update those values in [config/project.yaml](config/project.yaml). Keep the folder name generic if you intend to publish the repo.

## Docker

Build the image:

```bash
docker compose build
```

Compile the PDF:

```bash
docker compose run --rm ai-cv build
```

Tailor the CV:

```bash
docker compose run --rm ai-cv tailor --job job.sample.txt --dry-run
```

Run the full flow from a preview:

```bash
docker compose run --rm ai-cv run --preview-dir output/preview-YYYYMMDD-HHMMSS
```

## Makefile Targets

1. `make setup` - copy `.env.example` and `config/project.example.yaml` if missing
2. `make build` - compile the PDF
3. `make tailor JOB=...` - generate a preview
4. `make run JOB=...` - tailor and build in one step
5. `make preview PREVIEW_DIR=...` - build from a reviewed preview

## Notes

1. `build` does not require an API key.
2. `tailor --dry-run` is the safest first step.
3. The repository intentionally keeps the rewrite scope narrow so users can keep their original CV structure.
