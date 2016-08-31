FROM nginx
MAINTAINER James Hanlon

RUN mkdir /etc/nginx/sites-available && \
    mkdir /etc/nginx/sites-enabled

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY uwsgi_params /tmp
