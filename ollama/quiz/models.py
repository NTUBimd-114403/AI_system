from django.db import models
import hashlib

class ReadingPassage(models.Model):
    PART_CHOICES = [
        ('Part5', 'Part 5'),
        ('Part6', 'Part 6'),
        ('Part7', 'Part 7'),
    ]

    title = models.CharField(max_length=255)
    content_with_blanks = models.TextField()
    word_count = models.IntegerField()
    reading_level = models.CharField(max_length=50)
    topic = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    part = models.CharField(max_length=10, choices=PART_CHOICES, default='Part6')

    content_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)  # ✅ 改為非 unique
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.content_hash:
            raw_text = self.content_with_blanks.strip()
            self.content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.part})"


class Question(models.Model):
    passage = models.ForeignKey(ReadingPassage, on_delete=models.CASCADE, related_name='questions')
    blank_number = models.PositiveIntegerField(null=True, blank=True)  # ✅ 適用 Part6，其他可省略
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)
    explanation = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.blank_number or ''} for {self.passage.title}"
