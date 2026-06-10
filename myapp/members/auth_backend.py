from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import User


class PhoneOrUsernameModelBackend(ModelBackend):
    """Authenticate with username or phone number + password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        if password is None:
            return None
        try:
            user = User.objects.get(Q(username=username) | Q(phone=username))
        except User.DoesNotExist:
            # Also try display_name as fallback
            try:
                user = User.objects.get(display_name=username)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                return None
        except User.MultipleObjectsReturned:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
