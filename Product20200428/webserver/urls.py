"""webserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from doodle import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('page2/', views.page2, name='page2'),
    path('page3/', views.page3, name='page3'),
    path('page4/', views.page4, name='page4'),
    path('parse/', views.parse, name='parse'),
    path('principle/', views.principle, name='principle'),
    path('save/', views.save_project, name='save'),
    path('bin/', views.bin, name='bin'),
    path('project/<int:pid>/delete/', views.project_delete, name='project_delete'),
    path('project/<int:pid>/rename/', views.project_rename, name='project_rename'),
    path('project/<int:pid>/reset/', views.project_reset, name='project_reset'),
    path('project/<int:pid>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:pid>/<str:method_type>/', views.project_parse, name='project_parse'),
    path('project/<int:pid>/showworking/<str:method_type>/', views.show_working, name='project_showworking'),
    path('project/<int:pid>/', views.project_detail, name='project_detail'),
    path('sendmail/', views.email, name="send_mail"),
    path('', views.index),
]
