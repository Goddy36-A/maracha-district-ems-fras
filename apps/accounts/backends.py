from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

MAX_FAILED_ATTEMPTS = 5


class SecureAuthBackend(ModelBackend):
    """
    Wraps Django's default ModelBackend to add:
    - Rejection of locked accounts.
    - Failed-login-attempt counting with auto-lock after MAX_FAILED_ATTEMPTS.
    Passwords are still verified using Django's standard secure hashing;
    this backend does not implement custom password storage.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)  # mitigate user-enumeration timing attacks
            return None

        if user.is_locked:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            if user.failed_login_attempts:
                user.failed_login_attempts = 0
                user.save(update_fields=["failed_login_attempts"])
            return user

        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.is_locked = True
        user.save(update_fields=["failed_login_attempts", "is_locked"])
        return None
