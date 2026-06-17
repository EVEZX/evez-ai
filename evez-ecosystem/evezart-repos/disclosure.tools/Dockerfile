FROM python:3.12-slim

LABEL maintainer="Steven Crawford-Maggard <rubikspubes69@gmail.com>"
LABEL description="disclosure.tools — UAP/FOIA eigenforensics gap detector"
LABEL version="0.1.0"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import gap_detector; print('ok')" || exit 1

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
