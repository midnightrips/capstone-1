"""Game model tests."""

# run these tests like:
#
#    python -m unittest tests/test_game_model.py


from app import app
import os
import unittest
from unittest import TestCase
from sqlalchemy import exc
from datetime import datetime

from models import db, User, Game, Survey, Favorite

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

db.create_all()

class GameModelTestCase(TestCase):
    """Test game model."""

    def setUp(self):
        """Set up the test client and sample data."""
        self.client = app.test_client()

        db.drop_all()
        db.create_all()

        # Sample user
        self.user = User(username='testuser', email='test@test.com', password='testpassword')
        db.session.add(self.user)
        db.session.commit()

        # Sample game
        self.game = Game(game_id=1, title="Sample Game", genre="Puzzle", game_url="http://example.com", user_id=self.user.id)
        db.session.add(self.game)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_game_creation(self):
        """Test if a game is created successfully."""
        game = Game.query.first()
        self.assertEqual(game.title, "Sample Game")
        self.assertEqual(game.genre, "Puzzle")
        self.assertEqual(game.game_url, "http://example.com")
        self.assertIsNotNone(game.played_at)

    def test_game_associated_with_user(self):
        """Test that a game is correctly associated with a user."""
        game = Game.query.first()
        self.assertEqual(game.user_id, self.user.id)

    def test_game_favorited_relationship(self):
        """Test that the game favorited_by relationship works."""
        favorite_games = self.user.favorites
        self.assertEqual(len(favorite_games), 0)

    def test_game_deletion_sets_user_id_to_null(self):
        """Test that deleting a user doesn't delete the game and sets user_id to null."""
        db.session.delete(self.user)
        db.session.commit()

        game = Game.query.first()
        self.assertIsNone(game.user_id)
        self.assertEqual(game.title, "Sample Game")


    
if __name__ == '__main__':
    unittest.main()
