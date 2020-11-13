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
from rest_framework.authtoken.views import obtain_auth_token
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static


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
    path('ReSpecTh/', include('ReSpecTh.urls')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('accounts/', include('django.contrib.auth.urls')),
]
              # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
