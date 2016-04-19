FROM nginx
MAINTAINER James Hanlon

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-cheese.conf /etc/nginx/sites-available/
