from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda request: __import__("django.http", fromlist=["JsonResponse"]).JsonResponse({"status": "ok"})),
    path("api/pos/", include("pos_service.pos.urls")),
    path("api/purchases/", include("pos_service.purchases.urls")),
]
