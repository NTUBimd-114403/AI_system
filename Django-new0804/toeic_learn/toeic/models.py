from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.utils import timezone
from django.conf import settings
# ---------- ENUM choices ----------

LISTENING_LEVEL_CHOICES = [
    ('beginner', 'Beginner'),
    ('intermediate', 'Intermediate'),
    ('advanced', 'Advanced'),
]

READING_LEVEL_CHOICES = LISTENING_LEVEL_CHOICES

QUESTION_TYPE_CHOICES = [
    ('reading', 'Reading'),
    # ('vocab', 'Vocabulary'),
    ('listen', 'Listening'),
]

EXAM_TYPE_CHOICES = [
    ('reading', 'Reading'),
    ('listen', 'Listening'),
    ('mixed', 'Mixed'),
]

SESSION_STATUS_CHOICES = [
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('abandoned', 'Abandoned'),
    ('timeout', 'Timeout'),
]

DIFFICULTY_LEVEL_CHOICES = [
    (1, 'Level 1'),
    (2, 'Level 2'),
    (3, 'Level 3'),
    (4, 'Level 4'),
    (5, 'Level 5'),
]

PART_CHOICES = [
    (0, 'All - 綜合測驗'), 
    (2, 'Part 2 - 應答問題'),
    (3, 'Part 3 - 簡短對話'),
    (5, 'Part 5 - 句子填空'),
    (6, 'Part 6 - 段落填空'),
    (7, 'Part 7 - 單篇閱讀'),
]

QUESTION_CATEGORY_CHOICES = [
    ('tense', '時態'),
    ('pos', '詞性'),
    ('syntax', '句型結構'),
    ('vocab', '單字'),
]

REJECTION_REASON_CHOICES = [
    ('format_error', '格式有誤'),
    ('wrong_part', '不符合相對應 Part'),
    ('content_error', '內文有誤'),
    ('question_error', '題目有誤'),
]
ACCENT_CHOICES = [
    ('british', 'British'),
    ('american', 'American'),
    ('australian', 'Australian'),
    ('canadian', 'Canadian'),
]

CATEGORY_CHOICES = [
        ('Business', '商業與職場'),
        ('Technology', '科技與資訊'),
        ('DailyLife', '日常生活'),
        ('Academic', '學術與教育'),
        ('Travel', '旅遊與文化'),
    ]

POINT_REASON_CHOICES = [
    ('exam_exchange', '測驗次數兌換'),
    ('test_completion', '完成測驗'),
    ('other', '其他')
]

# ---------- Custom User Manager ----------

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email 必須提供")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

# ---------- Custom User Model (Email as PK) ----------

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(primary_key=True, unique=True)
    nickname = models.CharField(max_length=50)
    point = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    learning_interests = models.CharField(max_length=255, blank=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# 每日單字資料表
class DailyVocabulary(models.Model):
    word = models.CharField(max_length=100, unique=True, verbose_name="英文單字")
    pronunciation = models.CharField(max_length=100, blank=True, verbose_name="音標")
    part_of_speech = models.CharField(max_length=50, verbose_name="詞性")
    translation = models.CharField(max_length=255, verbose_name="中文翻譯")
    example_sentence = models.TextField(verbose_name="例句")
    example_translation = models.TextField(verbose_name="例句翻譯", blank=True, null=True)
    difficulty_level = models.IntegerField(default=1, verbose_name="難度等級")
    related_category = models.CharField(max_length=100, blank=True, verbose_name="主題類別",choices=CATEGORY_CHOICES,default='DailyLife')

    def __str__(self):
        return self.word

class Phrase(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    english_passage = models.TextField()
    chinese_translation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class UserVocabularyRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="使用者")
    word = models.ForeignKey(DailyVocabulary, on_delete=models.CASCADE, verbose_name="單字")
    is_familiar = models.BooleanField(default=False, verbose_name="是否熟悉")
    last_viewed = models.DateTimeField(auto_now=True, verbose_name="最後檢視時間")
    sent_time = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="單字發送時間")
    
    class Meta:
        unique_together = ('user', 'word')
        verbose_name = "使用者單字紀錄"
        verbose_name_plural = "使用者單字紀錄"

class DailyTestRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="使用者")
    date = models.DateField(default=timezone.now, verbose_name="測驗日期")
    mixed_test_count = models.IntegerField(default=0, verbose_name="綜合測驗次數")
    other_part_test_count = models.IntegerField(default=0, verbose_name="單一Part測驗次數")

    class Meta:
        unique_together = ('user', 'date')
        verbose_name = "每日測驗紀錄"
        verbose_name_plural = "每日測驗紀錄"

    def __str__(self):
        return f"{self.user.email} - {self.date}"

# ---------- Other Models ----------

class PointTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='email')
    change_amount = models.IntegerField()
    reason = models.CharField(max_length=255, choices=POINT_REASON_CHOICES) 
    created_at = models.DateTimeField(auto_now_add=True)


class ListeningMaterial(models.Model):
    material_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_url = models.CharField(max_length=255, null=True, blank=True)
    transcript = models.TextField()
    translation = models.TextField(null=True, blank=True)  # 新增的欄位
    accent = models.CharField(max_length=50, choices=ACCENT_CHOICES, null=True, blank=True)
    topic = models.CharField(max_length=255)
    listening_level = models.CharField(max_length=20, choices=LISTENING_LEVEL_CHOICES)
    is_approved = models.BooleanField(default=False)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReadingPassage(models.Model):
    passage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    translation = models.TextField(null=True, blank=True)
    word_count = models.IntegerField()
    reading_level = models.CharField(max_length=20, choices=READING_LEVEL_CHOICES)
    topic = models.CharField(max_length=255)
    is_approved = models.BooleanField(default=False)
    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)
    rejection_reason = models.CharField(
        max_length=50,
        choices=REJECTION_REASON_CHOICES,
        null=True,
        blank=True
    )
    


class Question(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    passage = models.ForeignKey(ReadingPassage, null=True, blank=True, on_delete=models.SET_NULL)
    material = models.ForeignKey(ListeningMaterial, null=True, blank=True, on_delete=models.SET_NULL)
    part = models.IntegerField(choices=PART_CHOICES, null=True, blank=True)
    question_text = models.TextField()
    option_a_text = models.TextField()
    option_b_text = models.TextField()
    option_c_text = models.TextField()
    option_d_text = models.TextField()
    is_correct = models.CharField(max_length=1)
    difficulty_level = models.IntegerField(choices=DIFFICULTY_LEVEL_CHOICES)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    question_category = models.CharField(
        max_length=10,
        choices=QUESTION_CATEGORY_CHOICES,
        default='vocab',
        verbose_name='分類題目類型'
    )


class Exam(models.Model):
    exam_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    part = models.IntegerField(choices=PART_CHOICES, null=True, blank=True)
    duration_minutes = models.IntegerField()
    total_questions = models.IntegerField()
    passing_score = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 

class ExamSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='email')
    time_limit_enabled = models.BooleanField(default=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=SESSION_STATUS_CHOICES)
    def update_status(self):
        now = timezone.now()

        # 如果狀態已定（完成或放棄），則不處理
        if self.status in ['completed', 'abandoned', 'timeout']:
            return

        # 檢查是否有時間限制
        if self.time_limit_enabled:
            # 有時間限制，但時間已過
            if now > self.end_time:
                self.status = 'timeout'
            # 有時間限制，但時間未過
            else:
                self.status = 'in_progress'
        else:
            # 沒有時間限制，狀態永遠為進行中，除非手動完成
            self.status = 'in_progress'

        self.save()


class ExamResult(models.Model):
    result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(ExamSession, on_delete=models.CASCADE)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField()
    total_score = models.IntegerField()
    is_passed = models.BooleanField()
    reading_score = models.IntegerField()
    listen_score = models.IntegerField()
    completed_at = models.DateTimeField()

class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_order = models.IntegerField()
    scores = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('exam', 'question')


class UserAnswer(models.Model):
    answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.CharField(max_length=10)
    answer_text = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField()
    answer_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
