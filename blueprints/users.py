"""User Routes."""

from flask import Blueprint, render_template, redirect, g, flash
from models import db, User, Game, Survey, Favorite
from forms import EditUserForm
import datetime
from helpers import unauthorized
from sqlalchemy.exc import IntegrityError

users_bp = Blueprint('users', __name__)

@users_bp.route('/users/<int:user_id>')
def show_user(user_id):
    """Show user info."""

    if not g.user:
        unauthorized()
        return redirect('/')

    user = User.query.get_or_404(user_id)
    games = Game.query.filter_by(user_id=user.id).all()

    return render_template('users/user-detail.html', user=user, games=games)

@users_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit user information"""
    form = EditUserForm()

    if not g.user:
        unauthorized()
        return redirect('/')
    
    user = User.query.get_or_404(user_id)
    
    if form.validate_on_submit():
        # Check if the new username or email already exists
        user_with_username = User.query.filter_by(username=form.username.data).first()
        user_with_email = User.query.filter_by(email=form.email.data).first()

        if user_with_username and user_with_username.id != user.id:
            flash("Username already taken", 'danger')
        elif user_with_email and user_with_email.id != user.id:
            flash("Email already taken", 'danger')
        else:
            # Authenticate the user before updating their profile
            authenticated_user = User.authenticate(g.user.username, form.password.data)
            
            if authenticated_user:
                try:
                    user.username = form.username.data
                    user.email = form.email.data
                    user.edited_at = datetime.datetime.now()
                    
                    db.session.commit()
                    flash("Profile updated!", "success")
                    return redirect(f"/users/{user.id}")

                except IntegrityError:
                    db.session.rollback()
                    flash("An error occurred while updating the profile.", 'danger')

            else:
                flash("Invalid credentials.", 'danger')
    
    return render_template('users/edit.html', form=form, user=user)

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete user, set their games and surveys' user_id to NULL, and delete favorites."""

    if not g.user or g.user.id != user_id:
        unauthorized()
        return redirect('/')

    user = User.query.get_or_404(user_id)

    try:
        Survey.query.filter_by(user_id=user_id).update({"user_id": None})
        Game.query.filter_by(user_id=user_id).update({"user_id": None})

        db.session.delete(user)
        db.session.commit()

        flash("User deleted successfully.", "success")
        return redirect("/register")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred", "danger")
        print(e)
        return redirect(f"/users/{user.id}")
    
    finally:
        db.session.close()

@users_bp.route('/users/<int:user_id>/games')
def show_games(user_id):
    """Show all games played by user."""
    
    if not g.user:
        unauthorized()
        return redirect('/')

    user = User.query.get_or_404(user_id)

    games = Game.query.filter_by(user_id=user.id).all()

    return render_template('users/games.html', user=user, games=games)

@users_bp.route('/users/favorites')
def show_favorites():
    """Show games favorited by user."""
    
    if not g.user:
        unauthorized()
        return redirect('/')

    liked_game_ids = db.session.query(Favorite.game_id).filter_by(user_id=g.user.id).all()

    liked_game_ids = [game_id for (game_id,) in liked_game_ids]

    games = Game.query.filter(Game.id.in_(liked_game_ids)).all()

    return render_template('favorites/favorite.html', games=games, favorites=liked_game_ids, user=g.user)