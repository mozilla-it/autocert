#!/bin/bash

AC_EP="$0"
AC_UID=${AC_UID:-0}
AC_GID=${AC_GID:-0}
AC_USER=${AC_USER:-root}
AC_CMD="python3 -u /usr/local/bin/gunicorn -t 120 -w 2 -b :8000 main:app"

if ! getent passwd $AC_USER 2>/dev/null; then
    echo "creating user $AC_USER with $AC_UID:$AC_GID"
    groupadd --gid $AC_GID $AC_USER
    useradd --uid $AC_UID --gid $AC_GID --shell /bin/bash --no-create-home $AC_USER
    echo -e "\n$AC_USER   ALL=(ALL) NOPASSWD: ALL\n" > /etc/sudoers
fi

echo "executing \"$AC_CMD\" as $AC_USER"
exec su -c "$AC_CMD" $AC_USER
