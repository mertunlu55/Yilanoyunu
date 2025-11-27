from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),      # ← BU SATIR OLACAK
    path('', include('oyun.urls')),      # ← Bunu zaten index için kullanıyoruz
]
