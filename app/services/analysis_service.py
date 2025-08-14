import json
import os
import anthropic
from app.models import db, Survey, Question, Answer, Insight, SurveyResponse
from app.constants import CLAUDE_MODEL, DEFAULT_ANALYSIS_MAX_TOKENS, ANALYSIS_TEMPERATURE


def generate_insights(survey_id):
    """
    Analyze survey responses and generate insights
    """
    survey = Survey.query.get(survey_id)
    if not survey:
        return []

    # Get all completed responses
    responses = SurveyResponse.query.filter(
        SurveyResponse.survey_id == survey_id,
        SurveyResponse.completed_at.isnot(None)
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

    # Use Claude to generate insights
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        completion = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=DEFAULT_ANALYSIS_MAX_TOKENS,
            temperature=ANALYSIS_TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are an expert survey data analyst. Analyze the survey responses and generate 
                    3-7 valuable insights related to the main survey question: "{survey.main_question}"

                    Return your analysis as a JSON array with this EXACT structure:
                    [
                      {{
                        "insight_statement": "Clear, actionable insight statement",
                        "confidence_level": 85,
                        "supporting_evidence": "Brief supporting evidence with direct quotes",
                        "insight_type": "trend|pattern|recommendation|concern|opportunity",
                        "tags": ["tag1", "tag2"]
                      }}
                    ]

                    Guidelines:
                    - insight_statement: 1-2 sentences, actionable and specific
                    - confidence_level: integer 0-100 based on evidence strength
                    - supporting_evidence: 2-3 sentences with direct quotes where possible
                    - insight_type: categorize as trend, pattern, recommendation, concern, or opportunity
                    - tags: 2-4 relevant keywords for this insight

                    Focus on insights that would be most valuable for improving the survey topic or understanding user needs.
                    
                    Survey data: {json.dumps(all_qa_data)}"""
                }
            ]
        )

        insights_text = completion.content[0].text
        print(f'Insights text: {insights_text}')

        # Try to parse as JSON
        try:
            insights_data = json.loads(insights_text)

            # Save insights to database
            current_response_count = len(responses)
            for insight_data in insights_data:
                insight = Insight(
                    survey_id=survey_id,
                    text=insight_data.get('insight_statement', ''),
                    supporting_evidence=insight_data.get('supporting_evidence', ''),
                    confidence=float(insight_data.get('confidence_level', 50)) / 100.0,
                    insight_type=insight_data.get('insight_type', 'pattern'),
                    tags=json.dumps(insight_data.get('tags', [])),
                    generated_from_responses_count=current_response_count
                )
                db.session.add(insight)

            db.session.commit()
            return insights_data

        except json.JSONDecodeError:
            print(f"Error parsing insights JSON: {insights_text}")

            # Save as single insight if JSON parsing fails
            current_response_count = len(responses)
            insight = Insight(
                survey_id=survey_id,
                text=insights_text,
                confidence=0.5,
                generated_from_responses_count=current_response_count
            )
            db.session.add(insight)
            db.session.commit()
            return [{"text": insights_text}]

    except Exception as e:
        print(f"Error generating insights: {e}")
        return []