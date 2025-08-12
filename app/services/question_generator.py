import json
import os
import anthropic
from app.models import db, Survey, Question, Answer, SurveyResponse
from app.constants import CLAUDE_MODEL, DEFAULT_QUESTION_MAX_TOKENS, QUESTION_GENERATION_TEMPERATURE


def generate_next_question(survey_id, response_id):
    """
    Generate the next question based on previous answers using LLM
    """
    survey = Survey.query.get(survey_id)
    response = SurveyResponse.query.get(response_id)

    # Get all previous answers for this response
    previous_answers = Answer.query.filter_by(response_id=response_id).all()
    previous_questions = [answer.question for answer in previous_answers]
    previous_qa_pairs = [
        {
            "question": answer.question.text,
            "answer": answer.text
        }
        for answer in previous_answers
    ]

    # If there are no previous questions, generate the first question
    if not previous_questions:
        return generate_first_question(survey)

    # Use Claude API to generate the next question
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=DEFAULT_QUESTION_MAX_TOKENS,
            temperature=QUESTION_GENERATION_TEMPERATURE,
            messages=[
                {
                    "role": "user", 
                    "content": f"""You are an adaptive survey assistant. You generate insightful follow-up questions based on 
                    the main survey question and previous responses. The main question is: 
                    "{survey.main_question}"

                    Generate a natural, conversational follow-up question that delves deeper based on previous answers.
                    The question should help gather more specific insights related to the main survey question.
                    Return ONLY the question text without any explanation or additional content.
                    
                    Previous Q&A: {json.dumps(previous_qa_pairs)}"""
                }
            ]
        )

        question_text = response.content[0].text.strip()
        print(f'Question text: {question_text}')

        # Create and save the new question
        new_question = Question(
            text=question_text,
            question_type='open_ended',
            order=len(previous_questions) + 1,
            survey_id=survey_id
        )
        db.session.add(new_question)
        db.session.commit()

        return new_question

    except Exception as e:
        print(f"Error generating question: {e}")
        return None


def generate_first_question(survey):
    """Generate the first question for a survey"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    print(f"Generating first question for survey: {survey.main_question}")
    print(f"API key available: {bool(api_key)}")
    
    if not api_key:
        print("No ANTHROPIC_API_KEY found in environment")
        return None
        
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=DEFAULT_QUESTION_MAX_TOKENS,
            temperature=QUESTION_GENERATION_TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are an adaptive survey assistant. Generate the first question for a survey 
                    based on the main survey question: "{survey.main_question}"

                    The first question should be open-ended and help start the conversation.
                    Return ONLY the question text without any explanation or additional content."""
                }
            ]
        )

        question_text = response.content[0].text.strip()
        print(f'First Question text: {question_text}')
        
        # Create and save the new question
        new_question = Question(
            text=question_text,
            order=1,
            survey_id=survey.id
        )
        db.session.add(new_question)
        db.session.commit()

        return new_question

    except Exception as e:
        print(f"Error generating first question: {e}")
        return None