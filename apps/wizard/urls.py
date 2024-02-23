from django.urls import path

from . import views

urlpatterns = [
    path('schedules/', views.GeneratedTimeTableView.as_view(), name='generated-time-tables'), 
    path('schedules/count/', views.GeneratedTimeTableCountView.as_view(), name='generated-time-tables-count'),
]