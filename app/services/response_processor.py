import json
import openai


def process_response(response_text):
    """
    Process a natural language response to extract structured data
    """
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """
                    Extract key information from this survey response. 
                    Identify:
                    1. Main topics mentioned
                    2. Sentiment (positive, negative, neutral)
                    3. Key entities mentioned
                    4. Any quantitative data provided

                    Format the output as JSON.
                """},
                {"role": "user", "content": response_text}
            ],
            max_tokens=300,
            temperature=0.3
        )

        processed_data = completion.choices[0].message.content

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
