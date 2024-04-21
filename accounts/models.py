import random
import string
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import User 

ID_CHOICES = (
    ('Driver License', 'Driver License'),
    ('Postal ID', 'Postal ID'),
)

ACCOUNT_TYPE_CHOICES = (
    ('Buyer', 'Buyer'),
    ('Seller', 'Seller'),
)

class PersonAccount(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256, null=False, blank=False)
    last_name = models.CharField(max_length=256, null=False, blank=False)
    phone = models.CharField(max_length=11)
    address = models.CharField(max_length=256,)
    id_options = models.CharField(choices=ID_CHOICES, max_length=64)
    id_image = models.ImageField()
    creationDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)
    account_type = models.CharField(choices=ACCOUNT_TYPE_CHOICES, max_length=64)

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.account_type}'

class UserAccountManager(models.Manager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class UserAccount(User):
    objects = UserAccountManager()

    class Meta:
        proxy = True

    REQUIRED_FIELDS = ['email']

class ShopifyAccess(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    shopify_url = models.CharField(max_length=256)
    api_key = models.CharField(max_length=256)
    api_secret = models.CharField(max_length=256)
    access_token = models.CharField(max_length=256)

    def __str__(self):
        return f'{self.shopify_url} - {self.api_key}'
    
class Live(models.Model):
    title = models.CharField(max_length=70, null=False, blank=False)
    description = models.CharField(max_length=150)
    createdBy = models.ForeignKey(PersonAccount, null=False, blank=False, on_delete= models.DO_NOTHING)
    creationDate = models.DateTimeField(auto_now_add=True)
    live = models.BooleanField()

    def __str__(self):
        return f'{self.title} - {self.description}'
    
class OTP(models.Model):
    email = models.CharField(max_length=256)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f'{self.email} - {self.otp_code} - {self.created_at} - {self.expires_at}'

    @classmethod
    def create_otp(cls, email):
        otp_instance = cls(email=email)

        otp_instance.otp_code = ''.join(random.choices(string.digits, k=6))

        otp_instance.expires_at = datetime.now() + timedelta(hours=1)

        otp_instance.save()

        return otp_instance