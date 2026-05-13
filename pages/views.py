import math

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AnswerForm, QuestionForm
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


def render_page(request, template_name, title, **context):
    payload = {"page_title": title, **sidebar_context(), **context}
    return render(request, template_name, payload)


def index(request):
    return render_page(request, "pages/index.html", "New Questions", page_obj=paginate(Question.objects.new(), request))


def hot(request):
    return render_page(request, "pages/hot.html", "Hot Questions", page_obj=paginate(Question.objects.hot(), request))


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, slug=tag_name)
    return render_page(request, "pages/tag.html", f"Tag: {tag_obj.name}", tag_name=tag_obj.name, page_obj=paginate(Question.objects.by_tag(tag_name), request))


def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.with_related(), id=question_id)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(author=request.user, question=question_obj)
            answers_before = question_obj.answers.filter(id__lte=answer.id).count()
            page_number = max(1, math.ceil(answers_before / 10))
            return redirect(f"{question_obj.get_absolute_url()}?page={page_number}#answer-{answer.id}")
    else:
        form = AnswerForm()
    answers_page = paginate(question_obj.answers.select_related("author__profile"), request)
    return render_page(
        request,
        "pages/question.html",
        question_obj.title,
        question=question_obj,
        answers_page=answers_page,
        form=form,
    )


@login_required
def ask(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_obj = form.save(author=request.user)
            return redirect(question_obj.get_absolute_url())
    else:
        form = QuestionForm()
    return render_page(request, "pages/ask.html", "New Question", form=form)
