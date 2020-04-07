# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
import os

from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user, logout_user
from sqlalchemy.sql.expression import func

from blog.decorators import confirm_required, permission_required
from blog.extensions import db
from blog.forms.main import TagForm, CommentForm
# from blog.forms.user import ArticleForm
from blog.models import User, Article, Tag, Follow, Comment, Notification, Collect  #Category,
from blog.notifications import push_comment_notification, push_collect_notification
from blog.utils import redirect_back, flash_errors

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['BLOG_ARTICLE_PER_PAGE']
        pagination = Article.query \
            .join(Follow, Follow.followed_id == Article.author_id) \
            .filter(Follow.follower_id == current_user.id) \
            .order_by(Article.timestamp.desc()) \
            .paginate(page, per_page)
        articles = pagination.items
    else:
        pagination = None
        articles = None
    tags = Tag.query.join(Tag.articles).group_by(Tag.id).order_by(func.count(Article.id).desc()).limit(10)
    return render_template('main/index.html', pagination=pagination, articles=articles, tags=tags)


# @main_bp.route('/explore')
# def explore():
#     articles = Article.query.order_by(func.random()).limit(12)
#     return render_template('main/explore.html', articles=articles)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if q == '':
        flash('Enter keyword about article, user or tag.', 'warning')
        return redirect_back()

    category = request.args.get('category', 'article')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_SEARCH_RESULT_PER_PAGE']
    # if category == 'user':
    #     pagination = User.query.whooshee_search(q).paginate(page, per_page)
    # elif category == 'tag':
    #     pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    # else:
    #     pagination = Article.query.whooshee_search(q).paginate(page, per_page)
    # results = pagination.items

    if category == 'user':
        middle_op = User.query.whooshee_search(q)
    elif category == 'tag':
        middle_op = Tag.query.whooshee_search(q)
    else:
        middle_op = Article.query.whooshee_search(q)
    results_all = middle_op.all()
    pagination = middle_op.paginate(page, per_page)
    results = pagination.items

    return render_template('main/search.html', q=q, results_all=results_all, results=results, pagination=pagination, category=category)


@main_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('main/notifications.html', pagination=pagination, notifications=notifications)


@main_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('Notification archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('All notifications archived.', 'success')
    return redirect(url_for('.show_notifications'))


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/article/<int:article_id>')  #methods=['GET', 'POST']
def show_article(article_id):
    article = Article.query.get_or_404(article_id)
    author = article.author
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(article).order_by(Comment.timestamp.desc()).paginate(
        page, per_page)
    last_articles = Article.query.with_parent(author).order_by(Article.timestamp.desc()).limit(10)
    last_comments = Comment.query.join(Article).join(User).filter(User.id == author.id) \
        .order_by(Comment.timestamp.desc()).limit(10)

    comments = pagination.items
    comment_form = CommentForm()
    tag_form = TagForm()
    return render_template('main/article.html', article=article, comment_form=comment_form, tag_form=tag_form,
                           pagination=pagination, comments=comments, last_articles=last_articles,
                           last_comments=last_comments)


@main_bp.route('/comment/<int:comment_id>')
def show_comment(comment_id):
    article = Comment.query.get_or_404(comment_id).article
    return redirect(url_for('.show_article', article_id=article.id) + '#comment-form')


@main_bp.route('/article/n/<int:article_id>')
def article_next(article_id):
    article = Article.query.get_or_404(article_id)
    article_n = Article.query.with_parent(article.author).filter(Article.id < article_id).order_by(Article.id.desc()).first()

    if article_n is None:
        flash('This is already the last one.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))
    return redirect(url_for('.show_article', article_id=article_n.id))


@main_bp.route('/article/p/<int:article_id>')
def article_previous(article_id):
    article = Article.query.get_or_404(article_id)
    article_p = Article.query.with_parent(article.author).filter(Article.id > article_id).order_by(Article.id.asc()).first()

    if article_p is None:
        flash('This is already the first one.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))
    return redirect(url_for('.show_article', article_id=article_p.id))


@main_bp.route('/set-comment/<int:article_id>', methods=['POST'])
@login_required
@confirm_required
def set_comment(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author:
        abort(403)

    if article.can_comment:
        article.can_comment = False
        flash('Comment disabled', 'info')
    else:
        article.can_comment = True
        flash('Comment enabled.', 'info')
    db.session.commit()
    if request.args.get('next'):
        return redirect_back()
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/article/<int:article_id>/comment/new', methods=['POST'])
@login_required
@confirm_required
@permission_required('COMMENT')
def new_comment(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        author = current_user._get_current_object()
        comment = Comment(body=body, author=author, article=article)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.author.receive_comment_notification:
                push_comment_notification(article_id=article.id, receiver=comment.replied.author)
        db.session.add(comment)
        db.session.commit()
        flash('Comment published.', 'success')

        if current_user != article.author and article.author.receive_comment_notification:
            push_comment_notification(article_id, receiver=article.author, page=page)

    flash_errors(form)
    return redirect(url_for('.show_article', article_id=article_id, page=page))


@main_bp.route('/reply/comment/<int:comment_id>')
@login_required
@confirm_required
@permission_required('COMMENT')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(
        url_for('.show_article', article_id=comment.article_id, reply=comment_id,
                author=comment.author.name) + '#comment-form')


@main_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and current_user != comment.article.author \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    if request.args.get('next'):
        return redirect_back()
    return redirect(url_for('.show_article', article_id=comment.article_id))


@main_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@main_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_ARTICLE_PER_PAGE']
    order_rule = 'time'
    pagination = Article.query.with_parent(tag).order_by(Article.timestamp.desc()).paginate(page, per_page)
    articles = pagination.items

    if order == 'by_collects':
        articles.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    # return tag.name
    return render_template('main/tag.html', tag=tag, pagination=pagination, articles=articles, order_rule=order_rule)


@main_bp.route('/article/<int:article_id>/tag/new', methods=['POST'])
@login_required
@confirm_required
def new_tag(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user != article.author and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in article.tags:
                article.tags.append(tag)
                db.session.commit()
        flash('Tag added.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/delete/tag/<int:article_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(article_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    article = Article.query.get_or_404(article_id)
    if current_user != article.author and not current_user.can('MODERATE'):
        abort(403)
    article.tags.remove(tag)
    db.session.commit()

    if not tag.articles:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/collect/<int:article_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(article_id):
    article = Article.query.get_or_404(article_id)
    if current_user.is_collecting(article):
        flash('Already collected.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))

    current_user.collect(article)
    flash('Photo collected.', 'success')
    if current_user != article.author and article.author.receive_collect_notification:
        push_collect_notification(collector=current_user, article_id=article_id, receiver=article.author)
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/uncollect/<int:article_id>', methods=['POST'])
@login_required
def uncollect(article_id):
    article = Article.query.get_or_404(article_id)
    if not current_user.is_collecting(article):
        flash('Not collect yet.', 'info')
        return redirect(url_for('.show_article', article_id=article_id))

    current_user.uncollect(article)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('.show_article', article_id=article_id))


@main_bp.route('/article/<int:article_id>/collectors')
def show_collectors(article_id):
    article = Article.query.get_or_404(article_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_USER_PER_PAGE']
    pagination = Collect.query.with_parent(article).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('main/collectors.html', collects=collects, article=article, pagination=pagination)