FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN python -m pip install --no-cache-dir .
COPY examples/ examples/
COPY sales/ sales/

USER 10001:10001
ENTRYPOINT ["solutionfit"]
CMD ["calculate", "--input", "examples/fictional-scenario-v1.json"]
