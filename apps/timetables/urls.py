from django.urls import path

from apps.timetables import views

urlpatterns = [
    path("<int:semester>/", views.TimeTableListView.as_view(), name="timetables-list"),
    path(
        "<int:semester>/<int:order>/",
        views.TimeTableView.as_view(),
        name="timetables-detail",
    ),
    path(
        "<int:semester>/<int:order>/sections/",
        views.TimeTableSectionAddView.as_view(),
        name="timetables-sections",
    ),
    path(
        "<int:semester>/<int:order>/sections/<int:section_id>/",
        views.TimeTableSectionDeleteView.as_view(),
        name="timetables-sections-delete",
    )
]
