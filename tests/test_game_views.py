"""Game View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_game_views.py

import os
import random
import requests
import requests_mock
from unittest import TestCase
from app import app, db, User, Game, Favorite, Survey
from forms import BeforeSurveyForm

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

base_URL = "https://www.freetogame.com/api"

db.create_all()

class GameViewTestCase(TestCase):
    """Test views for game routes."""

    def setUp(self):
        """Create test client and add sample data."""
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        # Create a test user
        self.testuser = User.register(username="testuser",
                                      email="test@test.com",
                                      password="testuser")
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        db.session.add(self.testuser)
        db.session.commit()

        # Add sample game to the database
        game = Game(
            game_id=1234,
            title="Test Game",
            genre="Action",
            game_url="http://testgame.com",
            user_id=self.testuser_id
        )
        db.session.add(game)
        db.session.commit()

        self.game_id = game.id

    def tearDown(self):
        """Clean up fouled transactions."""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_get_random_games_unauthorized(self):
        """Test access to random games page when not logged in."""
        with self.client as c:
            response = c.get('/games')
            self.assertEqual(response.status_code, 302)  # Redirect

            resp = c.get('/games', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_get_random_games_authorized(self):
        """Test access to random games page when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            response = c.get('/games')
            self.assertEqual(response.status_code, 200)  # Should render random games page

            # Mock random sample of three games (simulate API response)
            self.assertIn(b'random-games', response.data)

    def test_show_game_details(self):
        """Test access to game details when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            response = c.get(f'/games/{self.game_id}')
            self.assertEqual(response.status_code, 200)  # Should render game details page
            self.assertIn(b'Test Game', response.data)  # Check for game title

    def test_favorite_game(self):
        """Test favoriting a game when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            # User favorites a game
            response = c.post(f'/games/add-like/{self.game_id}')
            self.assertEqual(response.status_code, 302)  # Redirect to user's games

            # Check if the game is favorited
            favorite = Favorite.query.filter_by(user_id=self.testuser_id, game_id=self.game_id).first()
            self.assertIsNotNone(favorite)

            # Test unfavoriting the game (remove favorite)
            response = c.post(f'/games/add-like/{self.game_id}')
            self.assertEqual(response.status_code, 302)  # Redirect to user's games

            # Check if the favorite is removed
            favorite = Favorite.query.filter_by(user_id=self.testuser_id, game_id=self.game_id).first()
            self.assertIsNone(favorite)

    def test_save_game(self):
        """Test saving a game."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

        # Create a 'before' survey entry before making the request to save the game.
            before_survey = Survey(
                stress=3,
                anxiety=2,
                depression=4,
                before_survey=True,
                after_survey=False,
                user_id=self.testuser_id
            )
            db.session.add(before_survey)
            db.session.commit()

            # Mock the request to the API for game details
            with requests_mock.Mocker() as m:
                m.get(f'{base_URL}/game?id=1234', json={
                    "id": 1234,
                    "title": "Test Game",
                    "genre": "Action",
                    "game_url": "http://testgame.com"
                })

                # Make the POST request to save the game
                response = c.post('/save-game', data={"game_id": 1234})
                self.assertEqual(response.status_code, 302)  # Redirect to /finish

                # Check if the game is saved in the database
                saved_game = Game.query.filter_by(game_id=1234, user_id=self.testuser_id).first()
                self.assertIsNotNone(saved_game)

                self.assertIsNotNone(before_survey)
