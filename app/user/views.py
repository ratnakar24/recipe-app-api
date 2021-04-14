from user.serializers import UserSerialer
from rest_framework import generics


class CreateUserView(generics.CreateAPIView):
    """Creates a new user in the system"""
    serializer_class = UserSerialer
