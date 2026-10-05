from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.errors import error_body
from .login_limits import authenticate_limited


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        max_length=128, trim_whitespace=False, write_only=True
    )


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses=inline_serializer("CsrfToken", {"csrfToken": serializers.CharField()})
    )
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_limited(request, **serializer.validated_data)
        if user is None:
            return Response(
                error_body(
                    "invalid_credentials",
                    "No se pudo iniciar sesión. Revisa tus datos o inténtalo más tarde.",
                ),
                status=400,
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    @extend_schema(
        request=None,
        responses=inline_serializer(
            "LogoutResult", {"status": serializers.CharField()}
        ),
    )
    def post(self, request):
        logout(request)
        return Response({"status": "ok"})


class MeView(APIView):
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
