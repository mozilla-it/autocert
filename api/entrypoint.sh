#!/bin/bash

AC_EP="$0"
AC_USER=${AC_USER:-root}
AC_UID=${AC_UID:-0}

echo "AC_EP=$AC_EP AC_USER=$AC_USER AC_UID=$AC_UID"

python3 -u /usr/local/bin/gunicorn -t 120 -w 2 -b :8000 main:app
