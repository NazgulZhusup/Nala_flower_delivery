
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('flowers.urls')),  # Включаем URL-ы приложения flowers
    path('accounts/', include('django.contrib.auth.urls')),  # Включение стандартных URL-ов аутентификации
    path('api/', include('flowers.api_urls')),

]

from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)