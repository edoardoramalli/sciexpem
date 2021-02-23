"""SciExpeM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.status import *
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import authentication_classes, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny


import sys

from rest_framework.authtoken.models import Token
from rest_framework.response import Response


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'groups': user.groups.values_list('name', flat=True),
            'permissions': user.get_user_permissions(),
        })

@login_required
def UI(request):
    return render(request, 'FrontEnd/index.html')


# @never_cache
@authentication_classes([])
@permission_classes([])
def home(request):
    return render(request, 'FrontEnd/home.html')


@api_view(['GET'])
@permission_classes([])
def testAuthentication(request):
    print(request.user)
    if request.user.is_authenticated:
        return Response(status=HTTP_200_OK)
    else:
        return Response(status=HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def loginUser(request):
    params = request.data
    username = params['username']
    password = params['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response('Username or Password are wrong', status=HTTP_200_OK)
    else:
        return Response('Username or Password are wrong', status=HTTP_403_FORBIDDEN)


urlpatterns = [
    path('', home, name='home'),
    path('UI', UI, name='UI'),
    path('testAuthentication', testAuthentication),
    path('login', loginUser),
    path('admin/', admin.site.urls),
    path('frontend/', include('FrontEnd.urls')),
    path('ExperimentManager/', include('ExperimentManager.urls')),
    path('CurveMatching/', include('CurveMatching.urls')),
    path('OpenSmoke/', include('OpenSmoke.urls')),
    path('ReSpecTh/', include('ReSpecTh.urls')),
    path('getInfoUser', CustomAuthToken.as_view(), name='api_token_auth'),
    path('accounts/', include('django.contrib.auth.urls')),
]# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
