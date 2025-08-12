import json
import os
import anthropic
from app.constants import CLAUDE_MODEL, DEFAULT_PROCESSING_MAX_TOKENS, PROCESSING_TEMPERATURE


def process_response(response_text):
    """
    Process a natural language response to extract structured data
    """
    try:
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        completion = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=DEFAULT_PROCESSING_MAX_TOKENS,
            temperature=PROCESSING_TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract key information from this survey response. 
                    Identify:
                    1. Main topics mentioned
                    2. Sentiment (positive, negative, neutral)
                    3. Key entities mentioned
                    4. Any quantitative data provided

                    Format the output as JSON.
                    
                    Survey response: {response_text}"""
                }
            ]
        )

        processed_data = completion.content[0].text
        print(f'Processed response: {processed_data}')
        # Try to parse as JSON, if it fails, return as text
        try:
            parsed_json = json.loads(processed_data)
            return json.dumps(parsed_json)
        except:
            return json.dumps({
                "raw_analysis": processed_data,
                "parsing_error": True
            })

    except Exception as e:
        print(f"Error processing response: {e}")
        return json.dumps({
            "error": str(e)
        })
