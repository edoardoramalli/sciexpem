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
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import ObtainAuthToken


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
# @never_cache
def index(request):
    return render(request, 'FrontEnd/index.html')




urlpatterns = [
    path('', index),
    path('admin/', admin.site.urls),
    path('frontend/', include('FrontEnd.urls')),
    path('ExperimentManager/', include('ExperimentManager.urls')),
    path('CurveMatching/', include('CurveMatching.urls')),
    path('OpenSmoke/', include('OpenSmoke.urls')),
    path('ReSpecTh/', include('ReSpecTh.urls')),
    path('getInfoUser', CustomAuthToken.as_view(), name='api_token_auth'),
    path('accounts/', include('django.contrib.auth.urls')),
]# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
