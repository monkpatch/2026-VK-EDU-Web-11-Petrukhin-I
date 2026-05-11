from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render


TAGS = ["python", "django", "mysql", "black-jack", "bender"]


def make_questions(count=35, tag="black-jack"):
    questions = []
    for i in range(1, count + 1):
        questions.append(
            {
                "id": i,
                "title": f"How to build a moon park #{i}?",
                "text": "Guys, I have trouble with a moon park. Can't find the black-jack...",
                "rating": 40 - i if i <= 20 else i % 11,
                "answers_count": (i * 3) % 9,
                "tags": [tag, "bender"] if tag else ["python", "django"],
                "avatar_seed": i,
            }
        )
    return questions


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get("page", 1)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(1)
    return page


def sidebar_context():
    return {
        "popular_tags": TAGS,
        "best_members": ["Mr. Freeman", "Dr. House", "Bender", "Queen Victoria", "V. Pupkin"],
    }


def render_page(request, template_name, title, auth=True, **context):
    payload = {"page_title": title, "auth": auth, **sidebar_context(), **context}
    return render(request, template_name, payload)


def index(request):
    page = paginate(make_questions(35), request)
    return render_page(request, "pages/index.html", "New Questions", auth=True, page_obj=page)


def hot(request):
    questions = sorted(make_questions(28), key=lambda question: question["rating"], reverse=True)
    page = paginate(questions, request)
    return render_page(request, "pages/hot.html", "Hot Questions", auth=True, page_obj=page)


def tag(request, tag_name):
    page = paginate(make_questions(24, tag=tag_name), request)
    return render_page(request, "pages/tag.html", f"Tag: {tag_name}", auth=False, tag_name=tag_name, page_obj=page)


def question(request, question_id):
    question_data = make_questions(question_id)[question_id - 1]
    answers = [
        {
            "id": i,
            "text": f"Answer #{i}: first of all I would like to thank you for the invitation...",
            "rating": i + 2,
            "avatar_seed": 100 + i,
            "is_correct": i == 1,
        }
        for i in range(1, 4)
    ]
    return render_page(
        request,
        "pages/question.html",
        question_data["title"],
        auth=False,
        question=question_data,
        answers=answers,
    )


def ask(request):
    return render_page(request, "pages/ask.html", "New Question", auth=False)


def login(request):
    return render_page(request, "pages/login.html", "Log In", auth=False)


def signup(request):
    return render_page(request, "pages/signup.html", "Registration", auth=False)


def profile(request):
    return render_page(request, "pages/profile.html", "Settings: Dr. Pepper", auth=True)
