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
>>> from cheese.init_app import app, init_app, db
>>> init_app(app)
>>> from cheese.init_app import user_manager
>>> from cheese.models import User, Role
>>> db.drop_all()
>>> db.create_all()
>>> user = User(email="admin@cheeseproject.co.uk", \
      password=user_manager.hash_password('admin'), \
      is_active=True)
>>> user.roles.append(Role(name='admin'))
>>> db.session.add(user)
>>> db.session.commit()
```
Or use the `manage.py resetdb` command.

### Run the development server

```
$ source env/bin/activate
$ source CONFIG
$ python manage.py runserver
...
```
Note that uWSGI can be run manually, e.g.:
```
uwsgi --http 0.0.0.0:9000 --manage-script-name --wsgi-file wsgi.py --callable app
```

## Deployment notes

### From scratch

- Create the CONFIG file as described above.
- Create the MySQL database as described above.
- Copy the `docker-compose.yml.in` file and populate it:
```
$ cp docker-compose.yml.in docker-compose.yml
$ ./update-env.sh
```
- Build and start the Docker containers:
```
$ docker-compose build
...
$ docker-compose up
...
```

### Perform a database migration

Create the migration and run the upgrade from in the container.
```
$ docker exec -it <continer-name> bash
$ cd /opt/www
$ python manage.py db migrate
...
$ python manage.py db upgrade
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

## Misc

Resize a set of images using ImageMagick to a fixed width (only shrink), eg:
```
$ convert '*.JPG[650x>]' -auto-orient 2017-10-training-%03d.jpg
```
See http://www.imagemagick.org/script/command-line-processing.php#geometry
