# copypase for now

FROM python:3.12

WORKDIR /app

COPY requirements.lock .
COPY requirements-dev.lock .
COPY pyproject.toml .
COPY src/ .


# RUN sed -i '/^-e/d' requirements.lock
# RUN pip install --no-cache-dir -r requirements.lock
# RUN pip install .

RUN pip install uv
RUN uv pip install --system -r requirements.lock

EXPOSE 8000

# в прод без reload
CMD ["uvicorn", "src.dual_choice.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
