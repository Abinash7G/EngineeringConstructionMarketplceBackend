from django.urls import path, include

urlpatterns = [
    path("api/stripe/", include("payments.urls")),
    # Other URL patterns
]