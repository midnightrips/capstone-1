"""Models for capstone."""

import datetime
from flask_sqlalchemy import SQLAlchemy

from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()


class User(db.Model):
    """User."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True) 
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    edited_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    games = db.relationship('Game', backref='user', lazy=True)
    surveys = db.relationship('Survey', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"
    
    def format_timestamp(self, timestamp):
        """Format the timestamp to a more user-friendly format."""
        return timestamp.strftime("%B %d, %Y at %I:%M %p")

    @property
    def formatted_created_at(self):
        return self.format_timestamp(self.created_at)

    @property
    def formatted_edited_at(self):
        return self.format_timestamp(self.edited_at)

    @classmethod
    def register(cls, username, password, email):
        """Register user with hashed password and return user."""
        hashed = bcrypt.generate_password_hash(password)

        hashed_utf8 = hashed.decode('utf8')

        return cls(username=username, password=hashed_utf8, email=email)

    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists and password is correct. Return user if valid; else return False."""

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            return user
        else:
            return False


class Game(db.Model):
    """Game."""

    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_id = db.Column(db.Integer, unique=True, nullable=False)  # API game ID -- should I just make this the primary key?
    title = db.Column(db.Text, nullable=False)
    genre = db.Column(db.Text, nullable=False)
    game_url = db.Column(db.Text, nullable=False)
    played_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="SET NULL"), nullable=True)

    favorited_by = db.relationship('Favorite', backref='game', lazy=True)

    def format_timestamp(self, timestamp):
        """Format the timestamp to a more user-friendly format."""
        return timestamp.strftime("%B %d, %Y at %I:%M %p")

    @property
    def formatted_played_at(self):
        return self.format_timestamp(self.played_at)


class Survey(db.Model):
    """Survey."""

    __tablename__ = "surveys"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stress = db.Column(db.Integer, nullable=False)
    anxiety = db.Column(db.Integer, nullable=False)
    depression = db.Column(db.Integer, nullable=False)
    before_survey = db.Column(db.Boolean, nullable=False, default=False)
    after_survey = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    before_survey_id = db.Column(db.Integer, db.ForeignKey('surveys.id'), nullable=True)  # Self-referential

    # Define the relationship to link the after_survey to a before_survey
    before_survey_ref = db.relationship('Survey', remote_side=[id], backref='after_survey_ref', uselist=False)
    games = db.relationship('Game', backref='surveys', lazy=True)

class Favorite(db.Model):
    """Favorite."""

    __tablename__ = "favorites"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), primary_key=True, nullable=False)


def connect_db(app):
    db.app = app
    db.init_app(app)