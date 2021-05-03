FROM debian:bullseye-slim
MAINTAINER James Hanlon

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y build-essential \
                       libffi-dev \
                       libssl-dev \
                       default-libmysqlclient-dev \
                       default-mysql-client \
                       libjpeg-dev \
                       python3 \
                       python3-dev \
                       python3-setuptools \
                       python3-pip

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

COPY mysql.cnf /etc/mysql/conf.d/
COPY uwsgi.ini /tmp
CMD uwsgi --ini /tmp/uwsgi.ini
