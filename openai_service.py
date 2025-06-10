import os
import json
import logging
import time
from openai import OpenAI

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "default_key")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_wisdom_quotes(user_input):
    """
    Get curated wisdom quotes from OpenAI GPT-4-mini based on user's current state
    """
    
    start_time = time.time()
    logging.info(f"Starting OpenAI request for input: '{user_input}'")
    
    # JSON-based prompt for reliable parsing
    system_prompt = """You are a wisdom curator for The Perspective Shift app. The user will describe how they're feeling or what's on their mind right now. Your task is to provide 2-3 carefully selected quotes from throughout history that offer a fresh perspective on their current state.

Respond with a JSON object containing an array of quotes. Each quote should have exactly these fields:
- quote: The exact quote text (without quotation marks)
- attribution: The person's name who said it
- perspective: 1-2 sentences explaining how this quote offers a new lens through which to view their current experience
- context: 1-2 sentences about when/why this wisdom emerged, the circumstances that led to this insight

Guidelines:
- Use only real, verifiable quotes
- Draw from diverse sources: ancient wisdom traditions, modern psychology, literature, science, arts
- Match the emotional tone while offering a shift in perspective
- For positive states, offer quotes that deepen or expand the feeling
- For challenging states, offer quotes that reframe without dismissing the experience
- Include a mix of well-known and lesser-known wisdom

Response format:
{
  "quotes": [
    {
      "quote": "quote text here",
      "attribution": "Person Name",
      "perspective": "explanation here",
      "context": "historical context here"
    }
  ]
}"""

    user_prompt = f"User's current state: {user_input}"
    
    logging.info(f"System prompt length: {len(system_prompt)} chars")
    logging.info(f"User prompt: '{user_prompt}'")

    try:
        # the newest OpenAI model is "gpt-4o-mini" which was released after "gpt-4-mini".
        # do not change this unless explicitly requested by the user
        api_start_time = time.time()
        logging.info("Making OpenAI API call...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
            response_format={"type": "json_object"},
            timeout=50.0  # 50 second timeout with 60s function limit
        )
        
        api_duration = time.time() - api_start_time
        response_text = response.choices[0].message.content
        logging.info(f"OpenAI API call successful! Duration: {api_duration:.2f}s, Response length: {len(response_text)} chars")
        logging.info(f"Full OpenAI response: {response_text}")
        
        # Parse JSON response
        logging.info("Parsing JSON response from OpenAI...")
        quotes = parse_json_response(response_text)
        logging.info(f"Parsing complete. Extracted {len(quotes)} quotes")
        
        for i, quote in enumerate(quotes):
            logging.info(f"Quote {i+1}: '{quote.get('quote', 'NO QUOTE')}' by {quote.get('attribution', 'NO ATTRIBUTION')}")
        
        total_duration = time.time() - start_time
        logging.info(f"Total get_wisdom_quotes duration: {total_duration:.2f}s (API: {api_duration:.2f}s)")
        return quotes
        
    except Exception as e:
        total_duration = time.time() - start_time
        logging.error(f"Error calling OpenAI API after {total_duration:.2f}s: {str(e)}")
        logging.error(f"Exception type: {type(e)}")
        # Return fallback quotes if API fails
        logging.warning("Returning fallback quotes due to API error")
        return get_fallback_quotes()

def parse_json_response(response_text):
    """
    Parse JSON response from OpenAI into a list of quote dictionaries
    """
    try:
        if not response_text:
            logging.error("Empty response from OpenAI")
            return get_fallback_quotes()
            
        logging.info("Parsing JSON response...")
        data = json.loads(response_text)
        
        if 'quotes' not in data:
            logging.error("No 'quotes' key found in JSON response")
            logging.error(f"Response keys: {list(data.keys())}")
            return get_fallback_quotes()
        
        quotes = data['quotes']
        logging.info(f"Found {len(quotes)} quotes in JSON response")
        
        # Validate each quote has required fields
        validated_quotes = []
        for i, quote in enumerate(quotes):
            if all(key in quote for key in ['quote', 'attribution', 'perspective', 'context']):
                validated_quotes.append({
                    'quote': quote['quote'].strip(),
                    'attribution': quote['attribution'].strip(), 
                    'perspective': quote['perspective'].strip(),
                    'context': quote['context'].strip()
                })
                logging.info(f"Validated quote {i+1}: '{quote['quote'][:50]}...' by {quote['attribution']}")
            else:
                logging.warning(f"Quote {i+1} missing required fields: {quote}")
        
        if len(validated_quotes) == 0:
            logging.error("No valid quotes found after validation")
            return get_fallback_quotes()
            
        return validated_quotes[:3]  # Return max 3 quotes
        
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {str(e)}")
        logging.error(f"Response text: {response_text}")
        return get_fallback_quotes()
    except Exception as e:
        logging.error(f"Error processing JSON response: {str(e)}")
        import traceback
        logging.error(f"Full traceback: {traceback.format_exc()}")
        return get_fallback_quotes()

def get_fallback_quotes():
    """
    Fallback quotes in case the API fails
    """
    return [
        {
            'quote': 'The only way to make sense out of change is to plunge into it, move with it, and join the dance.',
            'attribution': 'Alan Watts',
            'perspective': 'This wisdom reminds us that resistance to our current experience often creates more suffering than the experience itself.',
            'context': 'Watts, a philosopher who bridged Eastern and Western thought, spoke these words as he explored how to find peace within life\'s constant flux during the cultural upheavals of the 1960s.'
        },
        {
            'quote': 'Everything can be taken from a man but one thing: the last of human freedoms - to choose one\'s attitude in any given set of circumstances.',
            'attribution': 'Viktor Frankl',
            'perspective': 'Even in our most challenging moments, we retain the power to choose how we relate to our experience.',
            'context': 'Frankl discovered this truth while surviving Nazi concentration camps, realizing that inner freedom could never be taken away, even when everything else was lost.'
        }
    ]
