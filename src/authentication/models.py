from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.timezone import now
import datetime


GENDER_CHOICES  = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))

contact_validator = [
    RegexValidator(regex=r'^[6-9]{1}[0-9]{9}$', message="Please enter a valid 10-digit mobile number.")
]

def regex_validators(value):
    err = None
    for validator in contact_validator:
        try:
            validator(value)
            return value
        except ValidationError as exc:
            err = exc
    raise err

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        
        email = self.normalize_email(email)
        existing_user = self.model.objects.filter(email=email).exists()
        
        if existing_user:
            raise ValueError('A user with this email already exists')
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    """ Required Parameters """
    name    = models.CharField(('Full Name'),max_length=100, blank=True)
    email   = models.EmailField('Email Address', unique=True)
    mobile  = models.CharField(('Mobile'), max_length=10, validators=[regex_validators,])

    """ Optional Profile Details  """
    dob = models.DateField(('Date of birth'), blank=True, null=True)
    avatar  = models.FileField(('Profile Picture'), blank=True, null=True)
    gender  = models.CharField(('Gender'), blank=True, max_length=1, choices=GENDER_CHOICES)
    state   = models.CharField(('State'),  blank=True, max_length=30)
    country = models.CharField(('Country'), max_length=200, blank=True, default="India")


    """ Account level details """
    is_subscription_active = models.BooleanField("Is Subscription Active", default=False)
    is_trial = models.BooleanField("Is Trial Period", default=True)
    is_admin    = models.BooleanField("Is Admin", blank=True, null=True, default=False)
    is_verified = models.BooleanField("Is Verified",blank=True, null=True, default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return{
            'refresh':str(refresh),
            'access':str(refresh.access_token)
        }