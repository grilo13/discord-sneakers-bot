FROM python:3.9.6

WORKDIR /app

RUN pip install -q poetry && \
    poetry config virtualenvs.create false


RUN apt-get update

COPY poetry.lock pyproject.toml /app/

RUN poetry config experimental.new-installer false
RUN poetry config virtualenvs.create false
RUN poetry install -n --no-dev --no-root
RUN poetry config experimental.new-installer true

COPY bot.py /app/
COPY discord-bot.py /app/
COPY user_info.json /app/

CMD ["python", "discord-bot.py"]