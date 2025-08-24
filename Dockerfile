FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
COPY pyproject.toml ./
RUN pip install .
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]