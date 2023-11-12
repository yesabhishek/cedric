from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import AccessToken
from .models import CustomUser
import requests
from django.conf import settings

def get_user_from_token(token):
    try:
        # Decode the token
        decoded_token = AccessToken(token)
        # Get the user ID
        user_id = decoded_token['user_id']
        # Get the user instance
        user = CustomUser.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError):
        # Handle invalid or expired token
        print("Invalid or expired token.")
    except ObjectDoesNotExist:
        # Handle non-existent user
        print("User does not exist.")
