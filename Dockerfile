FROM python:2.7

RUN mkdir /code
WORKDIR /code

RUN apt-get update && apt-get -y install ghostscript

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD . /code

CMD ["sniffer"]