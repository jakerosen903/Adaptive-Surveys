from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.models import db, User, Survey, Question, SurveyResponse, Answer, Insight
from app.services.question_generator import generate_next_question
from app.services.analysis_service import generate_insights
from app.services.response_processor import process_response
from app.constants import MAX_QUESTIONS_PER_SURVEY
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import uuid

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return render_template('register.html')
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('main.dashboard'))
    
    return render_template('register.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    surveys = current_user.surveys.all()
    return render_template('dashboard.html', surveys=surveys)

@main_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_survey():
    if request.method == 'POST':
        title = request.form['title']
        main_question = request.form['main_question']
        
        survey = Survey(
            title=title,
            main_question=main_question,
            user_id=current_user.id
        )
        db.session.add(survey)
        db.session.commit()
        
        flash('Survey created successfully!')
        return redirect(url_for('main.dashboard'))
    
    return render_template('create_survey.html')

@main_bp.route('/survey/<int:survey_id>')
def take_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    # Get or create respondent ID
    respondent_id = session.get('respondent_id')
    if not respondent_id:
        respondent_id = str(uuid.uuid4())
        session['respondent_id'] = respondent_id
    
    # Get or create survey response
    response = SurveyResponse.query.filter_by(
        survey_id=survey_id,
        respondent_id=respondent_id
    ).first()
    
    if not response:
        response = SurveyResponse(
            survey_id=survey_id,
            respondent_id=respondent_id
        )
        db.session.add(response)
        db.session.commit()
    
    # Get the next question
    answered_questions = [a.question for a in response.answers.all()]
    
    if not answered_questions:
        # Generate first question
        question = generate_next_question(survey_id, response.id)
        if not question:
            # Fallback: create a simple first question
            question = Question(
                text=f"What are your initial thoughts about: {survey.main_question}",
                order=1,
                survey_id=survey_id
            )
            db.session.add(question)
            db.session.commit()
    else:
        # Check if we should generate another question
        if len(answered_questions) < MAX_QUESTIONS_PER_SURVEY:
            question = generate_next_question(survey_id, response.id)
            if not question:
                # End survey if no more questions can be generated
                from datetime import datetime
                response.completed_at = datetime.utcnow()
                db.session.commit()
                return render_template('survey_complete.html', survey=survey)
        else:
            question = None
    
    if not question:
        # Survey complete
        from datetime import datetime
        response.completed_at = datetime.utcnow()
        db.session.commit()
        return render_template('survey_complete.html', survey=survey)
    
    return render_template('take_survey.html', survey=survey, question=question, response=response)

@main_bp.route('/insights/<int:survey_id>')
@login_required
def view_insights(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    
    if survey.user_id != current_user.id:
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
    
    # Generate fresh insights
    insights_data = generate_insights(survey_id)
    
    # Debug: Print what was generated
    print(f"Generated insights data: {insights_data}")
    
    # Get insights from database
    insights = survey.insights.all()
    print(f"Insights from database: {[i.text for i in insights]}")
    
    return render_template('insights.html', survey=survey, insights=insights)

@api_bp.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    answer_text = data.get('answer')
    response_id = data.get('response_id')
    
    # Process the answer
    processed_data = process_response(answer_text)
    
    # Save the answer
    answer = Answer(
        text=answer_text,
        processed_data=processed_data,
        question_id=question_id,
        response_id=response_id
    )
    db.session.add(answer)
    db.session.commit()
    
    return jsonify({'success': True})