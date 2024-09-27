"""Capstone application."""

from flask import Flask, redirect, render_template, flash, session, g, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
import os
from models import db, connect_db, User, Game, Survey, Favorite
from forms import AddUserForm, LoginForm, EditUserForm, BeforeSurveyForm, AfterSurveyForm
from sqlalchemy.exc import IntegrityError
import requests
import random
from flask_migrate import Migrate
import datetime

base_URL = "https://www.freetogame.com/api"
browser_games_URL = "https://www.freetogame.com/api/games?platform=browser"

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql:///capstone-app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

migrate = Migrate(app, db)

app.config['SECRET_KEY'] = "12345"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app_context = app.app_context()
app_context.push()
connect_db(app)
db.drop_all()
db.create_all()

debug = DebugToolbarExtension(app)

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/register', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = AddUserForm()

    if form.validate_on_submit():
        try:
            user = User.register(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/register.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/register.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("Logged out successfully!")
    return redirect('/login')

###################################################################################
# User routes

@app.route('/users/<int:user_id>')
def show_user(user_id):
    """Show user info."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    games = Game.query.filter_by(user_id=user.id).all()

    return render_template('users/user-detail.html', user=user, games=games)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    """Edit user information"""
    form = EditUserForm()

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    
    if form.validate_on_submit():
        user = User.authenticate(g.user.username,
                                 form.password.data)
        
        
        
        if user:
            user.username = form.username.data
            user.email = form.email.data
            user.edited_at = datetime.datetime.now()
            
            db.session.commit()
            flash("Profile updated!", "success")
            return redirect(f"users/{user.id}") # redirecting to users/1/users/1 for some reason...

        flash("Invalid credentials.", 'danger')
    
    return render_template('users/edit.html', form=form, user=user)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete user, set their games and surveys' user_id to NULL, and delete favorites."""

    if not g.user or g.user.id != user_id:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    # Set user_id in Surveys to NULL
    Survey.query.filter_by(user_id=user_id).update({"user_id": None})

    # Set user_id in Games to NULL
    Game.query.filter_by(user_id=user_id).update({"user_id": None})

    # Delete all Favorites related to the user
    Favorite.query.filter_by(user_id=user_id).delete()

    # Now delete the user
    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.", "success")
    return redirect("/register")


@app.route('/users/<int:user_id>/games')
def show_games(user_id):
    """Show all games played by user."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    games = Game.query.filter_by(user_id=user.id).all()

    return render_template('users/games.html', user=user, games=games)

@app.route('/users/favorites')
def show_favorites():
    """Show games favorited by user."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    liked_game_ids = db.session.query(Favorite.game_id).filter_by(user_id=g.user.id).all()

    liked_game_ids = [game_id for (game_id,) in liked_game_ids]

    games = Game.query.filter(Game.id.in_(liked_game_ids)).all()

    return render_template('favorites/favorite.html', games=games, favorites=liked_game_ids, user=g.user)


#################################################################################
# homepage route

@app.route('/')
def homepage():
    """Show homepage with games to play if user; redirect to registration page if not."""

    if not g.user:
        return render_template("home-anon.html")

    return render_template('home.html')

####################################################################################
# Survey routes

@app.route('/start', methods=['GET', 'POST'])
def start():
    """Show 'before' survey and handle form submission."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = BeforeSurveyForm()

    if form.validate_on_submit():
        stress = int(form.stress.data)
        anxiety = int(form.anxiety.data)
        depression = int(form.depression.data)

        before_survey = Survey(
            stress=stress,
            anxiety=anxiety,
            depression=depression,
            before_survey=True,
            after_survey=False,  
            user_id=g.user.id
        )

        db.session.add(before_survey)
        db.session.commit()

        session['before_survey_id'] = before_survey.id

        return redirect("/games")

    return render_template('surveys/before-survey.html', form=form)

@app.route('/finish', methods=['GET', 'POST'])
def finish():
    """Show 'after' survey and handle form submission."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = AfterSurveyForm()

    before_survey = Survey.query.filter_by(user_id=g.user.id, before_survey=True).order_by(Survey.created_at.desc()).first()

    if form.validate_on_submit():
        stress = int(form.stress.data)
        anxiety = int(form.anxiety.data)
        depression = int(form.depression.data)

        after_survey = Survey(
            stress=stress,
            anxiety=anxiety,
            depression=depression,
            before_survey=False,
            after_survey=True,
            before_survey_id=session['before_survey_id'], 
            game_id=before_survey.game_id,
            user_id=g.user.id
        )
        
        db.session.add(after_survey)
        db.session.commit()

        session.pop('before_survey_id')
        return redirect("/thank-you")

    return render_template('surveys/after-survey.html', form=form)

###############################################################################
# game routes

@app.route('/games')
def get_random_games():
    """Get three random games from API and display the options."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    res = requests.get(browser_games_URL)

    if res.status_code == 200:
        games = res.json()

        # Get three random games
        random_games = random.sample(games, 3)

        # Prepare the data for the template
        game_data = [
            {
                "title": game["title"],
                "id": game["id"],
                "description": game["short_description"],
                "genre": game["genre"],
                "url": game["game_url"]
            }
            for game in random_games
        ]

        return render_template('games/random-games.html', games=game_data)

    else:
        return "Failed to retrieve data from the API", 500
    
@app.route('/games/<int:game_id>')
def show_game_details(game_id):
    """Show game information"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    game = Game.query.get_or_404(game_id)

    surveys = Survey.query.filter_by(user_id=g.user.id, game_id=game_id).all()

    return render_template('games/game.html', game=game, user=g.user, surveys=surveys)

@app.route('/games/add-like/<int:game_id>', methods=['POST'])
def favorite_game(game_id):
    """Add or remove a game from user's favorites."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    game = Game.query.get_or_404(game_id)

    # Check if the game is already favorited by the user
    favorite = Favorite.query.filter_by(user_id=g.user.id, game_id=game.id).first()

    if favorite:
        # If it exists, remove it (unfavorite)
        db.session.delete(favorite)
        db.session.commit()
        flash(f"Removed {game.title} from your favorites.", "info")
    else:
        # If it doesn't exist, add it (favorite)
        new_favorite = Favorite(user_id=g.user.id, game_id=game.id)
        db.session.add(new_favorite)
        db.session.commit()
        flash(f"Added {game.title} to your favorites.", "success")

    return redirect(f'/users/{g.user.id}/games')




# @app.route('/games/add-like/<int:game_id>', methods=['POST'])
# def favorite_game(game_id):
#     """Add or remove a game from user's favorites and return JSON."""

#     if not g.user:
#         flash("Access unauthorized.", "danger")
#         return jsonify({"error": "Unauthorized access"}), 401

#     game = Game.query.get_or_404(game_id)

#     # Check if the game is already favorited by the user
#     favorite = Favorite.query.filter_by(user_id=g.user.id, game_id=game.id).first()
#     favorited = False

#     if favorite:
#         # If it exists, remove it (unfavorite)
#         db.session.delete(favorite)
#         db.session.commit()
#         favorited = False
#         flash(f"Removed {game.title} from your favorites.", "info")
#     else:
#         # If it doesn't exist, add it (favorite)
#         new_favorite = Favorite(user_id=g.user.id, game_id=game.id)
#         db.session.add(new_favorite)
#         db.session.commit()
#         favorited = True
#         flash(f"Added {game.title} to your favorites.", "success")

#     return jsonify({
#         "favorited": favorited,
#         "game_id": game.id
#     })





    
@app.route('/save-game', methods=['POST'])
def save_selected_game():
    """Save the game selected to database and open game tab."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    game_id = request.form.get("game_id") # is this line necessary?

    res = requests.get(f"{base_URL}/game?id={game_id}")

    if res.status_code == 200:
        game = res.json()

        # Check if this game has already been saved for this specific user
        existing_game = Game.query.filter_by(game_id=game['id'], user_id=g.user.id).first()

        if not existing_game:
            new_game = Game(
                game_id=game['id'],
                title=game['title'],
                genre=game['genre'],
                game_url=game['game_url'],
                user_id=g.user.id
            )
            db.session.add(new_game)
            db.session.commit()

            before_survey = Survey.query.filter_by(user_id=g.user.id, before_survey=True).order_by(Survey.created_at.desc()).first()
            before_survey.game_id = new_game.id
            db.session.commit()

        flash("Game saved successfully!", "success")
        return redirect('/finish')

    else:
        flash("Failed to retrieve game data.", "danger")
        return redirect('/games')
    


#######################################################
# Thank you route

@app.route('/thank-you')
def show_thanks():
    """Show thank you page."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    after_survey = Survey.query.filter_by(user_id=g.user.id, after_survey=True).order_by(Survey.id.desc()).first()

    # Get the linked before survey
    before_survey = after_survey.before_survey_ref if after_survey else None

    return render_template('thank-you.html', before_survey=before_survey, after_survey=after_survey, user=g.user)

    # recent_before_survey = Survey.query.filter_by(user_id=g.user.id, before_survey=True).order_by(Survey.id.desc()).first()
    # recent_after_survey = Survey.query.filter_by(user_id=g.user.id, after_survey=True).order_by(Survey.id.desc()).first()

    # return render_template('thank-you.html', user=g.user, 
    #                        before_survey=recent_before_survey,
    #                        after_survey=recent_after_survey)


 #################################################
 # Turn off all caching in flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
