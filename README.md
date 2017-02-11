# The CHEESE Project website.

The CHEESE Project aims to reduce domestic energy losses, at low cost, by up to
a third. This saves money, improves health and wellbeing and, reduces our
carbon emissions. Visit it at: http://www.cheeseproject.co.uk.

## Development notes

### Python dependencies

```
$ virtualenv env
$ source env/bin/activate
$ pip install -r flask/requirements.txt
```

### Populate CONFIG

- `CHEESE_MYSQL_HOST` must be set to the name of the MySQL Docker container.
- `CHEESE_MYSQL_DATA_DIR` must be set to a location on the host machine, in
  which to store the MySQL data.

Run `./update-env.sh` to create the mysql.cnf file.

### Setup a local MySQL server

Create a MySQL user and database, setting the correct permissions (this happens
automatically in the MySQL Docker container):
```
$ mysql -u root -p
mysql> create database <database>;
mysql> create user '<username>'@'localhost' identified by '<password>';
mysql> grant all privileges on <database>.* to '<username>'@'localhost'
identified by '<password>';
mysql> flush privileges;
mysql> exit
```

### Populate the database

To initialise a minimal database:
```
$ docker exec -it <cheese-flask> bash
$ cd /opt/www
$ python
>>> from website import db, People
...
>>> db.drop_all()
>>> db.create_all()
>>> from werkzeug.security import generate_password_hash
>>> person = People(email="admin", password=generate_password_hash("..."), group='Admin')
>>> db.session.add(person)
>>> db.session.commit()
```
Or use the `website.py populate_db` command.

### Run the development server

```
$ source env/bin/activate
$ source CONFIG
$ python website.py runserver
...
```

## Deployment notes

### Perform a database migration

Create the migration and run the upgrade from in the container.
```
$ docker exec -it <continer-name> bash
$ cd /opt/www
$ python website.py db migrate
...
$ python website.py db upgrade
...
$ exit
```
Then commit the new migration Python script.

### Setup SSL

Generate a certificate signing request:
```
$ openssl req -new -newkey rsa:2048 -nodes \
	-keyout cheeseproject.co.uk.key -out cheeseproject.co.uk.csr
```

Obtain the certificate (.crt) and intermediate certificate (.pem) from the
certificate provider.

Append the intermediate certificate to the certificate:
```
$ cat intermediate.pem >> cheeseproject.co.uk.crt
```
Place the `.crt` and `.key` files in a directory for the webserver to access:
```
$ ls ssl/
cheeseproject.co.uk.crt       cheeseproject.co.uk.csr
cheeseproject.co.uk.gandi.pem cheeseproject.co.uk.key
```
