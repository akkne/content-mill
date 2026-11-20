FROM node:22-bookworm-slim AS script-cli
RUN npm install --global --prefix /opt/script-cli @openai/codex@0.170.0 @anthropic-ai/claude-code@2.1.316 \
    && /opt/script-cli/bin/codex --version && /opt/script-cli/bin/claude --version

FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
RUN pip install --no-cache-dir .

COPY --from=script-cli /opt/script-cli /opt/script-cli
COPY --from=script-cli /usr/local/bin/node /usr/local/bin/node
ENV PATH="/opt/script-cli/bin:${PATH}"

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
