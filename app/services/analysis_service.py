import json
import openai
from app.models import db, Survey, Question, Answer, Insight, SurveyResponse


def generate_insights(survey_id):
    """
    Analyze survey responses and generate insights
    """
    survey = Survey.query.get(survey_id)
    if not survey:
        return []

    # Get all completed responses
    responses = SurveyResponse.query.filter_by(
        survey_id=survey_id,
        completed_at=None
    ).all()

    if not responses:
        return []

    # Collect all Q&A pairs
    all_qa_data = []
    for response in responses:
        answers = Answer.query.filter_by(response_id=response.id).all()
        qa_pairs = [
            {
                "question": answer.question.text,
                "answer": answer.text,
                "processed_data": json.loads(answer.processed_data) if answer.processed_data else {}
            }
            for answer in answers
        ]
        all_qa_data.append({
            "respondent_id": response.respondent_id,
            "qa_pairs": qa_pairs
        })

    # Use OpenAI to generate insights
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"""
                    You are an expert survey data analyst. Analyze the survey responses and generate 
                    5 valuable insights related to the main survey question: "{survey.main_question}"

                    For each insight, provide:
                    1. A clear insight statement
                    2. A confidence level as a percentage (0-100)
                    3. Brief supporting evidence using direct references from the responses

                    Format the output as a JSON array of insight objects.
                """},
                {"role": "user", "content": json.dumps(all_qa_data)}
            ],
            max_tokens=1000,
            temperature=0.5
        )

        insights_text = completion.choices[0].message.content

        # Try to parse as JSON
        try:
            insights_data = json.loads(insights_text)

            # Save insights to database
            for insight_data in insights_data:
                insight = Insight(
                    survey_id=survey_id,
                    text=insight_data.get('insight_statement', '') + "\n\n" +
                         insight_data.get('supporting_evidence', ''),
                    confidence=float(insight_data.get('confidence_level', 0.5))
                )
                db.session.add(insight)

            db.session.commit()
            return insights_data

        except json.JSONDecodeError:
            print(f"Error parsing insights JSON: {insights_text}")

            # Save as single insight if JSON parsing fails
            insight = Insight(
                survey_id=survey_id,
                text=insights_text,
                confidence=0.5
            )
            db.session.add(insight)
            db.session.commit()
            return [{"text": insights_text}]

    except Exception as e:
        print(f"Error generating insights: {e}")
        return []