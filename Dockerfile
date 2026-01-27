FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY app ./app
COPY frontend/dist /frontend/dist

ENV DOCKER_ENV=true
ENV TZ="Asia/Shanghai"

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000","--log-level","error"]
