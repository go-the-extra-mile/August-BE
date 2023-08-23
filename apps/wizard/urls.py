from django.urls import path

from . import views

urlpatterns = [
    path('', views.TestOpenedSectionListView.as_view(), name='test-time-table-detail'),
    path('schedules', views.GeneratedTimeTableView.as_view(), name='generated-time-tables'), 
    path('schedules/count', views.GeneratedTimeTableCountView.as_view(), name='generated-time-tables-count'),
]