from django.urls import path
from django.conf import settings

from . import views

urlpatterns = [
    path('schedules/', views.GeneratedTimeTableView.as_view(), name='generated-time-tables'), 
    path('schedules/count/', views.GeneratedTimeTableCountView.as_view(), name='generated-time-tables-count'),
]

if settings.DEBUG:
    urlpatterns += [
        path("schedules-test/", views.GeneratedTimeTableTestView.as_view()),
        path("schedules-test/count/", views.GeneratedTimeTableCountTestView.as_view()),
    ]