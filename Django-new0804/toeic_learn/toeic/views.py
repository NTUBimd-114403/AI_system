import os
import json
import random
from datetime import timedelta
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.contrib.auth import logout
import logging
from django.db import transaction
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from datetime import date
from .forms import RegisterForm
from .models import (
    ReadingPassage, Question, QUESTION_CATEGORY_CHOICES, UserAnswer,
    ExamResult, Exam, ExamQuestion, ExamSession, DailyVocabulary,
    UserVocabularyRecord, ListeningMaterial,PointTransaction,DailyTestRecord,Phrase
)

# 獲取當前使用的使用者模型
User = get_user_model()

logger = logging.getLogger(__name__)

# 定義測驗次數上限和兌換點數
DAILY_MIXED_TEST_LIMIT = 1
DAILY_OTHER_PART_TEST_LIMIT = 3
EXCHANGE_POINTS_FOR_MIXED_TEST = 50
EXCHANGE_POINTS_FOR_OTHER_PART_TEST = 20


logging.basicConfig(level=logging.INFO)
# 將您的主頁視圖函式更新為此
def home(request):
    """
    渲染主頁面，並在頁面上隨機顯示每日片語，同時傳遞用戶資訊。
    """
    username = None
    if request.user.is_authenticated:
        username = request.user.email

    try:
        # 取得所有片語
        all_phrases = list(Phrase.objects.all())

        # 根據今天的日期設定隨機種子，確保每日片語一致
        # 這個方法可以保證在同一天內，使用者每次刷新頁面都看到相同的片語
        today = date.today()
        random.seed(today.day + today.month + today.year)
        
        # 隨機選擇3個片語，如果片語總數少於3個則選擇全部
        if len(all_phrases) >= 3:
            daily_phrases = random.sample(all_phrases, 3)
        else:
            daily_phrases = all_phrases
        
        context = {
            'daily_phrases': daily_phrases,
            'user': request.user,
            'username': username
        }
    except Exception as e:
        context = {
            'error_message': f'無法載入片語：{e}',
            'user': request.user,
            'username': username
        }
        daily_phrases = []

    return render(request, "home.html", context)

def user(request):
    return render(request, 'user.html')

@login_required
def profile_settings(request):
    # 這個視圖只需要渲染模板，不需要額外傳遞資料
    return render(request, 'profile_settings.html')

@login_required
@require_POST
def update_profile(request):
    try:
        data = json.loads(request.body)
        nickname = data.get('nickname', '').strip()
        if not nickname:
            return JsonResponse({'success': False, 'error': '暱稱不能為空。'}, status=400)
            
        request.user.nickname = nickname
        request.user.save()
        messages.success(request, '暱稱更新成功！')
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無效的 JSON 資料。'}, status=400)

@login_required
@require_POST
def change_password(request):
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password')
        new_password1 = data.get('new_password1')
        new_password2 = data.get('new_password2')
        
        # 建立 PasswordChangeForm 實例並傳入資料
        form = PasswordChangeForm(user=request.user, data={
            'old_password': old_password,
            'new_password1': new_password1,
            'new_password2': new_password2,
        })
        
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密碼已成功變更。')
            return JsonResponse({'success': True})
        else:
            errors = [f'{field}: {", ".join(error_list)}' for field, error_list in form.errors.items()]
            return JsonResponse({'success': False, 'error': '; '.join(errors)}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': '無效的 JSON 資料。'}, status=400)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, '請輸入電子郵件和密碼')
            return render(request, 'login.html')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, '登入成功！')
            return redirect('home')
        else:
            messages.error(request, '帳號或密碼錯誤')
            return render(request, 'login.html')

    return render(request, 'login.html')

def logout_view(request):
    """
    自訂的登出視圖，確保清除所有快閃訊息。
    """
    # 使用 Django 內建的登出函數。
    # 這會結束目前的使用者會話。
    logout(request)

    # 明確地從會話中清除所有訊息。
    # 這可以防止舊的訊息出現在下一個頁面。
    storage = messages.get_messages(request)
    storage.used = True 
    
    # 創建一個新的成功訊息，用於登出操作。
    messages.success(request, '您已成功登出！')
    
    # 重新導向到登入頁面。
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '註冊成功！請登入。')
            return redirect('login')
        else:
            messages.error(request, '註冊失敗，請檢查表單內容。')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def test_page(request):
    return render(request, 'test.html')

def reading_test(request):
    # 隨機抽取一篇已審核的文章
    passages = ReadingPassage.objects.filter(is_approved=True)  # 假設有 is_approved 欄位標示審核狀態
    if not passages.exists():
        return render(request, 'reading_test.html', {'error': '目前沒有已審核的文章'})

    passage = random.choice(passages)

    # 取得該文章的所有題目
    questions = Question.objects.filter(passage=passage)

    # 將資料包成 dict 傳給模板
    passage_data = {
        'title': passage.title,
        'content': passage.content,
        'topic': passage.topic,
        'word_count': passage.word_count,
        'reading_level': passage.reading_level,
    }

    # 將題目轉成 list of dict，方便 JS 使用
    questions_data = []
    for q in questions:
        questions_data.append({
            'question_id': q.question_id,
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
        })

    # 把題目序列化成JSON字串，安全傳到模板
    questions_json = json.dumps(questions_data)

    return render(request, 'reading_test.html', {
        'passage': passage_data,
        'questions_json': questions_json,
    })


@csrf_exempt
@require_POST
def submit_test_answer(request):
    """
    接收使用者測驗答案，計算分數並回傳詳細結果與分析。
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        answers = data.get('answers')

        if not session_id or answers is None:
            return JsonResponse({'success': False, 'error': '缺少 session_id 或 answers'})

        try:
            session = ExamSession.objects.get(session_id=session_id)
            user = session.user
        except ExamSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': '找不到考試紀錄'})

        if session.status == 'completed':
            return JsonResponse({'success': False, 'error': '本次測驗已完成，請勿重複提交'})

        answer_time = timezone.now()
        question_details = []

        total_questions = 0
        correct_total = 0
        part_analysis = {}
        category_analysis = {}

        transcripts = {}
        translations = {}
        reading_passages = []
        part3_material_ids = set()
        reading_material_ids = set()

        exam = session.exam
        exam_questions_queryset = ExamQuestion.objects.filter(exam=exam).order_by('question_order').select_related('question__material', 'question__passage')
        answers = answers or {}

        for eq in exam_questions_queryset:
            question = eq.question
            qid = str(question.question_id)
            selected_option = answers.get(qid) 
            if selected_option is None:
                selected_option = ''

            is_correct = False
            if selected_option:
                if selected_option.lower() == question.is_correct.lower():
                    is_correct = True
            
            answer_text = ''
            if selected_option:
                if selected_option.lower() == 'a':
                    answer_text = question.option_a_text
                elif selected_option.lower() == 'b':
                    answer_text = question.option_b_text
                elif selected_option.lower() == 'c':
                    answer_text = question.option_c_text
                elif selected_option.lower() == 'd':
                    answer_text = question.option_d_text

            UserAnswer.objects.create(
                session=session,
                question=question,
                selected_options=selected_option,
                answer_text=answer_text,
                is_correct=is_correct,
                answer_time=answer_time,
            )

            total_questions += 1
            if is_correct:
                correct_total += 1

            part = f'part{question.part}' if question.part else 'unknown_part'
            if part not in part_analysis:
                part_analysis[part] = {'total': 0, 'correct': 0}
            part_analysis[part]['total'] += 1
            if is_correct:
                part_analysis[part]['correct'] += 1

            category = question.question_category or 'unknown_category'
            if category not in category_analysis:
                category_analysis[category] = {'total': 0, 'correct': 0}
            category_analysis[category]['total'] += 1
            if is_correct:
                category_analysis[category]['correct'] += 1

            options = [
                {'value': 'a', 'text': question.option_a_text},
                {'value': 'b', 'text': question.option_b_text},
                {'value': 'c', 'text': question.option_c_text},
                {'value': 'd', 'text': question.option_d_text},
            ]

            if question.material:
                material = question.material
                material_id_str = str(material.material_id)
                
                if part == 'part2':
                    transcripts[qid] = material.transcript
                    translations[qid] = material.translation
                elif part == 'part3' and material_id_str not in part3_material_ids:
                    transcripts[qid] = material.transcript
                    translations[qid] = material.translation
                    part3_material_ids.add(material_id_str)
            
            if question.passage:
                passage = question.passage
                passage_id_str = str(passage.passage_id)
                
                if passage_id_str not in reading_material_ids:
                    reading_passages.append({
                        'id': passage_id_str,
                        'content': passage.content,
                        'translation': passage.translation,
                        'material_part': f'part{question.part}', 
                    })
                    reading_material_ids.add(passage_id_str)

            question_details.append({
                'question_id': qid,
                'question_text': question.question_text,
                'user_answer': selected_option,
                'correct_answer': question.is_correct,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'options': options,
                'part': part,
                'category': question.get_question_category_display() if question.question_category else '未分類',
                'question_order': eq.question_order,
            })

        def calc_score(correct, total):
            return round((correct / total * 100), 2) if total else 0.0

        reading_total = sum(p['total'] for part, p in part_analysis.items() if part in ['part5', 'part6', 'part7'])
        reading_correct = sum(p['correct'] for part, p in part_analysis.items() if part in ['part5', 'part6', 'part7'])
        listen_total = sum(p['total'] for part, p in part_analysis.items() if part in ['part2', 'part3'])
        listen_correct = sum(p['correct'] for part, p in part_analysis.items() if part in ['part2', 'part3'])

        reading_score = calc_score(reading_correct, reading_total)
        listen_score = calc_score(listen_correct, listen_total)
        total_score = calc_score(correct_total, total_questions)

        is_passed = total_score >= float(exam.passing_score)

        # 點數發放邏輯
        points_to_award = 0
        point_reason = ''
        if total_score >= 80:
            points_to_award = 10
            point_reason = 'test_completion'
        elif total_score >= 60:
            points_to_award = 5
            point_reason = 'test_completion'

        with transaction.atomic():
            # 儲存測驗結果
            ExamResult.objects.create(
                session=session,
                total_questions=total_questions,
                correct_answers=correct_total,
                total_score=total_score,
                is_passed=is_passed,
                reading_score=reading_score,
                listen_score=listen_score,
                completed_at=timezone.now(),
            )

            # 更新使用者點數並記錄交易
            if points_to_award > 0:
                user.point += points_to_award
                user.save()

                PointTransaction.objects.create(
                    user=user,
                    change_amount=points_to_award,
                    reason=point_reason
                )
                logger.info(f"User {user.email} awarded {points_to_award} points for test completion. Total points: {user.point}")
            
            # 更新測驗狀態
            session.status = 'completed'
            session.end_time = timezone.now()
            session.save()

        test_type = exam.get_exam_type_display()
        
        response_data = {
            'success': True,
            'data': {
                'score': total_score,
                'correct_answers': correct_total,
                'total_questions': total_questions,
                'is_passed': is_passed,
                'reading_score': reading_score,
                'listen_score': listen_score,
                'question_details': question_details,
                'test_type': test_type,
                'transcripts': transcripts,
                'translations': translations,
                'reading_passages': reading_passages,
                'part_analysis': part_analysis,
                'category_analysis': category_analysis,
                'points_awarded': points_to_award
            }
        }
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Error in submit_test_answer: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

def get_listening_transcript(exam):
    """
    取得聽力測驗的文字稿
    """
    try:
        # 找到考卷中第一個有 ListeningMaterial 的題目，並取出文字稿
        first_listening_question = Question.objects.filter(
            examquestion__exam=exam,
            material__isnull=False
        ).first()

        if first_listening_question and first_listening_question.material:
            transcript = first_listening_question.material.transcript
            print(f"Transcript found: {transcript}")
            return transcript
        else:
            print("No transcript found for this exam")
            return None
    except Exception as e:
        print(f"Error getting transcript: {str(e)}")
        return None


def test_result(request):
    """
    顯示測驗結果頁面，內容不變
    """
    context = {
        'page_title': '測驗結果',
        'test_type': 'reading'
    }
    
    return render(request, 'result.html', context)

def get_daily_record_and_counts(user):
    """
    取得使用者當天的每日測驗紀錄。
    """
    today = timezone.localdate(timezone.now())
    record, created = DailyTestRecord.objects.get_or_create(user=user, date=today)
    return record, record.mixed_test_count, record.other_part_test_count

# 獲取當前台灣日期
def get_taiwan_today():
    """
    取得台灣時區的當天日期，手動計算時差。
    """
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    return taiwan_now.date()

def get_daily_record_and_counts(user):
    """
    取得使用者當天的每日測驗紀錄。
    """
    today = get_taiwan_today()
    record, created = DailyTestRecord.objects.get_or_create(user=user, date=today)
    # 如果是新紀錄，設定預設的測驗次數上限
    if created:
        record.mixed_test_limit = DAILY_MIXED_TEST_LIMIT
        record.other_part_test_limit = DAILY_OTHER_PART_TEST_LIMIT
        record.save()
    return record, record.mixed_test_count, record.other_part_test_count

def check_and_update_test_count(user, part_number):
    """
    檢查並更新當天測驗次數。
    回傳 (is_allowed, message)
    """
    record, mixed_count, other_part_count = get_daily_record_and_counts(user)
    
    if part_number == 0:  # 綜合測驗
        if mixed_count >= record.mixed_test_limit:
            return False, "今日綜合測驗次數已達上限。"
        record.mixed_test_count += 1
    else: # 單一 Part 測驗
        if other_part_count >= record.other_part_test_limit:
            return False, f"今日 Part {part_number} 測驗次數已達上限。"
        record.other_part_test_count += 1
    
    record.save()
    return True, "測驗次數已更新。"

@login_required
@require_POST
def check_test_limit(request):
    """
    檢查使用者當日的測驗次數是否已達上限。
    這個函式不進行測驗，只回傳狀態給前端。
    """
    try:
        data = json.loads(request.body)
        part_number_str = data.get('part_number')
        part_number = int(part_number_str)
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': '無效的請求數據'}, status=400)

    user = request.user
    today = get_taiwan_today()
    record, _ = DailyTestRecord.objects.get_or_create(user=user, date=today)

    if part_number == 0:
        if record.mixed_test_count >= record.mixed_test_limit:
            points_needed = EXCHANGE_POINTS_FOR_MIXED_TEST
            message = f"今日綜合測驗次數已達上限 ({record.mixed_test_limit} 次)。"
            return JsonResponse({'status': 'limit_reached', 'message': message, 'points_needed': points_needed})
    else:
        if record.other_part_test_count >= record.other_part_test_limit:
            points_needed = EXCHANGE_POINTS_FOR_OTHER_PART_TEST
            message = f"今日 Part {part_number} 測驗次數已達上限 ({record.other_part_test_limit} 次)。"
            return JsonResponse({'status': 'limit_reached', 'message': message, 'points_needed': points_needed})

    return JsonResponse({'status': 'ok', 'message': '次數充足'})

@login_required
def all_test(request):
    user = request.user
    is_allowed, message = check_and_update_test_count(user, part_number=0)
    
    if not is_allowed:
        return render(request, 'home.html', {'message': message})
    
    try:
        available_exams = Exam.objects.filter(part=0)
        if not available_exams.exists():
            return render(request, 'home.html', {'message': '找不到綜合測驗。請執行管理指令以建立。'})
        exam = random.choice(available_exams)
    except Exception as e:
        return render(request, 'home.html', {'message': f'發生錯誤：{e}'})

    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=exam.duration_minutes),
        status='in_progress',
    )
    
    exam_questions = ExamQuestion.objects.filter(exam=exam).select_related('question__passage', 'question__material').order_by('question_order')
    
    if not exam_questions.exists():
        return render(request, 'error_page.html', {'message': '綜合測驗沒有題目。'})
    
    questions_data = []
    
    for eq in exam_questions:
        q = eq.question
        
        question_dict = {
            'question_id': str(q.question_id),
            'part': q.part,
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
            'explanation': q.explanation,
            'is_correct': q.is_correct,
            'question_category': q.get_question_category_display()
        }
        
        if q.part in [2, 3] and q.material:
            audio_url = q.material.audio_url
            if audio_url and not audio_url.startswith(('http://', 'https://', '/')):
                audio_url = os.path.join(settings.MEDIA_URL, audio_url)
            
            question_dict['audio_url'] = audio_url
            question_dict['transcript'] = q.material.transcript
            question_dict['material'] = {
                'topic': q.material.topic,
                'accent': q.material.accent,
                'listening_level': q.material.listening_level,
            }
        
        if q.part in [6, 7] and q.passage:
            question_dict['passage_title'] = q.passage.title
            question_dict['passage_content'] = q.passage.content
            question_dict['passage'] = {
                'topic': q.passage.topic,
                'word_count': q.passage.word_count,
                'reading_level': q.passage.reading_level,
            }

        questions_data.append(question_dict)
    
    questions_json = json.dumps(questions_data)
    
    context = {
        'exam_title': exam.title,
        'exam_id': str(exam.exam_id),
        'session_id': str(session.session_id),
        'questions_json': questions_json,
        'duration_minutes': exam.duration_minutes,
    }
    
    return render(request, 'all_test.html', context)

@login_required
def part2(request):
    user = request.user
    part_number = 2
    is_allowed, message = check_and_update_test_count(user, part_number)
    
    if not is_allowed:
        return render(request, 'part2.html', {'error': message})
    
    available_exams = Exam.objects.filter(part=part_number)
    if not available_exams.exists():
        return render(request, 'part2.html', {'error': f'目前沒有 Part {part_number} 的專屬考卷'})
    
    selected_exam = random.choice(available_exams)

    exam_questions = ExamQuestion.objects.filter(
        exam=selected_exam
    ).select_related('question', 'question__material').order_by('question_order')

    questions_data = []
    for eq in exam_questions:
        q = eq.question
        audio_url = None
        if q.material and q.material.audio_url:
            audio_url = os.path.join(settings.MEDIA_URL, q.material.audio_url)

        questions_data.append({
            'question_id': str(q.question_id),
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'difficulty_level': q.difficulty_level,
            'transcript': q.material.transcript if q.material else None,
            'audio_url': audio_url,
        })
    
    if not questions_data:
        return render(request, 'part2.html', {'error': '考卷中未找到對應音檔'})

    questions_json = json.dumps(questions_data)
    
    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=selected_exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=selected_exam.duration_minutes),
        status='in_progress',
    )
    context = {
        'questions_json': questions_json,
        'exam_id': selected_exam.exam_id,
        'session_id': session.session_id,
    }
    return render(request, 'part2.html', context)

@login_required
def part3(request):
    user = request.user
    part_number = 3
    is_allowed, message = check_and_update_test_count(user, part_number)
    
    if not is_allowed:
        return render(request, 'part3.html', {'error': message})
        
    available_exams = Exam.objects.filter(part=part_number)
    if not available_exams.exists():
        return render(request, 'part3.html', {'error': f'目前沒有 Part {part_number} 的專屬考卷'})
    selected_exam = random.choice(available_exams)
    exam_questions = ExamQuestion.objects.filter(exam=selected_exam).select_related('question__material').order_by('question_order')
    
    material = None
    questions_data = []
    for eq in exam_questions:
        q = eq.question
        if not material and q.material:
            material = q.material
        questions_data.append({
            'question_id': str(q.question_id),
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
        })
    if not material:
        return render(request, 'part3.html', {'error': '考卷中未找到對應音檔'})
    audio_url = material.audio_url
    if audio_url and not audio_url.startswith(('http://', 'https://', '/')):
        audio_url = os.path.join(settings.MEDIA_URL, audio_url)
    material_data = {
        'audio_url': audio_url,
        'transcript': material.transcript,
        'topic': material.topic,
        'accent': material.accent,
        'listening_level': material.listening_level,
    }
    questions_json = json.dumps(questions_data)
    
    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=selected_exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=selected_exam.duration_minutes),
        status='in_progress',
    )
    context = {
        'material': material_data,
        'questions_json': questions_json,
        'exam_id': selected_exam.exam_id,
        'session_id': session.session_id,
    }
    return render(request, 'part3.html', context)

@login_required
def part5(request):
    user = request.user
    part_number = 5
    is_allowed, message = check_and_update_test_count(user, part_number)
    
    if not is_allowed:
        return render(request, 'part5.html', {'error': message})
        
    available_exams = Exam.objects.filter(part=part_number)
    if not available_exams.exists():
        return render(request, 'part5.html', {'error': f'目前沒有 Part {part_number} 的專屬考卷'})
    selected_exam = random.choice(available_exams)
    exam_questions = ExamQuestion.objects.filter(exam=selected_exam).select_related('question').order_by('question_order')
    questions_data = []
    for eq in exam_questions:
        q = eq.question
        questions_data.append({
            'question_id': str(q.question_id),
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
        })
    questions_json = json.dumps(questions_data)
    
    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=selected_exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=selected_exam.duration_minutes),
        status='in_progress',
    )
    context = {
        'questions_json': questions_json,
        'exam_id': selected_exam.exam_id,
        'session_id': session.session_id,
    }
    return render(request, 'part5.html', context)

@login_required
def part6(request):
    user = request.user
    part_number = 6
    is_allowed, message = check_and_update_test_count(user, part_number)
    
    if not is_allowed:
        return render(request, 'part6.html', {'error': message})
        
    available_exams = Exam.objects.filter(part=part_number)
    if not available_exams.exists():
        return render(request, 'part6.html', {'error': f'目前沒有 Part {part_number} 的專屬考卷'})
    selected_exam = random.choice(available_exams)
    exam_questions = ExamQuestion.objects.filter(exam=selected_exam).select_related('question').order_by('question_order')
    questions_data = []
    passage = None
    for eq in exam_questions:
        q = eq.question
        if not passage and q.passage:
            passage = q.passage
        questions_data.append({
            'question_id': str(q.question_id),
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
        })
    if not passage:
        return render(request, 'part6.html', {'error': '考卷中未找到對應文章'})
    passage_data = {
        'title': passage.title,
        'content': passage.content,
        'topic': passage.topic,
        'word_count': passage.word_count,
        'reading_level': passage.reading_level,
    }
    questions_json = json.dumps(questions_data)
    
    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=selected_exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=selected_exam.duration_minutes),
        status='in_progress',
    )
    context = {
        'passage': passage_data,
        'questions_json': questions_json,
        'exam_id': selected_exam.exam_id,
        'session_id': session.session_id,
    }
    return render(request, 'part6.html', context)

@login_required
def part7(request):
    user = request.user
    part_number = 7
    is_allowed, message = check_and_update_test_count(user, part_number)
    
    if not is_allowed:
        return render(request, 'part7.html', {'error': message})

    available_exams = Exam.objects.filter(part=part_number)
    if not available_exams.exists():
        return render(request, 'part7.html', {'error': f'目前沒有 Part {part_number} 的專屬考卷'})
    selected_exam = random.choice(available_exams)
    exam_questions = ExamQuestion.objects.filter(exam=selected_exam).select_related('question').order_by('question_order')
    questions_data = []
    passage = None
    for eq in exam_questions:
        q = eq.question
        if not passage and q.passage:
            passage = q.passage
        questions_data.append({
            'question_id': str(q.question_id),
            'question_text': q.question_text,
            'option_a_text': q.option_a_text,
            'option_b_text': q.option_b_text,
            'option_c_text': q.option_c_text,
            'option_d_text': q.option_d_text,
            'difficulty_level': q.difficulty_level,
        })
    if not passage:
        return render(request, 'part7.html', {'error': '考卷中未找到對應文章'})
    passage_data = {
        'title': passage.title,
        'content': passage.content,
        'topic': passage.topic,
        'word_count': passage.word_count,
        'reading_level': passage.reading_level,
    }
    questions_json = json.dumps(questions_data)
    
    # 手動處理時間戳記
    utc_now = datetime.utcnow()
    taiwan_now = utc_now + timedelta(hours=8)
    session = ExamSession.objects.create(
        exam=selected_exam,
        user=user,
        time_limit_enabled=True,
        start_time=taiwan_now,
        end_time=taiwan_now + timedelta(minutes=selected_exam.duration_minutes),
        status='in_progress',
    )
    context = {
        'passage': passage_data,
        'questions_json': questions_json,
        'exam_id': selected_exam.exam_id,
        'session_id': session.session_id,
    }
    return render(request, 'part7.html', context)


@login_required
@transaction.atomic
def exchange_test(request):
    """
    處理使用者兌換額外測驗次數的 View。
    POST 請求需要包含 'exam_type' 參數 ('mixed' 或 'part')。
    """
    user = request.user
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '無效的請求方法'}, status=405)
    
    try:
        data = json.loads(request.body)
        exam_type = data.get('exam_type')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'status': 'error', 'message': '無效的請求數據'}, status=400)
    
    if exam_type not in ['mixed', 'part']:
        return JsonResponse({'status': 'error', 'message': '無效的測驗類型'}, status=400)
    
    if exam_type == 'mixed':
        points_needed = EXCHANGE_POINTS_FOR_MIXED_TEST
    else:
        points_needed = EXCHANGE_POINTS_FOR_OTHER_PART_TEST
    
    if user.point < points_needed:
        return JsonResponse({'status': 'error', 'message': f'您的點數不足，無法兌換。需要 {points_needed} 點。'})
    
    user.point -= points_needed
    user.save()
    
    PointTransaction.objects.create(
        user=user,
        change_amount=-points_needed,
        reason='exam_exchange'
    )
    
    today = get_taiwan_today()
    record, _ = DailyTestRecord.objects.get_or_create(user=user, date=today)

    if exam_type == 'mixed':
        # 新增一次綜合測驗機會
        record.mixed_test_limit += 1 
    else:
        # 新增一次單一 Part 測驗機會
        record.other_part_test_limit += 1 
    
    record.save()
    
    return JsonResponse({'status': 'success', 'message': f'成功兌換 {points_needed} 點，已為您新增一次測驗機會！', 'current_points': user.point})

@csrf_exempt
def update_exam_status(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        new_status = data.get('status')

        try:
            session = ExamSession.objects.get(session_id=session_id)

            # 根據狀態更新欄位
            if new_status == 'in_progress':
                session.status = 'in_progress'
                session.start_time = timezone.now()
            elif new_status == 'completed':
                session.status = 'completed'
                session.end_time = timezone.now()

            session.save()
            return JsonResponse({'success': True})
        except ExamSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Session not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})    


@login_required
def get_points_history(request):
    """
    提供使用者點數變動記錄的 API 接口
    """
    user = request.user
    transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')

    data = [
        {
            'date': transaction.created_at.strftime('%Y-%m-%d %H:%M'),
            'reason': transaction.get_reason_display(),
            'amount': transaction.change_amount
        }
        for transaction in transactions
    ]
    return JsonResponse({'success': True, 'transactions': data})

@login_required
def record(request):
    user = request.user

    # 定義 Part 編號與名稱的映射關係
    part_names = {
        2: "應答問題",
        3: "簡短對話",
        5: "句子填空",
        6: "段落填空",
        7: "閱讀測驗",
    }

    # 歷史測驗紀錄
    exam_results = (
        ExamResult.objects
        .filter(session__user=user)
        .order_by('-completed_at')
        .select_related('session__exam')
    )

    # 設定每頁顯示的筆數
    items_per_page = 10
    paginator = Paginator(exam_results, items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 為每個 ExamResult 物件增加 part_display 屬性
    for result in page_obj:
        result.part_display = result.session.exam.get_part_display()

    # 閱讀作答情況
    reading_total = UserAnswer.objects.filter(session__user=user, question__question_type='reading').count()
    reading_correct = UserAnswer.objects.filter(session__user=user, question__question_type='reading', is_correct=True).count()

    # 聽力作答情況
    listening_total = UserAnswer.objects.filter(session__user=user, question__question_type='listen').count()
    listening_correct = UserAnswer.objects.filter(session__user=user, question__question_type='listen', is_correct=True).count()

    # 計算百分比
    reading_progress = int((reading_correct / reading_total) * 100) if reading_total else 0
    listening_progress = int((listening_correct / listening_total) * 100) if listening_total else 0

    # 總學習時數
    total_answers = UserAnswer.objects.filter(session__user=user).count()
    study_hours = round(total_answers / 60, 1)

    # --- 新增：按 Part 分析作答情況 ---
    part_performance = {}
    part_numbers = [2, 3, 5, 6, 7] # 你們的測驗Part
    
    for part in part_numbers:
        part_answers = UserAnswer.objects.filter(
            session__user=user,
            question__part=part
        )
        total_in_part = part_answers.count()
        correct_in_part = part_answers.filter(is_correct=True).count()
        percentage_in_part = int((correct_in_part / total_in_part) * 100) if total_in_part else 0
        
        # 透過 part_names 字典來取得正確的顯示名稱
        part_display_name = part_names.get(part, f'Part {part}')
        
        if total_in_part > 0: # 只顯示有作答紀錄的 Part
            part_performance[part] = {
                'display_name': part_display_name,
                'total': total_in_part,
                'correct': correct_in_part,
                'percentage': percentage_in_part,
            }
    # --- Part 分析新增結束 ---

    # --- 新增：按題目類別分析作答情況 ---
    category_performance = {}
    category_choices_dict = dict(QUESTION_CATEGORY_CHOICES)

    for category_key, category_display_name in QUESTION_CATEGORY_CHOICES:
        category_answers = UserAnswer.objects.filter(
            session__user=user,
            question__question_category=category_key
        )
        total_in_category = category_answers.count()
        correct_in_category = category_answers.filter(is_correct=True).count()
        percentage_in_category = int((correct_in_category / total_in_category) * 100) if total_in_category else 0
        
        # 只有在有作答紀錄時才加入字典
        if total_in_category > 0:
            category_performance[category_key] = {
                'display_name': category_display_name,
                'total': total_in_category,
                'correct': correct_in_category,
                'percentage': percentage_in_category,
            }
    # --- 類別分析新增結束 ---

    context = {
        'user': user,
        'page_obj': page_obj,
        'reading_progress': reading_progress,
        'listening_progress': listening_progress,
        'study_hours': study_hours,
        'reading_total': reading_total,
        'reading_correct': reading_correct,
        'listening_total': listening_total,
        'listening_correct': listening_correct,
        'category_performance': category_performance,
        'part_performance': part_performance, # <-- 將 Part 分析數據傳遞到模板
        'learning_suggestions': get_learning_suggestions(category_performance),
    }

    return render(request, 'record.html', context)

def get_learning_suggestions(category_performance):
    suggestions = []
    for key, data in category_performance.items():
        if data['percentage'] < 60:
            suggestions.append(f"你在「{data['display_name']}」類別正確率較低，建議多加強相關文法或單字練習。")
        elif data['percentage'] < 80:
            suggestions.append(f"你在「{data['display_name']}」類別有待提升，可複習該類題型的解題技巧。")
    if not suggestions:
        suggestions.append("太棒了！你目前表現穩定，請持續保持並多挑戰進階題目。")
    return suggestions

@login_required
@require_http_methods(["GET"])
def get_daily_vocabulary(request):
    """
    根據使用者的學習興趣推薦單字。
    推薦邏輯：
    1. 優先推薦 1 個「已經看過但未標記為熟悉」的舊單字。
    2. 接著推薦 2 個「從未看過」的新單字。
    使用者每天最多只能領取一次。
    """
    user = request.user
    today_date = timezone.now().date()
    
    already_sent_today = UserVocabularyRecord.objects.filter(
        user=user,
        sent_time__date=today_date
    ).exists()

    if already_sent_today:
        # 如果今天已經有任何單字被發送過，則不發送新單字
        return JsonResponse({'message': '你今天已經領取過單字囉！可至歷史單字區查看單字紀錄', 'words': []})
    
    # 獲取使用者已熟悉的單字 ID
    familiar_words_ids = UserVocabularyRecord.objects.filter(
        user=user,
        is_familiar=True
    ).values_list('word_id', flat=True)

    # 獲取所有已看過但未熟悉的單字 ID (弱點單字)
    weak_words_ids = UserVocabularyRecord.objects.filter(
        user=user,
        is_familiar=False
    ).values_list('word_id', flat=True)
    
    # 獲取使用者設定的學習興趣
    user_interests = user.learning_interests.split(',') if hasattr(user, 'learning_interests') and user.learning_interests else []
    
    # 根據興趣篩選單字
    vocabulary_queryset = DailyVocabulary.objects.all()
    if user_interests:
        vocabulary_queryset = vocabulary_queryset.filter(related_category__in=user_interests)

    # 獲取所有尚未熟悉的單字 ID (包含弱點和從未看過的)，並應用興趣篩選
    all_unfamiliar_words_ids = vocabulary_queryset.exclude(
        id__in=familiar_words_ids
    ).values_list('id', flat=True)

    # 獲取所有從未看過的單字 ID (排除所有已看過的單字)，並應用興趣篩選
    unseen_words_ids = vocabulary_queryset.exclude(
        id__in=familiar_words_ids
    ).exclude(
        id__in=weak_words_ids
    ).values_list('id', flat=True)

    words_to_get_ids = []

    # 1. 優先推薦 1 個舊單字 (弱點單字)，並確保它在興趣範圍內
    weak_words_in_interest = [wid for wid in weak_words_ids if wid in all_unfamiliar_words_ids]
    if weak_words_in_interest:
        weak_word_id = random.choice(weak_words_in_interest)
        words_to_get_ids.append(weak_word_id)

    # 2. 接著推薦 2 個新單字，並確保它在興趣範圍內
    num_new_words = 3 - len(words_to_get_ids)
    if unseen_words_ids and num_new_words > 0:
        new_word_candidates = [wid for wid in unseen_words_ids if wid not in words_to_get_ids]
        num_to_sample = min(len(new_word_candidates), num_new_words)
        words_to_get_ids.extend(random.sample(new_word_candidates, num_to_sample))

    # 如果總數仍不足，則從所有未熟悉的單字中隨機補足
    if len(words_to_get_ids) < 3:
        remaining_slots = 3 - len(words_to_get_ids)
        remaining_candidates = [wid for wid in all_unfamiliar_words_ids if wid not in words_to_get_ids]
        num_to_sample = min(len(remaining_candidates), remaining_slots)
        if remaining_candidates:
            words_to_get_ids.extend(random.sample(remaining_candidates, num_to_sample))
    
    if not words_to_get_ids:
        # 如果使用者已經學完所有該興趣下的單字，或者沒有單字可推薦
        message = '恭喜你！所有單字都已完成學習，或目前沒有符合你興趣的單字了。'
        return JsonResponse({'message': message, 'words': []})
        
    new_words = DailyVocabulary.objects.filter(id__in=words_to_get_ids)

    words_data = []
    for word in new_words:
        # ✅ 使用 update_or_create 確保只在單字第一次被發送時建立新紀錄，
        # 並且 sent_time 會自動設定，之後不會更新。
        UserVocabularyRecord.objects.update_or_create(
            user=user,
            word=word,
            defaults={
                'last_viewed': timezone.now(),
            }
        )
        words_data.append({
            'word_id': word.id,
            'word': word.word,
            'pronunciation': word.pronunciation,
            'part_of_speech': word.part_of_speech,
            'translation': word.translation,
            'example_sentence': word.example_sentence,
            'example_translation': word.example_translation,
            'difficulty_level': word.difficulty_level,
            'related_category': word.related_category,
        })

    return JsonResponse({'message': '這是你今天的單字清單：', 'words': words_data})

@login_required
@require_http_methods(["POST"])
def mark_word_as_familiar(request):
    """
    將指定單字標記為熟悉。
    """
    try:
        data = json.loads(request.body)
        word_id = data.get('word_id')

        if not word_id:
            return JsonResponse({'message': '未提供單字 ID。'}, status=400)

        word = DailyVocabulary.objects.get(id=word_id)
        user = request.user

        record, created = UserVocabularyRecord.objects.update_or_create(
            user=user,
            word=word,
            defaults={'is_familiar': True, 'last_viewed': timezone.now()}
        )
        
        return JsonResponse({'message': f'單字 "{word.word}" 已成功標記為熟悉！'})
    except DailyVocabulary.DoesNotExist:
        return JsonResponse({'message': '找不到該單字。'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'message': '無效的 JSON 格式。'}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'發生錯誤：{e}'}, status=500)


@require_POST
@login_required
def update_learning_interests(request):
    try:
        data = json.loads(request.body)
        interests_string = data.get('interests', '')

        # 取得目前登入的使用者
        user = request.user
        
        # 更新使用者的學習興趣欄位
        user.learning_interests = interests_string
        user.save()

        return JsonResponse({'success': True, 'message': '學習興趣已成功更新！'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': '無效的 JSON 資料。'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新失敗: {str(e)}'}, status=500)

def history_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # 1. 從網址中獲取篩選和搜尋參數
    status = request.GET.get('status', 'all')
    search_term = request.GET.get('search', '')

    # 2. 初始化查詢集合
    user_vocabularies = UserVocabularyRecord.objects.filter(user=request.user)

    # 3. 根據參數進行篩選
    if status == 'familiar':
        user_vocabularies = user_vocabularies.filter(is_familiar=True)
    elif status == 'unfamiliar':
        user_vocabularies = user_vocabularies.filter(is_familiar=False)
    
    context = {
        'vocabularies': user_vocabularies,
        'current_status': status,
        'current_search': search_term,
    }
    return render(request, 'history.html', context)