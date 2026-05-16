FROM nginx:alpine

# Install gettext (provides envsubst)
RUN apk add --no-cache gettext

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy index.html template
COPY index.html /usr/share/nginx/html/index.html.template

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
