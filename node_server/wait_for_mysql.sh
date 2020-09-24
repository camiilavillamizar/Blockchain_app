#!/bin/sh

while ! mysqladmin ping -h"mysql_database" -P"3306" --silent; do
    echo "Waiting for MySQL to be up..."
    sleep 1
done

sleep 3
echo "Starting node_server..."
exit 0