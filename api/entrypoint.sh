#!/bin/bash

echo "name: $0"
echo "args: $@"

python3 -u /usr/local/bin/gunicorn -t 120 -w 2 -b :8000 main:app
