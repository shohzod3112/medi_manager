from django.urls import include, path

urlpatterns = [
    path("", include(("users.urls", "users"), namespace="users")),
    path(
        "",
        include(("organizations.urls", "organizations"), namespace="organizations"),
    ),
]
