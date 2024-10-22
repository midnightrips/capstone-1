"""Survey model tests."""

# run these tests like:
#
#    python -m unittest tests/test_survey_model.py


from app import app
import os
import unittest
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Game, Survey

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

db.create_all()

class SurveyModelTestCase(TestCase):
    """Test survey model."""

    def setUp(self):
        """Set up the test client and sample data."""
        self.client = app.test_client()

        db.drop_all()
        db.create_all()

        self.user = User(username='testuser', email='test@test.com', password='testpassword')
        db.session.add(self.user)
        db.session.commit()

        # Sample game
        self.game = Game(game_id=1, title="Sample Game", genre="Puzzle", game_url="http://example.com", user_id=self.user.id)
        db.session.add(self.game)
        db.session.commit()

        # Sample before survey
        self.before_survey = Survey(stress=2, anxiety=3, depression=4, before_survey=True, user_id=self.user.id)
        db.session.add(self.before_survey)
        db.session.commit()

        # Sample after survey
        self.after_survey = Survey(stress=3, anxiety=4, depression=5, after_survey=True, user_id=self.user.id, before_survey_id=self.before_survey.id)
        db.session.add(self.after_survey)
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction."""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_survey_creation(self):
        """Test if a survey is created successfully."""
        survey = Survey.query.first()
        self.assertEqual(survey.stress, 2)
        self.assertEqual(survey.anxiety, 3)
        self.assertEqual(survey.depression, 4)
        self.assertTrue(survey.before_survey)
        self.assertIsNotNone(survey.created_at)

    def test_survey_linked_to_user(self):
        """Test that a survey is correctly associated with a user."""
        survey = Survey.query.first()
        self.assertEqual(survey.user_id, self.user.id)

    def test_survey_linked_to_game(self):
        """Test that a survey is linked to a game."""
        self.before_survey.game_id = self.game.id
        db.session.commit()

        survey = Survey.query.filter_by(id=self.before_survey.id).first()
        self.assertEqual(survey.game_id, self.game.id)

    def test_survey_before_after_relationship(self):
        """Test that the after_survey is linked to the correct before_survey."""
        survey = Survey.query.filter_by(after_survey=True).first()
        self.assertEqual(survey.before_survey_id, self.before_survey.id)

    def test_survey_deletion_sets_user_id_to_null(self):
        """Test that deleting a user doesn't delete the survey and sets user_id to null."""
        db.session.delete(self.user)
        db.session.commit()

        survey = Survey.query.first()
        self.assertIsNone(survey.user_id)
        self.assertEqual(survey.stress, 2)

if __name__ == '__main__':
    unittest.main()