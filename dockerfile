FROM python:3.11.1-slim
WORKDIR /
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "/src/main.py"]