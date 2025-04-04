from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    surveys = db.relationship('Survey', backref='creator', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    main_question = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    questions = db.relationship('Question', backref='survey', lazy='dynamic')
    responses = db.relationship('SurveyResponse', backref='survey', lazy='dynamic')

    def __repr__(self):
        return f'<Survey {self.title}>'


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    question_type = db.Column(db.String(50), default='open_ended')  # open_ended, multiple_choice, etc.
    options = db.Column(db.Text)  # JSON encoded options for multiple choice
    order = db.Column(db.Integer)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'))
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def __repr__(self):
        return f'<Question {self.text[:30]}...>'


class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    respondent_id = db.Column(db.String(64))  # Anonymous identifier for respondents
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    answers = db.relationship('Answer', backref='response', lazy='dynamic')

    def __repr__(self):
        return f'<SurveyResponse {self.id}>'


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    processed_data = db.Column(db.Text)  # JSON encoded processed/analyzed data
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    response_id = db.Column(db.Integer, db.ForeignKey('survey_response.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Answer {self.text[:30]}...>'


class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey('survey.id'))
    text = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float)  # 0-1 score of confidence in the insight
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Insight {self.text[:30]}...>'
