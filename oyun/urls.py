from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # API endpoint'ler
    path("api/score/submit/", views.submit_score, name="submit_score"),
    path("api/score/top/", views.top_scores, name="top_scores"),
    path("api/auth/register/", views.register_user, name="register_user"),
    path("api/auth/login/", views.login_user, name="login_user"),
]
