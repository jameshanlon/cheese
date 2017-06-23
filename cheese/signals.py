from cheese.init_app import app
from flask_user.signals import user_sent_invitation, user_registered

@user_registered.connect_via(app)
def after_registered_hook(sender, user, user_invite):
    sender.logger.info("USER REGISTERED")

@user_sent_invitation.connect_via(app)
def after_invitation_hook(sender, **extra):
    sender.logger.info("USER SENT INVITATION")
