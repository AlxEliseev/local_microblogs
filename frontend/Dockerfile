FROM nginx

COPY ./dist/css /usr/share/nginx/html/css
COPY ./dist/js /usr/share/nginx/html/js
COPY ./dist/favicon.ico /usr/share/nginx/html
COPY ./dist/index.html /usr/share/nginx/html

COPY ./nginx.conf /etc/nginx/nginx.conf