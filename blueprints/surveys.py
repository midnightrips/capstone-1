"""Survey routes."""

from flask import Blueprint, render_template, redirect, session, g
from models import db, Survey
from forms import BeforeSurveyForm, AfterSurveyForm
from helpers import unauthorized

surveys_bp = Blueprint('surveys', __name__)

@surveys_bp.route('/surveys/start', methods=['GET', 'POST'])
def start():
    """Show 'before' survey and handle form submission."""

    if not g.user:
        unauthorized()
        return redirect('/')
    
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

@surveys_bp.route('/surveys/finish', methods=['GET', 'POST'])
def finish():
    """Show 'after' survey and handle form submission."""
    
    if not g.user:
        unauthorized()
        return redirect('/')
    
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
        return redirect("/surveys/thank-you")

    return render_template('surveys/after-survey.html', form=form)

@surveys_bp.route('/surveys/thank-you')
def show_thanks():
    """Show thank you page after survey completion."""
    if not g.user:
        unauthorized()
        return redirect('/')

    after_survey = Survey.query.filter_by(user_id=g.user.id, after_survey=True).order_by(Survey.id.desc()).first()
    before_survey = after_survey.before_survey_ref if after_survey else None

    return render_template('thank-you.html', before_survey=before_survey, after_survey=after_survey, user=g.user)