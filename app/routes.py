from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models import db, User, Survey, Question, SurveyResponse, Answer, Insight
from app.services.question_generator import generate_next_question
from app.services.analysis_service import generate_insights
from app.services.response_processor import process_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)



# Login roots
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])
        user = User(username=request.form['username'], email=request.form['email'], password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html')

# Web routes
@main_bp.route('/')
def index():
    return render_template('base.html')


@main_bp.route('/dashboard')
def dashboard():
    surveys = Survey.query.all()
    return render_template('dashboard.html', surveys=surveys)


@main_bp.route('/survey/create', methods=['GET', 'POST'])
def create_survey():
    if request.method == 'POST':
        # Handle survey creation form submission
        new_survey = Survey(
            title=request.form['title'],
            main_question=request.form['main_question'],
            description=request.form['description'],
            user_id=1  # Replace with actual user authentication
        )
        db.session.add(new_survey)
        db.session.commit()

        # Generate initial questions based on main question
        return redirect(url_for('main.dashboard'))

    return render_template('create_survey.html')


@main_bp.route('/survey/<int:survey_id>')
def view_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    return render_template('take_survey.html', survey=survey)


@main_bp.route('/survey/<int:survey_id>/insights')
def survey_insights(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    insights = Insight.query.filter_by(survey_id=survey_id).all()
    return render_template('insights.html', survey=survey, insights=insights)


# API routes
@api_bp.route('/surveys', methods=['GET'])
def get_surveys():
    surveys = Survey.query.all()
    return jsonify([{
        'id': survey.id,
        'title': survey.title,
        'main_question': survey.main_question,
        'description': survey.description
    } for survey in surveys])


@api_bp.route('/surveys', methods=['POST'])
def create_survey_api():
    data = request.json
    new_survey = Survey(
        title=data['title'],
        main_question=data['main_question'],
        description=data.get('description', ''),
        user_id=1  # Replace with actual user authentication
    )
    db.session.add(new_survey)
    db.session.commit()

    # Generate initial questions based on main question
    return jsonify({'id': new_survey.id}), 201


@api_bp.route('/surveys/<int:survey_id>/questions', methods=['GET'])
def get_questions(survey_id):
    questions = Question.query.filter_by(survey_id=survey_id).order_by(Question.order).all()
    return jsonify([{
        'id': question.id,
        'text': question.text,
        'question_type': question.question_type,
        'options': question.options
    } for question in questions])


@api_bp.route('/surveys/<int:survey_id>/answer', methods=['POST'])
def submit_answer(survey_id):
    data = request.json

    # Find or create survey response
    response = SurveyResponse.query.filter_by(
        survey_id=survey_id,
        respondent_id=data['respondent_id']
    ).first()

    if not response:
        response = SurveyResponse(
            survey_id=survey_id,
            respondent_id=data['respondent_id']
        )
        db.session.add(response)
        db.session.commit()

    # Save the answer
    answer = Answer(
        text=data['answer_text'],
        question_id=data['question_id'],
        response_id=response.id
    )
    db.session.add(answer)
    db.session.commit()

    # Process the answer
    processed_data = process_response(answer.text)
    answer.processed_data = processed_data
    db.session.commit()

    # Generate next question
    next_question = generate_next_question(survey_id, response.id)
    if next_question:
        return jsonify({
            'next_question': {
                'id': next_question.id,
                'text': next_question.text,
                'question_type': next_question.question_type,
                'options': next_question.options
            }
        })
    else:
        # Complete the survey response
        response.completed_at = datetime.utcnow()
        db.session.commit()

        # Generate insights based on new data
        generate_insights(survey_id)

        return jsonify({'status': 'completed'})


@api_bp.route('/surveys/<int:survey_id>/insights', methods=['GET'])
def get_insights(survey_id):
    insights = Insight.query.filter_by(survey_id=survey_id).all()
    return jsonify([{
        'id': insight.id,
        'text': insight.text,
        'confidence': insight.confidence,
        'created_at': insight.created_at.isoformat()
    } for insight in insights])