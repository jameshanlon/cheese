#!/bin/bash
echo "Performing backup..."
DATE=$(date +"%m-%d-%y-%H-%M")
FILENAME="backup-${CHEESE_MYSQL_DATABASE}_${DATE}.sql"
# Do a mysqldump.
docker exec -it ${CHEESE_CONTAINER_NAME} \
	mysqldump $MYSQL_DATABASE > ./$FILENAME
echo "Done: created '$FILENAME'"
