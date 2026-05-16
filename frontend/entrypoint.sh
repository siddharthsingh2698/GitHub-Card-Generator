#!/bin/sh

# Substitute environment variables in the HTML template
export BACKEND_URL=${BACKEND_URL:-http://localhost:8080}
envsubst < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html

# Start nginx in foreground
exec nginx -g 'daemon off;'
