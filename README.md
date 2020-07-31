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

Update Python packages:
```
$ pip install --upgrade -r flask/requirements.txt
```

### Setup on OSX

```
$ brew install mysql openssl
$ export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/
$ virtualenv env
$ pip install -r flask/requirements.txt
...
```

Troubleshooting:
- https://stackoverflow.com/questions/12218229/my-config-h-file-not-found-when-intall-mysql-python-on-osx-10-8

### Populate CONFIG

- `FLASK_APP=run.py`
- `FLASK_ENV=development`
- `CHEESE_EMAIL_SENDER` must be set for mail to work (even if it is disabled
  for debug).
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

To initialise a testing database:
```
$ docker exec -it <cheese-flask> bash
$ cd /opt/www
$ FLASK_APP=run.py flask resetdb command.
```

To initialise a new, empty database, use the commands from `resetdb()` in
`cheese/commands.py`, eg:
```
$ docker exec -it <cheese-flask> bash
$ cd /opt/www
$ python
>>> from cheese.factory import create_app
>>> app = create_app({})
>>> from cheese.models import User, Role
>>>  user = User(email="admin@cheeseproject.co.uk", \
       password=user_manager.hash_password('admin'), \
       is_active=True)
>>> with app.app_context():
...  db.drop_all()
...  db.create_all()
...  user.roles.append(Role(name='admin'))
...  db.session.add(user)
...  db.session.commit()
```

To restore a local database from a backup:
```
mysql -u root -p < mysql-backup.sql
```
Or restore a database in a Docker container:
```
cat mysql-backup.sql | docker exec -i flask_container_1 mysql -h database_container_1
```
The `-h` host parameter may not be necessary.

Migrating to MariaDB caused an issue with MySQL connections timing
out, giving 'MySQL has gone away error message'. See details of the
fix on [Stack Overflow][1] and [Flask documentation][2].

[1]: https://stackoverflow.com/questions/51506416/mariadb-server-times-out-client-connection-after-600-seconds
[2]: http://flask-sqlalchemy.pocoo.org/2.3/config/#timeouts

### Run the development server

```
$ source env/bin/activate
$ source CONFIG # Make sure FLASK_APP and FLASK_DEBUG set.
$ flask run
...
```
Note that uWSGI can be run manually, e.g.:
```
uwsgi --http 0.0.0.0:9000 --manage-script-name --wsgi-file run.py --callable app
```

### Run the unit tests

```
$ source CONFIG
$ source env/bin/activate
$ pytest --verbose
...
```
Run a particular test, or tests matching a regex:
```
$ pytest --verbose -k test_apply_for_survey_form
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
- Rebuild a single container (eg to update environment):
```
$ docker-compose ps
$ docker-compose down <service_name>
$ docker-compose up -d --no-deps --build <service_name>
```

### Perform a database migration

Create the migration and run the upgrade from in the container.
```
$ docker exec -it <continer-name> bash
$ cd /opt/www
$ FLASK_APP=run.py flask db migrate
...
$ FLASK_APP=run.py flask db upgrade
...
$ exit
```
Then commit the new migration Python script.

### Setup SSL

Install and run certbot to use Lets Encrypt the quick and easy way
(assuming Debian Jessie). Currently this needs to be done any time
the proxy container is rebuilt.
```
$ docker exec -it <proxy-containter> bash
$ apt-get install wget
$ wget https://dl.eff.org/certbot-auto
$ chmod a+x certbot-auto
$ ./certbot-auto --nginx
```
To renew:
```
$ docker exec -it <proxy-containter> bash
$ /usr/local/bin/certbot-auto renew
```
More details at https://certbot.eff.org/lets-encrypt

#### Old method

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

### Using S3 storage

Examples:
```
s3cmd la --recursive s3://jwh/cheese/
s3cmd put images/* s3://jwh/cheese/files/images
s3cmd rm  s3://jwh/cheese/images/.*
s3cmd setacl s3://jwh/cheese --acl-public --recursive
```

## Misc

Resize a set of images using ImageMagick to a fixed width (only shrink), eg:
```
$ convert '*.{jpg,JPG}[800x>]' -auto-orient <album-name>-%0d.jpg
```
See http://www.imagemagick.org/script/command-line-processing.php#geometry
