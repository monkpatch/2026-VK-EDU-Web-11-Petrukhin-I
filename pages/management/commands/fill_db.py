import random
from collections import defaultdict

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from pages.models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


BATCH_SIZE = 5000


class Command(BaseCommand):
    help = "Fill DB with demo data: python manage.py fill_db [ratio]"

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int, nargs="?", default=100)

    def handle(self, *args, **options):
        ratio = max(1, options["ratio"])
        fake = Faker("ru_RU")

        users_count = ratio
        tags_count = ratio
        questions_count = ratio * 10
        answers_count = ratio * 100
        likes_count = ratio * 200

        self.stdout.write(self.style.WARNING(f"Start fill_db ratio={ratio}"))

        with transaction.atomic():
            users = self._create_users(fake, users_count)
            self._create_profiles(users)
            tags = self._create_tags(fake, tags_count)
            questions = self._create_questions(fake, users, questions_count)
            self._attach_tags_to_questions(questions, tags)
            answers = self._create_answers(fake, users, questions, answers_count)
            self._create_question_likes(users, questions, likes_count)
            self._create_answer_likes(users, answers, likes_count)

        self.stdout.write(self.style.SUCCESS("fill_db completed"))

    def _create_users(self, fake, count):
        items = []
        for _ in range(count):
            username = f"user_{fake.unique.pystr(min_chars=10, max_chars=10).lower()}"
            items.append(
                User(
                    username=username,
                    email=f"{username}@example.com",
                )
            )
        User.objects.bulk_create(items, batch_size=BATCH_SIZE, ignore_conflicts=True)
        return list(User.objects.order_by("-id")[:count])

    def _create_profiles(self, users):
        profiles = [Profile(user=user) for user in users]
        Profile.objects.bulk_create(profiles, batch_size=BATCH_SIZE, ignore_conflicts=True)

    def _create_tags(self, fake, count):
        tags = []
        for i in range(count):
            name = f"{fake.word()}-{i}"
            tags.append(Tag(name=name, slug=slugify(name)))
        Tag.objects.bulk_create(tags, batch_size=BATCH_SIZE, ignore_conflicts=True)
        return list(Tag.objects.order_by("-id")[:count])

    def _create_questions(self, fake, users, count):
        items = []
        user_ids = [u.id for u in users]
        for _ in range(count):
            items.append(
                Question(
                    title=fake.sentence(nb_words=6),
                    text=fake.paragraph(nb_sentences=4),
                    author_id=random.choice(user_ids),
                    rating=random.randint(-20, 200),
                )
            )
        Question.objects.bulk_create(items, batch_size=BATCH_SIZE)
        return list(Question.objects.order_by("-id")[:count])

    def _attach_tags_to_questions(self, questions, tags):
        through_model = Question.tags.through
        pairs = []
        tag_ids = [t.id for t in tags]
        for question in questions:
            for tag_id in random.sample(tag_ids, k=min(3, len(tag_ids))):
                pairs.append(through_model(question_id=question.id, tag_id=tag_id))
        through_model.objects.bulk_create(pairs, batch_size=BATCH_SIZE, ignore_conflicts=True)

    def _create_answers(self, fake, users, questions, count):
        items = []
        user_ids = [u.id for u in users]
        question_ids = [q.id for q in questions]
        for _ in range(count):
            items.append(
                Answer(
                    question_id=random.choice(question_ids),
                    author_id=random.choice(user_ids),
                    text=fake.paragraph(nb_sentences=3),
                    rating=random.randint(-10, 100),
                    is_correct=False,
                )
            )
        Answer.objects.bulk_create(items, batch_size=BATCH_SIZE)
        return list(Answer.objects.order_by("-id")[:count])

    def _create_question_likes(self, users, questions, count):
        by_question = defaultdict(set)
        user_ids = [u.id for u in users]
        question_ids = [q.id for q in questions]
        likes = []
        attempts = 0
        while len(likes) < count and attempts < count * 5:
            attempts += 1
            user_id = random.choice(user_ids)
            question_id = random.choice(question_ids)
            if user_id in by_question[question_id]:
                continue
            by_question[question_id].add(user_id)
            likes.append(QuestionLike(user_id=user_id, question_id=question_id, value=random.choice([-1, 1])))
        QuestionLike.objects.bulk_create(likes, batch_size=BATCH_SIZE, ignore_conflicts=True)

    def _create_answer_likes(self, users, answers, count):
        by_answer = defaultdict(set)
        user_ids = [u.id for u in users]
        answer_ids = [a.id for a in answers]
        likes = []
        attempts = 0
        while len(likes) < count and attempts < count * 5:
            attempts += 1
            user_id = random.choice(user_ids)
            answer_id = random.choice(answer_ids)
            if user_id in by_answer[answer_id]:
                continue
            by_answer[answer_id].add(user_id)
            likes.append(AnswerLike(user_id=user_id, answer_id=answer_id, value=random.choice([-1, 1])))
        AnswerLike.objects.bulk_create(likes, batch_size=BATCH_SIZE, ignore_conflicts=True)
