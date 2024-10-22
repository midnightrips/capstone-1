"""Capstone Application: MentalGaming"""

from flask import Flask, redirect, render_template, flash, session, g
from models import db, connect_db, User
from forms import AddUserForm, LoginForm
from flask_migrate import Migrate
import os
from helpers import do_login, do_logout
from sqlalchemy.exc import IntegrityError

# Import blueprints
from blueprints.users import users_bp
from blueprints.games import games_bp
from blueprints.surveys import surveys_bp

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///capstone-app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "12345"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app_context = app.app_context()
app_context.push()
connect_db(app)
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(users_bp)
app.register_blueprint(games_bp)
app.register_blueprint(surveys_bp)

@app.before_request
def add_user_to_g():
    """If logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


##############################################################################
# Homepage route

@app.route('/')
def homepage():
    """Show homepage with games to play if user; redirect to registration page if not."""

    if not g.user:
        return render_template("home-anon.html")

    return render_template('home.html')

##############################################################################
# User signup/login/logout

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
            user_with_username = User.query.filter_by(username=form.username.data).first()
            user_with_email = User.query.filter_by(email=form.email.data).first()

            if user_with_username:
                flash("Username already taken", 'danger')
            elif user_with_email:
                flash("Email already taken", 'danger')
            else:
                # If username and email are not taken, register the user
                user = User.register(
                    username=form.username.data,
                    password=form.password.data,
                    email=form.email.data,
                )
                db.session.add(user)
                db.session.commit()

                do_login(user)
                return redirect("/")

        except IntegrityError:
            db.session.rollback()
            return render_template('users/register.html', form=form)
        
        finally:
            db.session.close()

        return redirect("/register")

    else:
        return render_template('users/register.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        try:
            user = User.authenticate(form.username.data,
                                     form.password.data)

            if user:
                do_login(user)
                flash(f"Hello, {user.username}!", "success")
                return redirect("/")
            
            flash("Invalid credentials.", 'danger')

        except Exception as e:
            flash("An error occurred during login. Please try again.", 'danger')
            app.logger.error(f"Login error: {e}")

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    try:
        do_logout()
        flash("Logged out successfully!", "success")
    except Exception as e:
        flash("An error occurred while logging out. Please try again.", 'danger')
        app.logger.error(f"Logout error: {e}")

    return redirect('/login')

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

if __name__ == '__main__':
    app.run(debug=True)