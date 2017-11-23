from cheese.init_app import app, mail
from flask_mail import Message
from flask_user.signals import user_sent_invitation, user_registered

@user_registered.connect_via(app)
def after_registered_hook(sender, user, user_invite):
    sender.logger.info("User {} registered".format(user.email))
    subject='[CHEESE] User {} registered'.format(user.email)
    message='Update their roles: '+app.config['URL_BASE']+'/admin/user/'
    mail.send(Message(subject=subject,
                      body=message,
                      recipients=[app.config['ADMINS']]))
