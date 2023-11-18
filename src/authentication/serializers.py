from rest_framework import serializers
from authentication.models import CustomUser as User
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
import datetime


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["name", "email", "password"]

    def validate(self, attrs):
        email = attrs.get("email", "")
        name = attrs.get("name", "")
        if not name:
            raise serializers.ValidationError({"name": "This field is required."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=8, write_only=True)
    email = serializers.EmailField(
        max_length=255,
    )
    tokens = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    name = serializers.CharField(max_length=68, min_length=8, read_only=True)

    def get_tokens(self, obj):
        user = User.objects.get(email=obj["email"])
        return {"refresh": user.tokens()["refresh"], "access": user.tokens()["access"]}

    class Meta:
        model = User
        fields = [
            "name",
            "password",
            "email",
            "tokens",
            "is_subscription_active",
            "is_trial",
            "created_at",
            "updated_at"
        ]

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        user = auth.authenticate(email=email, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")
        if not user.is_active:
            raise AuthenticationFailed("Account disabled, contact admin")
        if (
            user
            and user.is_trial
            and (datetime.datetime.now().date() - user.created_at.date()).days >= 14
        ):
            user.is_trial = False
            user.save()
        return {
            "name": user.name,
            "email": user.email,
            "tokens": user.tokens,
            "is_subscription_active": user.is_subscription_active,
            "is_trial": user.is_trial,
            "created_at": str(user.created_at.date()),
            "updated_at": str(user.updated_at.date()),
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail("bad_token")


class ResetPasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField()

    class Meta:
        model = User
        fields = ["email", "new_password"]

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value

    def save(self, **kwargs):
        email = self.email
        new_password = self.new_password
        user = User.objects.get(email=email)
        user.password = set_password(new_password)
        user.save()
