"""Survey View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_survey_views.py

import os
from unittest import TestCase
from app import app, db, User, Survey, session
from forms import BeforeSurveyForm, AfterSurveyForm

os.environ['DATABASE_URL'] = "postgresql:///capstone-test"

app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

db.create_all()

class SurveyViewTestCase(TestCase):
    """Test views for survey routes."""

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

    def tearDown(self):
        """Clean up fouled transactions."""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_start_survey_get_unauthorized(self):
        """Test access to 'before' survey (GET) when not logged in."""
        with self.client as c:
            response = c.get('/start')
            self.assertEqual(response.status_code, 302)

            resp = c.get(f'/start', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_start_survey_get_authorized(self):
        """Test access to 'before' survey (GET) when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            response = c.get('/start')
            self.assertEqual(response.status_code, 200)  # Should render survey form
            self.assertIn(b'before-survey', response.data)  # Ensure survey form is present

    def test_start_survey_post_authorized(self):
        """Test form submission for 'before' survey when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            response = c.post('/start', data={
                'stress': 4,
                'anxiety': 3,
                'depression': 5
            })

            self.assertEqual(response.status_code, 302)  # Redirect to /games

            # Check if the survey data is added to the database
            survey = Survey.query.filter_by(user_id=self.testuser_id, before_survey=True).first()
            self.assertIsNotNone(survey)
            self.assertEqual(survey.stress, 4)
            self.assertEqual(survey.anxiety, 3)
            self.assertEqual(survey.depression, 5)

    def test_finish_survey_get_unauthorized(self):
        """Test access to 'after' survey (GET) when not logged in."""
        with self.client as c:
            response = c.get('/finish')
            self.assertEqual(response.status_code, 302)

            resp = c.get(f'/finish', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_finish_survey_get_authorized(self):
        """Test access to 'after' survey (GET) when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            # Add a 'before' survey to the database to simulate previous completion
            before_survey = Survey(
                user_id=self.testuser_id,
                stress=4,
                anxiety=3,
                depression=5,
                before_survey=True,
                after_survey=False
            )
            db.session.add(before_survey)
            db.session.commit()

            response = c.get('/finish')
            self.assertEqual(response.status_code, 200)  # Should render after-survey form
            self.assertIn(b'after-survey', response.data)

    def test_finish_survey_post_authorized(self):
        """Test form submission for 'after' survey when logged in."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['curr_user'] = self.testuser_id

            # Add a 'before' survey to the database to simulate previous completion
            before_survey = Survey(
                user_id=self.testuser_id,
                stress=4,
                anxiety=3,
                depression=5,
                before_survey=True,
                after_survey=False
            )
            db.session.add(before_survey)
            db.session.commit()

            # Simulate session data for the 'before_survey_id'
            with c.session_transaction() as sess:
                sess['before_survey_id'] = before_survey.id

            response = c.post('/finish', data={
                'stress': 3,
                'anxiety': 4,
                'depression': 2
            })

            self.assertEqual(response.status_code, 302)  # Redirect to thank-you

            resp = c.get(f'/thank-you', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # Check if the after-survey data is added to the database
            after_survey = Survey.query.filter_by(user_id=self.testuser_id, after_survey=True).first()
            self.assertIsNotNone(after_survey)
            self.assertEqual(after_survey.stress, 3)
            self.assertEqual(after_survey.anxiety, 4)
            self.assertEqual(after_survey.depression, 2)


