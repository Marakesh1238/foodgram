from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from foodgram import settings
from .views import docks

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', docks, name='docs'),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
