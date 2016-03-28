#!/bin/bash

usage() {
  echo usage: `basename $0` "<option>"
  exit 1
}

rebuild() {
  echo "Rebuilding containers..."
  
  # Remove the existing containers.
  docker rm website

  # (Re)build the website container.
  docker build -t website .

  # Create the website container and link with the db.
  docker create --name website \
    -p 9080:9080 \
    -v `pwd`:/opt/www \
    website
}

up() {
  echo "Starting containers..."
  docker start website
}

down() {
  echo "Stopping containers..."
  docker stop website
}

restart() {
  echo "Restarting website processes..."
  # Restart processes with supervisorctl.
  docker exec -it website \
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
