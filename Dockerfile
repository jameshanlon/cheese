FROM nginx
MAINTAINER James Hanlon

# Nginx config.
RUN mkdir /etc/nginx/sites-available && \
    mkdir /etc/nginx/sites-enabled
COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-cheese.conf /etc/nginx/sites-available/
RUN rm /etc/nginx/conf.d/default.conf && \
    ln -s /etc/nginx/sites-available/nginx-cheese.conf \
          /etc/nginx/sites-enabled/nginx-cheese.conf
