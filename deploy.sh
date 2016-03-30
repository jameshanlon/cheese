#!/bin/bash

usage() {
  echo usage: `basename $0` "<option>"
  exit 1
}

rebuild() {
  echo "Rebuilding containers..."
  
  # Remove the existing containers.
  docker rm cheese-website

  # (Re)build the cheese-website container.
  docker build -t cheese-website .

  # Create the cheese-website container and link with the db.
  docker create --name cheese-website \
    -p 9080:9080 \
    -v `pwd`:/opt/www \
    cheese-website
}

up() {
  echo "Starting containers..."
  docker start cheese-website
}

down() {
  echo "Stopping containers..."
  docker stop cheese-website
}

restart() {
  echo "Restarting cheese-website processes..."
  # Restart processes with supervisorctl.
  docker exec -it cheese-website \
    service nginx restart
}

refresh() {
  down
  rebuild
  up
}

# Perform an action.
case "$1" in
  "down" )
    down;;
  "up" )
    up;;
  "restart" )
    restart;;
  "rebuild" )
    rebuild;;
  "refresh" )
    refresh;;
  *)
    echo ERROR: $* 1>&2
    usage;;
esac
