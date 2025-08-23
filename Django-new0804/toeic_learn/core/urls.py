"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from toeic import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("login/", views.login_view, name="login"),
    path("register/",views.register_view, name="register"),
    
    path('test/', views.test_page, name='test'),
    path('reading_test/', views.reading_test, name='reading_test'),
    path('reading_test/<int:passage_id>/', views.reading_test, name='reading_test_detail'),
    # path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("logout/", views.logout_view, name="logout"),
    path('record/', views.record, name='record'),
    path('get-points-history/', views.get_points_history, name='get_points_history'),
    path('api/submit_test_answer/', views.submit_test_answer, name='submit_test_answer'),
    path('test_result/', views.test_result, name='test_result'),
    path('all_test/', views.all_test, name='all_test'),
    path('part2/', views.part2, name='part2'), 
    path('part3/', views.part3, name='part3'),
    path('part5/', views.part5, name='part5'), 
    path('part6/', views.part6, name='part6'),
    path('part7/', views.part7, name='part7'), 
    # path('exam/part/<int:part_number>/', views.exam_part_view, name='exam_part_view'),
    path('api/update_exam_status/', views.update_exam_status, name='update_exam_status'),
    path('api/chatbot/vocabulary/', views.get_daily_vocabulary, name='get_daily_vocabulary'),
    path('api/chatbot/mark-familiar/', views.mark_word_as_familiar, name='mark_word_as_familiar'),
    path('update-interests/', views.update_learning_interests, name='update_interests'),
    path('history/', views.history_view, name='history'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


