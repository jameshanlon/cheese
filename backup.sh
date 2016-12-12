#!/bin/bash
set -e
if [ -z ${CHEESE_BACKUP_DIR+x} ]; then
  echo "CHEESE_BACKUP_DIR not set!"
  exit 1
fi
echo "Performing backup..."
DATE=$(date +"%m-%d-%y-%H-%M")
FILENAME="${CHEESE_BACKUP_DIR}/backup-${CHEESE_MYSQL_DATABASE}_${DATE}.sql"
# Do a mysqldump.
docker exec -it ${CHEESE_CONTAINER_NAME} \
	mysqldump $CHEESE_MYSQL_DATABASE > $FILENAME
# Remove backups older than 90 days.
echo "Done: created '$FILENAME'"
echo "Removing old backups:"
find ${CHEESE_BACKUP_DIR} -type f -mtime +90 -print -exec rm {} +
