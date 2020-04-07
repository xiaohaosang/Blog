# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li <withlihui@gmail.com>
    :license: MIT, see LICENSE for more details.
"""
from flask import render_template, flash, redirect, url_for, current_app, request, Blueprint, abort
from flask_login import login_required, current_user, fresh_login_required, logout_user

from blog.decorators import confirm_required, permission_required
from blog.emails import send_change_email_email
from blog.extensions import db, avatars
from blog.forms.user import EditProfileForm, UploadAvatarForm, CropAvatarForm, ChangeEmailForm, ArticleForm,\
    ChangePasswordForm, NotificationSettingForm, PrivacySettingForm, DeleteAccountForm          # CategoryForm
from blog.models import User, Article, Collect, Comment  # Category
from blog.notifications import push_follow_notification
from blog.settings import Operations
from blog.utils import generate_token, validate_token, redirect_back, flash_errors

user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    '''
    if user == current_user and user.locked:
        flash('Your account is locked.', 'danger')

    if user == current_user and not user.active:
        logout_user()
    '''
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_ARTICLE_PER_PAGE']
    pagination = Article.query.filter(Article.author_id == user.id).order_by(Article.timestamp.desc()).paginate(page, per_page)
    articles = pagination.items
    return render_template('user/index.html', user=user, pagination=pagination, articles=articles)


# @user_bp.route('/<username>/category/<int:category_id>')
# def show_category(username, category_id):
#     user = User.query.filter_by(username=username).first_or_404()
#     '''
#     if user == current_user and user.locked:
#         flash('Your account is locked.', 'danger')
#
#     if user == current_user and not user.active:
#         logout_user()
#     '''
#     category = user.categories.query.filer_by(id=category_id).first_or_404()   #类似User.unfollow方法
#     page = request.args.get('page', 1, type=int)
#     per_page = current_app.config['BLOG_Article_PER_PAGE']
#     pagination = Article.query.filter(Article.author_id == user.id).filter(Article.category_id == category.id).
#     order_by(Article.timestamp.desc()).paginate(page, per_page)
#     # pagination = Article.query.with_parent(category).order_by(Post.timestamp.desc()).paginate(page, per_page)
#     articles = pagination.items
#     return render_template('user/category.html', user=user, category=category, pagination=pagination,
#     articles=articles)
#
#
# @user_bp.route('/<username>/category/manage')
# @login_required
# @confirm_required
# def manage_category(username):
#     user = User.query.filter_by(username=username).first_or_404()
#     if user != current_user:
#         abort(403)
#     return render_template('user/manage_category.html')
#
#
# @user_bp.route('/<username>/category/new', methods=['GET', 'POST'])
# @login_required
# @confirm_required
# def new_category(username):
#     user = User.query.filter_by(username=username).first_or_404()
#     if user != current_user:
#         abort(403)
#     form = CategoryForm()
#     if form.validate_on_submit():
#         name = form.name.data
#         '''
#         category = Category.query.filter_by(name=name).first()
#         if category is None:
#             category = Category(name=name)
#             db.session.add(category)
#             db.session.commit()
#         if category not in user.categories:
#             user.categories.append(category)
#             db.session.commit()
#         '''
#         # 除了category.id=1,其他的category的user都只有一个
#         category = Category(name=name)
#         user.categories.append(category)
#         db.session.add(category)
#         db.session.commit()
#
#         flash('Category created.', 'success')
#         return redirect(url_for('.manage_category'))
#     return render_template('user/new_category.html', form=form)
#
#
# @user_bp.route('/<username>/category/<int:category_id>/edit', methods=['GET', 'POST'])
# @login_required
# @confirm_required
# def edit_category(username, category_id):
#     user = User.query.filter_by(username=username).first_or_404()
#     if user != current_user:
#         abort(403)
#     form = CategoryForm()
#     category = Category.query.get_or_404(category_id)
#     if category.id == 1:
#         flash('You can not edit the default category.', 'warning')
#         return redirect(url_for('user.index'))
#     if form.validate_on_submit():
#         '''
#         user.categories.remove(category)
#         db.session.commit()
#         if not category.users:
#             db.session.delete(category)
#             db.session.commit()
#         '''
#         category.name = form.name.data
#         db.session.commit()
#         flash('Category updated.', 'success')
#         return redirect(url_for('.manage_category'))
#
#     form.name.data = category.name
#     return render_template('user/edit_category.html', form=form)


# @user_bp.route('/<username>/category/<int:category_id>/delete', methods=['POST'])
# @login_required
# @confirm_required
# def delete_category(username, category_id):
#     user = User.query.filter_by(username=username).first_or_404()
#     if user != current_user:
#         abort(403)
#     category = Category.query.get_or_404(category_id)
#     if category.id == 1:
#         flash('You can not delete the default category.', 'warning')
#         return redirect(url_for('blog.index'))
#     category.delete()
#     flash('Category deleted.', 'success')
#     return redirect(url_for('.manage_category'))


@user_bp.route('/<username>/article/manage')
@login_required
@confirm_required
def manage_article(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_ARTICLE_PER_PAGE']
    pagination = Article.query.filter(Article.author_id == user.id).order_by(Article.timestamp.desc()).paginate(page, per_page)
    articles = pagination.items
    return render_template('user/manage_article.html', page=page, pagination=pagination, articles=articles)


@user_bp.route('/<username>/comment/manage')
@login_required
@confirm_required
def manage_comment(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_COMMENT_PER_PAGE']
    pagination = Comment.query.filter(Comment.author_id == user.id).order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
    comments = pagination.items
    return render_template('user/manage_comment.html', page=page, comments=comments, pagination=pagination)


@user_bp.route('/<username>/article/new', methods=['GET', 'POST'])
@login_required
@confirm_required
def new_article(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)

    form = ArticleForm()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        # category = Category.query.get(form.category.data)  #form.category.data是id？
        article = Article(title=title, body=body, author=current_user._get_current_object())

        # same with:
        # category_id = form.category.data
        # post = Post(title=title, body=body, category_id=category_id,author_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        flash('Post created.', 'success')
        return redirect(url_for('main.show_article', article_id=article.id))
    return render_template('user/new_article.html', form=form)


@user_bp.route('/<username>/article/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
@confirm_required
def edit_article(username, article_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)

    form = ArticleForm()
    article = Article.query.get_or_404(article_id)
    if form.validate_on_submit():
        article.title = form.title.data
        article.body = form.body.data
        # article.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('Article updated.', 'success')
        return redirect(url_for('main.show_article', article_id=article.id))
    form.title.data = article.title
    form.body.data = article.body
    # form.category.data = article.category_id
    return render_template('user/edit_article.html', form=form)


@user_bp.route('/<username>/article/<int:article_id>/delete', methods=['POST'])
@login_required
@confirm_required
def delete_article(username, article_id):
    user = User.query.filter_by(username=username).first_or_404()
    if user != current_user:
        abort(403)

    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'success')
    return redirect_back()


@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_ARTICLE_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)



@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('Already followed.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.follow(user)
    flash('User followed.', 'success')
    if user.receive_follow_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('Not follow yet.', 'info')
        return redirect(url_for('.index', username=username))

    current_user.unfollow(user)
    flash('User unfollowed.', 'info')
    return redirect_back()


@user_bp.route('/<username>/followers')
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/<username>/following')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLOG_USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    form.website.data = current_user.website
    form.location.data = current_user.location
    return render_template('user/settings/edit_profile.html', form=form)


@user_bp.route('/settings/avatar')
@login_required
@confirm_required
def change_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form, crop_form=crop_form)


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('Image uploaded, please crop.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
@confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        db.session.commit()
        flash('Avatar updated.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/change-password', methods=['GET', 'POST'])
@fresh_login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.validate_password(form.old_password.data):
            current_user.set_password(form.password.data)
            db.session.commit()
            flash('Password updated.', 'success')
            return redirect(url_for('.index', username=current_user.username))
        else:
            flash('Old password is incorrect.', 'warning')
    return render_template('user/settings/change_password.html', form=form)


@user_bp.route('/settings/change-email', methods=['GET', 'POST'])
@fresh_login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operations.CHANGE_EMAIL, new_email=form.email.data.lower())
        send_change_email_email(to=form.email.data, user=current_user, token=token)
        flash('Confirm email sent, check your inbox.', 'info')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_email.html', form=form)


@user_bp.route('/change-email/<token>')
@login_required
def change_email(token):
    if validate_token(user=current_user, token=token, operation=Operations.CHANGE_EMAIL):
        flash('Email updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    else:
        flash('Invalid or expired token.', 'warning')
        return redirect(url_for('.change_email_request'))


@user_bp.route('/settings/notification', methods=['GET', 'POST'])
@login_required
def notification_setting():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        current_user.receive_collect_notification = form.receive_collect_notification.data
        current_user.receive_comment_notification = form.receive_comment_notification.data
        current_user.receive_follow_notification = form.receive_follow_notification.data
        db.session.commit()
        flash('Notification settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.receive_collect_notification.data = current_user.receive_collect_notification
    form.receive_comment_notification.data = current_user.receive_comment_notification
    form.receive_follow_notification.data = current_user.receive_follow_notification
    return render_template('user/settings/edit_notification.html', form=form)


@user_bp.route('/settings/privacy', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        current_user.public_collections = form.public_collections.data
        db.session.commit()
        flash('Privacy settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.public_collections.data = current_user.public_collections
    return render_template('user/settings/edit_privacy.html', form=form)


@user_bp.route('/settings/account/delete', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('Your are free, goodbye!', 'success')
        return redirect(url_for('main.index'))
    return render_template('user/settings/delete_account.html', form=form)
