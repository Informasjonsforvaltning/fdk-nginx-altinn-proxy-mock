#!/usr/bin/env sh
set -eu

envsubst '${API_KEY}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# start request-aware v2 mock handler for authorizedparties filtering by SSN
python3 /scripts/v2_mock_server.py &

exec "$@"