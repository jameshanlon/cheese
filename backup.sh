#!/bin/bash
echo "Performing backup..."
DATE=$(date +"%m-%d-%y-%H-%M")
FILENAME="${CHEESE_BACKUP_DIR}/backup-${CHEESE_MYSQL_DATABASE}_${DATE}.sql"
# Do a mysqldump.
docker exec -it ${CHEESE_CONTAINER_NAME} \
	mysqldump $CHEESE_MYSQL_DATABASE > $FILENAME
# Remove backups older than 30 days.
echo "Done: created '$FILENAME'"
echo "Removing old backups:"
find ${CHEESE_BACKUP_DIR} -type f -mtime +30 -print -exec rm {} +
