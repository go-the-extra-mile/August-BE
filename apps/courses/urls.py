from django.urls import include, path

from apps.courses import views

app_name = "courses"

urlpatterns = [
    path(
        "",
        views.OpenedSectionByCourseByInstructorListView.as_view(),
        name="opened-section-list",
    ),
]
