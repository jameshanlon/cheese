from cheese.models import db, user_manager, User, Role
from cheese.factory import create_app
app = create_app()
user = User(email="admin@cheeseproject.co.uk", \
            password=user_manager.hash_password('admin'), \
            active=True)
with app.app_context():
  db.drop_all()
  db.create_all()
  user.roles.append(Role(name='admin'))
  db.session.add(user)
  db.session.commit()
