FROM python:3.10-slim

RUN apt-get update && apt-get install -y git cmake make g++ libssl-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone --recursive https://github.com/tdlib/telegram-bot-api.git
RUN mkdir -p telegram-bot-api/build && cd telegram-bot-api/build && cmake -DCMAKE_BUILD_TYPE=Release .. && cmake --build . -j2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
