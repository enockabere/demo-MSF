from django.urls import path
from . import views

urlpatterns = [
    path('', views.Login.as_view(), name='auth'),
    path('logout', views.logout, name='logout'),
    path('profile', views.profile.as_view(), name='profile'),
]
