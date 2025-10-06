from django.contrib import admin
from django.urls import path
from toeic import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ---------- 首頁與帳號相關 ----------
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path('profile-settings/', views.profile_settings, name='profile-settings'),
    path('update-profile/', views.update_profile, name='update-profile'),
    path('change-password/', views.change_password, name='change-password'),

    # ---------- 密碼重置 ----------

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

    # ---------- 測驗相關 ----------
    path("test/", views.test_page, name="test"),

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

    # ---------- 單字學習與 AI 功能 ----------
    path('api/chatbot/vocabulary/', views.get_daily_vocabulary, name='get_daily_vocabulary'),
    path('api/chatbot/mark-familiar/', views.mark_word_as_familiar, name='mark_word_as_familiar'),
    path('update-interests/', views.update_learning_interests, name='update_interests'),
    path('relation-map/', views.relation_map_view, name='relation_map'),
    path('relation-map/<str:word>/', views.relation_map_view, name='relation_map_with_word'),
    path('api/get_word_relations/<str:word>/', views.get_word_relations_by_ai, name='get_word_relations'),

    # ---------- 其他 API ----------
    path('api/update_exam_status/', views.update_exam_status, name='update_exam_status'),

    # ---------- 其他頁面 ----------
    path('faq/', views.faq, name='faq'),
    path('history/', views.history_view, name='history'),

    # ---------- Django Admin ----------
    path("admin/", admin.site.urls),
    
    # ---------- Admin Backend ---------
    path("mgmt-test/", views.get_mgmt_test, name="mgmt_test"),
    path("mgmt-login/", views.mgmt_login, name="mgmt_login"),
    path("mgmt-home/", views.get_mgmt_home, name="mgmt_home"),
    path("mgmt-user/", views.mgmt_user, name="mgmt_user"),
    path('mgmt-point/', views.point_list, name='point_list'),
    path('mgmt-question/', views.question_list, name='question_list'),
    path('mgmt-dashboard/', views.dashboard_view, name='dashboard'),
    
    # ------- Admin API Endpoint -------
    path('mgmt/api/user/update/', views.update_user_api, name='update_user_api'),
    path('mgmt/api/user/create/', views.create_user_api, name='create_user_api'),
    path('mgmt/api/user/delete/', views.delete_user_api, name='delete_user_api'),
    path('mgmt/api/user/<str:email>/', views.get_user_api, name='get_user_api'),
    path('mgmt/api/point/create/', views.point_create, name='point_create'),
    path('mgmt/api/point/delete/', views.point_delete, name='point_delete'),
    path('mgmt/api/point/export/', views.point_export, name='point_export'),
    path('mgmt/api/point/<uuid:transaction_id>/', views.point_detail, name='point_detail'),
    path('mgmt/api/question/create/', views.question_create, name='question_create'),
    path('mgmt/api/question/update/', views.question_update, name='question_update'),
    path('mgmt/api/question/delete/', views.question_delete, name='question_delete'),
    path('mgmt/api/question/export/', views.question_export, name='question_export'),
    path('mgmt/api/question/import/', views.question_import, name='question_import'),
    path('mgmt/api/question/<uuid:question_id>/', views.question_detail, name='question_detail'),
    path('mgmt/api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

