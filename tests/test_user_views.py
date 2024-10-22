"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_user_views.py

from app import app, CURR_USER_KEY
import os
from unittest import TestCase
from models import db, Game, User, Favorite, Survey
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG_TB_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""
        db.session.rollback()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.register(username="testuser",
                                      email="test@test.com",
                                      password="testuser")
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        db.session.add(self.testuser)
        db.session.commit()

        # Create sample games for the user
        self.game1 = Game(game_id="111", title="Game 1", genre="Genre 1", game_url="http://game1.com", user_id=self.testuser_id)
        self.game2 = Game(game_id="222", title="Game 2", genre="Genre 2", game_url="http://game2.com", user_id=self.testuser_id)

        db.session.add(self.game1)
        db.session.add(self.game2)
        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        res = super().tearDown()
        db.session.rollback()
        return res

    def login(self):
        """Helper function to log in a user."""
        with self.client as c:
            return c.post('/login', data={
                'username': 'testuser',
                'password': 'testuser'
            }, follow_redirects=True)

    def logout(self):
        """Helper function to log out a user."""
        with self.client as c:
            return c.get('/logout', follow_redirects=True)

    def test_show_user_info(self):
        """Test viewing user info page."""
        self.login()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'testuser', resp.data)
            self.assertIn(b'Game 1', resp.data)

    def test_edit_user(self):
        """Test editing user info."""
        self.login()

        with self.client as c:
            resp = c.post(f'/users/{self.testuser_id}/edit', data={
                'username': 'updateduser',
                'password': 'testuser',  # Correct password to authenticate
                'email': 'updated@test.com'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Profile updated!', resp.data)

            # Check if the user info was updated
            user = User.query.get(self.testuser_id)
            self.assertEqual(user.username, 'updateduser')
            self.assertEqual(user.email, 'updated@test.com')

    def test_edit_user_invalid_password(self):
        """Test editing user info with invalid password."""
        self.login()

        with self.client as c:
            resp = c.post(f'/users/{self.testuser_id}/edit', data={
                'username': 'updateduser',
                'password': 'wrongpassword',  # Wrong password should cause failure
                'email': 'updated@test.com'
            }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Invalid credentials.', resp.data)

    def test_delete_user(self):
        """Test deleting a user and setting user_id to NULL in surveys and games."""
        self.login()

        # Create a survey for the user to ensure it gets updated
        survey = Survey(stress=2, anxiety=3, depression=4, user_id=self.testuser_id)
        db.session.add(survey)
        db.session.commit()

        with self.client as c:
            resp = c.post(f'/users/{self.testuser_id}/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'User deleted successfully.', resp.data)

            # Check if the user's games and surveys have their user_id set to NULL
            game = Game.query.get(self.game1.id)
            survey = Survey.query.filter_by(id=survey.id).first()

            self.assertIsNone(game.user_id)
            self.assertIsNone(survey.user_id)

    def test_show_games(self):
        """Test showing all games played by the user."""
        self.login()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}/games')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Game 1', resp.data)
            self.assertIn(b'Game 2', resp.data)

    def test_show_favorites(self):
        """Test showing favorited games."""
        self.login()

        # Add a game to user's favorites
        favorite = Favorite(user_id=self.testuser_id, game_id=self.game1.id)
        db.session.add(favorite)
        db.session.commit()

        with self.client as c:
            resp = c.get('/users/favorites')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Game 1', resp.data)

    def test_access_unauthorized(self):
        """Test unauthorized access to user-specific pages."""
        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')
            self.assertEqual(resp.status_code, 302)

            resp = c.get(f'/users/{self.testuser_id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            resp = c.get(f'/users/{self.testuser_id}/edit')
            self.assertEqual(resp.status_code, 302)

            resp = c.get(f'/users/{self.testuser_id}/games')
            self.assertEqual(resp.status_code, 302)

            resp = c.get('/users/favorites')
            self.assertEqual(resp.status_code, 302)
