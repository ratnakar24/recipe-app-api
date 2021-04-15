from user.serializers import UserSerialer, AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework import generics


class CreateUserView(generics.CreateAPIView):
    """Creates a new user in the system"""
    serializer_class = UserSerialer


class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
