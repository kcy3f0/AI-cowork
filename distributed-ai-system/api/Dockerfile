FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 預設啟動 fastapi server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
