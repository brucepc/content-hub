from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from easyconnect.hw_api import EasyconnectApApi
hw_api = EasyconnectApApi()

USER_ADMIN_NAME = getattr(settings, 'USER_ADMIN_NAME', None)
USER_ADMIN_EMAIL = getattr(settings, 'USER_ADMIN_EMAIL', None)
USER_ADMIN_PASSWD = getattr(settings, 'USER_ADMIN_PASSWD', None)
USER_TEACH_NAME = getattr(settings, 'USER_TEACH_NAME', None)
USER_TEACH_PASSWD = getattr(settings, 'USER_TEACH_PASSWD', None)

import logging
logger = logging.getLogger(__name__)

def update_teacher_account():
    try:
        teacher_hw_user, teacher_hw_pass = hw_api.get_teacher_account()
        if teacher_hw_user is not None:
            try:
                teach_user = User.objects.get(username__exact=teacher_hw_user)
                teach_user.set_password(teacher_hw_pass)
                teach_user.save()
                Token.objects.create(user=teach_user)
            except:
                logger.info('API account name does not exist.')

                allusers = User.objects.all()
                for singleuser in allusers:
                    singleuser.delete()
                teach_user = User.objects.create_user(username=teacher_hw_user, password=teacher_hw_pass)
                teach_user.save()
                Token.objects.create(user=teach_user)
    except Exception as e:
        #logger.exception(e)
        try:
            teach_user = User.objects.create_user(username=USER_TEACH_NAME, password=USER_TEACH_PASSWD)
            teach_user.save()
            Token.objects.create(user=teach_user)
        except Exception as e:
            logger.info('default teacher username exists. Continuing startup...')

# Create the default admin and teacher users
# admin_user = User.objects.create_superuser(username=USER_ADMIN_NAME, email=USER_ADMIN_EMAIL, password=USER_ADMIN_PASSWD)

def update_admin_account():
    try:
        admin_hw_user, admin_hw_pass = hw_api.get_admin_account()
        if admin_hw_user is not None:
            try:
                admin_user = User.objects.get(username__exact=admin_hw_user)
                admin_user.set_password(admin_hw_pass)
                admin_user.save()
                Token.objects.create(user=admin_user)
            except:
                admin_user = User.objects.create_superuser(username=admin_hw_user, email=USER_ADMIN_EMAIL, password=admin_hw_pass) #email is unused but required
                admin_user.save()
                Token.objects.create(user=admin_user)
    except Exception as e:
        #logger.exception(e)
        try:
            admin_user = User.objects.create_superuser(username=USER_ADMIN_NAME, email=USER_ADMIN_EMAIL, password=USER_ADMIN_PASSWD)
            admin_user.save()
            Token.objects.create(user=admin_user)
        except Exception as e:
            logger.info('default admin exists. Continuing startup...')