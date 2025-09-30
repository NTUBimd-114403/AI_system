from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.conf import settings
from .models import (
    User,
    Question,
    ReadingPassage,
    ListeningMaterial,
    DailyVocabulary,
    UserVocabularyRecord,
    Phrase,
    DailyTestRecord,
    PointTransaction,
    Exam,
    ExamQuestion,
    ExamSession,
    ExamResult,
    UserAnswer,
    REJECTION_REASON_CHOICES
)

# ---- User 管理 ----
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'nickname', 'is_staff', 'point']
    search_fields = ('email',)
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('nickname', 'point', 'learning_interests')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password', 'is_staff', 'is_active')}
        ),
    )

admin.site.register(User, CustomUserAdmin)


# ---- 內聯管理: 測驗題目 ----
class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 1  # 每次新增頁面多顯示一欄
    autocomplete_fields = ['question'] # 啟用題目自動完成搜尋


# ---- 測驗相關管理 ----
@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_type', 'part', 'total_questions', 'is_active', 'created_at')
    list_filter = ('exam_type', 'is_active', 'part')
    search_fields = ('title', 'description')
    inlines = [ExamQuestionInline]  # 在 Exam 頁面內聯顯示 Questions


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'status', 'start_time', 'end_time')
    list_filter = ('status', 'exam__exam_type')
    search_fields = ('user__email', 'exam__title')
    readonly_fields = ('session_id', 'exam', 'user', 'start_time', 'end_time', 'status')


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('session', 'total_score', 'is_passed', 'completed_at')
    list_filter = ('is_passed',)
    search_fields = ('session__user__email', 'session__exam__title')
    readonly_fields = ('result_id', 'session', 'total_questions', 'correct_answers', 'total_score', 'is_passed', 'reading_score', 'listen_score', 'completed_at')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'selected_options', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('session__user__email', 'question__question_text')
    readonly_fields = ('answer_id', 'session', 'question', 'selected_options', 'answer_text', 'is_correct', 'answer_time', 'created_at')


# ---- 內容管理 (文章、聽力、題目) ----
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'part', 'question_type', 'difficulty_level', 'question_category')
    list_filter = ('part', 'question_type', 'difficulty_level', 'question_category')
    search_fields = ('question_text', 'explanation')
    # 使用關聯欄位時，啟用自動完成搜尋，讓管理員更容易找到相關文章或聽力
    autocomplete_fields = ['passage', 'material']


@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    list_display = ('title', 'reading_level', 'topic', 'is_approved', 'rejection_reason', 'created_at')
    list_filter = ('reading_level', 'is_approved')
    search_fields = ('title', 'content')
    list_editable = ('is_approved',)
    # 使用自訂表單來處理 'rejection_reason' 邏輯
    def get_form(self, request, obj=None, **kwargs):
        class ReadingPassageForm(forms.ModelForm):
            class Meta:
                model = ReadingPassage
                fields = '__all__'
                
            def clean(self):
                cleaned_data = super().clean()
                is_approved = cleaned_data.get('is_approved')
                if is_approved:
                    cleaned_data['rejection_reason'] = None
                return cleaned_data
        return ReadingPassageForm


@admin.register(ListeningMaterial)
class ListeningMaterialAdmin(admin.ModelAdmin):
    list_display = ('listening_level', 'topic', 'is_approved', 'rejection_reason', 'created_at')
    list_filter = ('listening_level', 'is_approved')
    search_fields = ('transcript', 'topic')
    list_editable = ('is_approved',)
    # 使用自訂表單來處理 'rejection_reason' 邏輯
    def get_form(self, request, obj=None, **kwargs):
        class ListeningMaterialForm(forms.ModelForm):
            class Meta:
                model = ListeningMaterial
                fields = '__all__'
                
            def clean(self):
                cleaned_data = super().clean()
                if cleaned_data.get('is_approved'):
                    cleaned_data['rejection_reason'] = None
                return cleaned_data
        return ListeningMaterialForm


# ---- 學習紀錄與點數管理 ----
@admin.register(DailyVocabulary)
class DailyVocabularyAdmin(admin.ModelAdmin):
    list_display = ('word', 'translation', 'difficulty_level', 'part_of_speech', 'related_category')
    search_fields = ('word', 'translation')
    list_filter = ('difficulty_level', 'part_of_speech', 'related_category')


@admin.register(UserVocabularyRecord)
class UserVocabularyRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'word', 'is_familiar', 'last_viewed')
    list_filter = ('is_familiar',)
    search_fields = ('user__email', 'word__word')
    readonly_fields = ('user', 'word', 'sent_time') # 這些欄位應該由程式自動產生


@admin.register(DailyTestRecord)
class DailyTestRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mixed_test_count', 'other_part_test_count')
    list_filter = ('date',)
    search_fields = ('user__email',)
    readonly_fields = ('user', 'date', 'mixed_test_count', 'other_part_test_count')


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'change_amount', 'reason', 'created_at')
    list_filter = ('reason',)
    search_fields = ('user__email',)
    readonly_fields = ('id', 'user', 'change_amount', 'reason', 'created_at')


# ---- 片語管理 ----
@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'english_passage', 'chinese_translation')
    list_filter = ('created_at',)