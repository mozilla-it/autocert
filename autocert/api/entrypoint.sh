#!/bin/bash

AC_EP="$0"
echo "this script is: $AC_EP"

AC_UID=${AC_UID:-0}
AC_GID=${AC_GID:-0}
AC_USER=${AC_USER:-root}
AC_APP_TIMEOUT=${AC_APP_TIMEOUT:-120}
AC_APP_PORT=${AC_APP_PORT:-8000}
AC_APP_WORKERS=${AC_APP_WORKERS:-2}
AC_APP_MODULE=${AC_APP_MODULE:-main:app}
CMD="python3 -u /usr/local/bin/gunicorn -t $AC_APP_TIMEOUT -w $AC_APP_WORKERS -b :$AC_APP_PORT $AC_APP_MODULE"

if ! getent passwd "$AC_USER" 2>/dev/null; then
    echo "creating user $AC_USER with $AC_UID:$AC_GID"
    groupadd --gid "$AC_GID" "$AC_USER"
    useradd --uid "$AC_UID" --gid "$AC_GID" --shell /bin/bash --no-create-home "$AC_USER"
    echo -e "\n$AC_USER   ALL=(ALL) NOPASSWD: ALL\n" > /etc/sudoers
    chown -R "$AC_USER:$AC_USER" /usr/src/app/
fi

echo "executing \"$CMD\" as $AC_USER"
exec su -c "$CMD" "$AC_USER"
