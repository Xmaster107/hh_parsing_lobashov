FROM python:3

COPY . /python

RUN pip install requests
RUN pip install telebot

WORKDIR /python

EXPOSE 666

CMD [ "python", "main.py" ]