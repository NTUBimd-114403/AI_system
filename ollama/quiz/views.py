from django.shortcuts import render, get_object_or_404
from .models import ReadingPassage, Question

def part_list(request):
    parts = [
        {'value': 'Part5', 'name': 'Part 5 - 句型填空'},
        {'value': 'Part6', 'name': 'Part 6 - 長篇填空'},
        {'value': 'Part7', 'name': 'Part 7 - 閱讀理解'},
    ]
    return render(request, 'part_list.html', {'parts': parts})

def passage_list(request, part):
    passages = ReadingPassage.objects.filter(part=part).order_by('-id')
    return render(request, 'quiz/passage_list.html', {'part': part, 'passages': passages})

def show_passage(request, passage_id):
    passage = get_object_or_404(ReadingPassage, id=passage_id)
    questions = passage.questions.all().order_by('blank_number')

    # 在每個 question 上加入 options 屬性，方便模板渲染
    for q in questions:
        q.options = [
            ('A', q.option_a),
            ('B', q.option_b),
            ('C', q.option_c),
            ('D', q.option_d),
        ]

    if request.method == 'POST':
        user_answers = {}
        for question in questions:
            ans = request.POST.get(f'q_{question.id}')
            user_answers[question.id] = ans

        total = questions.count()
        correct_count = 0
        detailed_results = []

        for question in questions:
            user_ans = user_answers.get(question.id)
            correct = (user_ans == question.correct_answer)
            if correct:
                correct_count += 1

            detailed_results.append({
                'question': question,
                'user_answer': user_ans,
                'is_correct': correct,
                'options': question.options,  # 傳選項給模板
            })

        context = {
            'passage': passage,
            'results': detailed_results,
            'correct_count': correct_count,
            'total': total,
            'submitted': True,
        }
        return render(request, 'quiz/show_passage.html', context)

    else:
        context = {
            'passage': passage,
            'questions': questions,
            'submitted': False,
        }
        return render(request, 'quiz/show_passage.html', context)
