FROM python:3.13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       latexmk \
       texlive-xetex \
       texlive-latex-extra \
         texlive-fonts-extra \
       texlive-fonts-recommended \
       texlive-lang-english \
     fonts-font-awesome \
       fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "ai_latex_cv_builder"]
