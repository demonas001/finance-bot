FROM python:3.11
WORKDIR /fin-bot
COPY . /fin-bot/
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", main.py]
