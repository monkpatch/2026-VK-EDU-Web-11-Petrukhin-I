from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render

from .models import Question, Tag



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
        "popular_tags": Tag.objects.order_by("name")[:20],
        "best_members": [],
    }


def render_page(request, template_name, title, auth=True, **context):
    payload = {"page_title": title, "auth": auth, **sidebar_context(), **context}
    return render(request, template_name, payload)


def index(request):
    return render_page(request, "pages/index.html", "New Questions", auth=True, page_obj=paginate(Question.objects.new(), request))


def hot(request):
    return render_page(request, "pages/hot.html", "Hot Questions", auth=True, page_obj=paginate(Question.objects.hot(), request))


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, slug=tag_name)
    return render_page(request, "pages/tag.html", f"Tag: {tag_obj.name}", auth=False, tag_name=tag_obj.name, page_obj=paginate(Question.objects.by_tag(tag_name), request))


def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.new(), id=question_id)
    answers_page = paginate(question_obj.answers.select_related("author__profile"), request)
    return render_page(request, "pages/question.html", question_obj.title, auth=False, question=question_obj, answers_page=answers_page)


def ask(request):
    return render_page(request, "pages/ask.html", "New Question", auth=False)


def login(request):
    return render_page(request, "pages/login.html", "Log In", auth=False)


def signup(request):
    return render_page(request, "pages/signup.html", "Registration", auth=False)


def profile(request):
    return render_page(request, "pages/profile.html", "Settings: Dr. Pepper", auth=True)
