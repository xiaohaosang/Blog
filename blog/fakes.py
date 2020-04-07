# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import os
import random

from PIL import Image
from faker import Faker
from flask import current_app
from sqlalchemy.exc import IntegrityError

from blog.extensions import db
from blog.models import Role, User, Article, Tag, Comment, Notification

fake = Faker()


def fake_admin():
    admin_role = Role.query.filter_by(name='Administrator').first()
    admin = User(name='Xiao hao',
                 username='xiaohao',
                 email='xiaohaosang@163.com',
                 bio=fake.sentence(),
                 website='',
                 role_id=admin_role.id,
                 confirmed=True)
    admin.set_password('xiaohaosang')
    notification = Notification(message='Hello, welcome to Blog.', receiver=admin)
    db.session.add(notification)
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for i in range(count):
        user = User(name=fake.name(),
                    confirmed=True,
                    username=fake.user_name(),
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade(),
                    email=fake.email())
        user.set_password('123456')
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.follow(User.query.get(random.randint(1, User.query.count())))
    db.session.commit()


# def fake_category(count=30):
#     category = Category(name='Default')
#     db.session.add(category)
#
#     for i in range(count):
#         category = Category(name=fake.word())
#         db.session.add(category)
#         try:
#             db.session.commit()
#         except IntegrityError:
#             db.session.rollback()
#
#     for user in User.query.all():
#         default_category = Category.query.filter_by(name='Default').first()
#         user.categories.append(default_category)
#         for j in range(random.randint(0, 10)):
#             category = Category.query.get(random.randint(1, Category.query.count()))
#             if category not in user.categories:
#                 user.categories.append(category)
#     db.session.commit()


def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_article(count=100):
    for i in range(count):
        article = Article(
            title=fake.sentence(),
            body=fake.text(2000),
            # category=Category.query.get(random.randint(1, Category.query.count())),
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year()
        )
        for j in range(random.randint(1, 5)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in article.tags:
                article.tags.append(tag)

        db.session.add(article)
    db.session.commit()


def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Article.query.get(random.randint(1, Article.query.count())))
    db.session.commit()


def fake_comment(count=200):
    for i in range(count):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            article=Article.query.get(random.randint(1, Article.query.count()))
        )
        db.session.add(comment)

    salt = int(count * 0.1)
    # replies
    for i in range(salt):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            replied=Comment.query.get(random.randint(1, Comment.query.count())),
            article=Article.query.get(random.randint(1, Article.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

