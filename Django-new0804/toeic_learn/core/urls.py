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
from django.urls import path,include
from toeic import views
from django.contrib.auth import views as auth_views # 引入 Django 認證視圖
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path("login/", views.login_view, name="login"),
    path("register/",views.register_view, name="register"),
    path('profile-settings/', views.profile_settings, name='profile-settings'),
    path('update-profile/', views.update_profile, name='update-profile'), # 確保此行存在
    path('change-password/', views.change_password, name='change-password'),
    # path('accounts/', include('django.contrib.auth.urls')), # 註解此行以避免衝突
    
    # 增加密碼重設流程的 URL
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset_form.html',
        email_template_name='password_reset_email.html',
        subject_template_name='password_reset_subject.txt',
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ), name='password_reset_complete'),

    path('test/', views.test_page, name='test'),
    path('reading_test/', views.reading_test, name='reading_test'),
    path('reading_test/<int:passage_id>/', views.reading_test, name='reading_test_detail'),
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
    path('check-test-limit/', views.check_test_limit, name='check_test_limit'),
    path('exchange-test/', views.exchange_test, name='exchange_test'),
    path('faq/', views.faq, name='faq'),
    path('relation-map/', views.relation_map_view, name='relation_map'),
    path('relation-map/<str:word>/', views.relation_map_view, name='relation_map_with_word'),
    path('api/get_word_relations/<str:word>/', views.get_word_relations_by_ai, name='get_word_relations'),
    # path('exam/part/<int:part_number>/', views.exam_part_view, name='exam_part_view'),
    path('api/update_exam_status/', views.update_exam_status, name='update_exam_status'),
    path('api/chatbot/vocabulary/', views.get_daily_vocabulary, name='get_daily_vocabulary'),
    path('api/chatbot/mark-familiar/', views.mark_word_as_familiar, name='mark_word_as_familiar'),
    path('update-interests/', views.update_learning_interests, name='update_interests'),
    path('history/', views.history_view, name='history'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
