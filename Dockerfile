FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock pyproject.toml .env ./

RUN pip install uv
RUN uv pip install --system -e .

EXPOSE 8001

CMD ["uvicorn", "src.dual_choice.main:app", "--host", "0.0.0.0", "--port", "8000"]
