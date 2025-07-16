from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.html import format_html
from .models import ReadingPassage
from .llm_utils import (
    generate_part5_questions,
    generate_part6_questions,
    generate_part7_questions,
)

@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    list_display = ('title', 'part', 'created_at', 'generate_button')
    list_filter = ('part',)
    ordering = ('-created_at',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate_part5/', self.admin_site.admin_view(self.generate_part5), name='quiz_readingpassage_generate_part5'),
            path('generate_part6/', self.admin_site.admin_view(self.generate_part6), name='quiz_readingpassage_generate_part6'),
            path('generate_part7/', self.admin_site.admin_view(self.generate_part7), name='quiz_readingpassage_generate_part7'),
        ]
        return custom_urls + urls

    def generate_part5(self, request):
        try:
            success = generate_part5_questions(debug=True, max_retries=5)
            if success:
                self.message_user(request, "✅ 成功生成 Part 5 題目")
            else:
                self.message_user(request, "❌ 生成 Part 5 失敗或內容重複", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"❌ 發生錯誤：{e}", level=messages.ERROR)
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def generate_part6(self, request):
        try:
            success = generate_part6_questions(debug=True, max_retries=5)
            if success:
                self.message_user(request, "✅ 成功生成 Part 6 題目")
            else:
                self.message_user(request, "❌ 生成 Part 6 失敗或內容重複", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"❌ 發生錯誤：{e}", level=messages.ERROR)
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def generate_part7(self, request):
        try:
            success = generate_part7_questions(debug=True, max_retries=5)
            if success:
                self.message_user(request, "✅ 成功生成 Part 7 題目")
            else:
                self.message_user(request, "❌ 生成 Part 7 失敗或內容重複", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"❌ 發生錯誤：{e}", level=messages.ERROR)
        return redirect(request.META.get('HTTP_REFERER', '..'))

    def generate_button(self, obj):
        if obj.part == 'Part5':
            url = reverse('admin:quiz_readingpassage_generate_part5')
            return format_html('<a class="button" href="{}" style="margin:0 5px;">➕ 產生 Part 5</a>', url)
        elif obj.part == 'Part6':
            url = reverse('admin:quiz_readingpassage_generate_part6')
            return format_html('<a class="button" href="{}" style="margin:0 5px;">➕ 產生 Part 6</a>', url)
        elif obj.part == 'Part7':
            url = reverse('admin:quiz_readingpassage_generate_part7')
            return format_html('<a class="button" href="{}" style="margin:0 5px;">➕ 產生 Part 7</a>', url)
        return "-"
    generate_button.short_description = "產生題目"
