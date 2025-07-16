from django.urls import path
from . import views

urlpatterns = [
    path('', views.part_list, name='part_list'),  # 主頁，顯示 Part5-7 按鈕
    path('part/<str:part>/', views.passage_list, name='passage_list'),  # 顯示該 Part 的文章標題
    path('passage/<int:passage_id>/', views.show_passage, name='show_passage'),  # 顯示文章與題目
]
