import json
import math

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AnswerForm, QuestionForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag


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


def user_vote_state(value):
    if value == 1:
        return "up"
    if value == -1:
        return "down"
    return "none"


def attach_question_votes(questions, user):
    if not user.is_authenticated:
        for question_obj in questions:
            question_obj.user_vote = "none"
        return
    values = dict(QuestionLike.objects.filter(user=user, question__in=questions).values_list("question_id", "value"))
    for question_obj in questions:
        question_obj.user_vote = user_vote_state(values.get(question_obj.id))


def attach_answer_votes(answers, user):
    if not user.is_authenticated:
        for answer_obj in answers:
            answer_obj.user_vote = "none"
        return
    values = dict(AnswerLike.objects.filter(user=user, answer__in=answers).values_list("answer_id", "value"))
    for answer_obj in answers:
        answer_obj.user_vote = user_vote_state(values.get(answer_obj.id))


def parse_ajax_payload(request):
    try:
        if request.content_type == "application/json":
            return json.loads(request.body.decode("utf-8") or "{}")
        return request.POST
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def json_error(error, status=400):
    return JsonResponse({"error": error}, status=status)


def ajax_auth_error():
    return json_error("auth_required", status=403)


def normalize_vote(value):
    if value == "like":
        return 1
    if value == "dislike":
        return -1
    return None


def apply_vote(request, model, like_model, target_field):
    if request.method != "POST":
        return json_error("method_not_allowed", status=405)
    if not request.user.is_authenticated:
        return ajax_auth_error()
    payload = parse_ajax_payload(request)
    if payload is None:
        return json_error("invalid_json")
    vote_value = normalize_vote(payload.get("type"))
    if vote_value is None:
        return json_error("invalid_vote_type")
    try:
        object_id = int(payload.get("id"))
    except (TypeError, ValueError):
        return json_error("invalid_id")

    with transaction.atomic():
        target = get_object_or_404(model.objects.select_for_update(), id=object_id)
        lookup = {"user": request.user, target_field: target}
        like = like_model.objects.select_for_update().filter(**lookup).first()
        if like and like.value == vote_value:
            return json_error("duplicate_vote", status=400)
        delta = vote_value if like is None else vote_value - like.value
        if like is None:
            like_model.objects.create(value=vote_value, **lookup)
        else:
            like.value = vote_value
            like.save(update_fields=["value"])
        target.rating += delta
        target.save(update_fields=["rating"])
        return JsonResponse({"rating": target.rating, "vote": user_vote_state(vote_value)})


def question_vote(request):
    return apply_vote(request, Question, QuestionLike, "question")


def answer_vote(request):
    return apply_vote(request, Answer, AnswerLike, "answer")


def answer_correct(request):
    if request.method != "POST":
        return json_error("method_not_allowed", status=405)
    if not request.user.is_authenticated:
        return ajax_auth_error()
    payload = parse_ajax_payload(request)
    if payload is None:
        return json_error("invalid_json")
    try:
        question_id = int(payload.get("question_id"))
        answer_id = int(payload.get("answer_id"))
    except (TypeError, ValueError):
        return json_error("invalid_id")

    with transaction.atomic():
        question_obj = get_object_or_404(Question.objects.select_for_update(), id=question_id)
        if question_obj.author_id != request.user.id:
            return json_error("forbidden", status=403)
        answer = get_object_or_404(Answer.objects.select_for_update(), id=answer_id, question=question_obj)
        Answer.objects.filter(question=question_obj, is_correct=True).exclude(id=answer.id).update(is_correct=False)
        if not answer.is_correct:
            answer.is_correct = True
            answer.save(update_fields=["is_correct"])
        return JsonResponse({"answer_id": answer.id, "is_correct": True})


def index(request):
    page_obj = paginate(Question.objects.new(), request)
    attach_question_votes(page_obj.object_list, request.user)
    return render_page(request, "pages/index.html", "New Questions", page_obj=page_obj)


def hot(request):
    page_obj = paginate(Question.objects.hot(), request)
    attach_question_votes(page_obj.object_list, request.user)
    return render_page(request, "pages/hot.html", "Hot Questions", page_obj=page_obj)


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, slug=tag_name)
    page_obj = paginate(Question.objects.by_tag(tag_name), request)
    attach_question_votes(page_obj.object_list, request.user)
    return render_page(request, "pages/tag.html", f"Tag: {tag_obj.name}", tag_name=tag_obj.name, page_obj=page_obj)


def search(request):
    query = request.GET.get("q", "").strip()
    questions = Question.objects.search(query) if query else Question.objects.none()
    page_obj = paginate(questions, request)
    attach_question_votes(page_obj.object_list, request.user)
    return render_page(request, "pages/search.html", "Search", search_query=query, page_obj=page_obj)


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
    attach_question_votes([question_obj], request.user)
    attach_answer_votes(answers_page.object_list, request.user)
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
