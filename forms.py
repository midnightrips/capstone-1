from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, Length

class AddUserForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)]) 
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class EditUserForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired(), Length(min=6, max=20)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])

class BeforeSurveyForm(FlaskForm):
    """'Before' survey form."""

    # Stress levels
    stress = RadioField(
        "How would you rate your stress levels on average?",
        choices=[(str(i), i) for i in range(6)], 
        validators=[DataRequired()]
    )

    # Anxiety levels
    anxiety = RadioField(
        "How would you rate your anxiety level right now? Some anxiety symptoms include excessive worry or restlessness.",
        choices=[(str(i), i) for i in range(6)],  
        validators=[DataRequired()]
    )

    # Depression levels
    depression = RadioField(
        "How would you rate your depression level right now? Some depressive symptoms include persistent sadness or loss of interest.",
        choices=[(str(i), i) for i in range(6)], 
        validators=[DataRequired()]
    )

    submit = SubmitField("Submit Survey")


class AfterSurveyForm(FlaskForm):
    """'After' survey form."""

    # Stress levels
    stress = RadioField(
        "How would you rate your stress levels on average?",
        choices=[(str(i), i) for i in range(6)], 
        validators=[DataRequired()]
    )

    # Anxiety levels
    anxiety = RadioField(
        "How would you rate your anxiety level right now? Some anxiety symptoms include excessive worry or restlessness.",
        choices=[(str(i), i) for i in range(6)],  
        validators=[DataRequired()]
    )

    # Depression levels
    depression = RadioField(
        "How would you rate your depression level right now? Some depressive symptoms include persistent sadness or loss of interest.",
        choices=[(str(i), i) for i in range(6)], 
        validators=[DataRequired()]
    )

    submit = SubmitField("Submit Survey")