"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


from app import app
import os
import unittest
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Game, Survey, Favorite

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

db.create_all()

class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        u1 = User.register("test1", "password", "email1@email.com")
        uid1 = 1111
        u1.id = uid1

        db.session.add(u1)
        db.session.commit()

        u1 = User.query.get(uid1)

        self.u1 = u1
        self.uid1 = uid1

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no games & no surveys
        self.assertEqual(len(u.games), 0)
        self.assertEqual(len(u.surveys), 0)

    ####################################
    # registration tests

    def test_user_register_method(self):
        """Test that the register method correctly hashes the password."""
        new_user = User.register(username='newuser', password='newpassword', email='new@test.com')
        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password, 'newpassword')  # Check that password isn't stored as plaintext
        self.assertTrue(user.password.startswith("$2b$"))

    def test_invalid_username_registration(self):
        invalid = User.register("", "password", "email1@email.com")
        uid = 123456789
        invalid.id = uid
        db.session.add(invalid)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_registration(self): ### why is this test failing?
        invalid = User.register("testtest", "password", "")
        uid = 123789
        invalid.id = uid
        db.session.add(invalid)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_registration(self):
        with self.assertRaises(ValueError) as context:
            User.register("testtest", "", "email1@email.com")

    ##################
    # authentication tests

    def test_user_authenticate_success(self):
        """Test that authentication works with the correct password."""
        user = User.authenticate('test1', 'password')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'test1')

    def test_user_password_fail(self):
        """Test that authentication fails with an incorrect password."""
        user = User.authenticate('test1', 'wrongpassword')
        self.assertFalse(user)

    def test_user_username_fail(self):
        """Test that authentication fails with an incorrect username."""
        user = User.authenticate('wrongusername', 'password')
        self.assertFalse(user)

    ###########
    # Game relationship test

    def test_user_games_relationship(self):
        """Test the relationship between user and games."""
        game = Game(game_id=1, title="Test Game", genre="Puzzle", game_url="http://example.com", user_id=self.u1.id)
        db.session.add(game)
        db.session.commit()

        self.assertEqual(len(self.u1.games), 1)
        self.assertEqual(self.u1.games[0].title, "Test Game")

    ##########
    # survey relationship test

    def test_user_surveys_relationship(self):
        """Test the relationship between user and surveys."""
        survey = Survey(stress=2, anxiety=3, depression=4, before_survey=True, user_id=self.u1.id)
        db.session.add(survey)
        db.session.commit()

        self.assertEqual(len(self.u1.surveys), 1)
        self.assertEqual(self.u1.surveys[0].stress, 2)

    #########
    # favorites relationship test

    def test_user_favorites_relationship(self):
        """Test the relationship between user and favorites."""
        game = Game(game_id=1, title="Favorite Game", genre="Puzzle", game_url="http://example.com", user_id=self.u1.id)
        db.session.add(game)
        db.session.commit()

        favorite = Favorite(user_id=self.u1.id, game_id=game.id)
        db.session.add(favorite)
        db.session.commit()

        self.assertEqual(len(self.u1.favorites), 1)
        self.assertEqual(self.u1.favorites[0].game.title, "Favorite Game")

    ###
    # test repr

    def test_user_repr(self):
        """Test the __repr__ method for User."""
        self.assertEqual(repr(self.u1), f"<User #{self.u1.id}: test1, email1@email.com>")

if __name__ == '__main__':
    unittest.main()