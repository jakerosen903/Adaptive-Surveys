# Adaptive Surveys

A dynamic survey platform that uses Claude AI to generate contextual follow-up questions based on user responses.

## Setup

### Prerequisites
- Python 3.13+
- Claude API key from Anthropic

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file:
   ```env
   SECRET_KEY=your-secret-key-here
   ANTHROPIC_API_KEY=your-claude-api-key-here
   ```

3. Initialize database:
   ```bash
   python init_db.py
   ```

4. Run the server:
   ```bash
   python app.py
   ```

Visit `http://localhost:5001` to access the application.

## Sharing Surveys Externally

To share surveys with people on different networks:

1. **Install ngrok** (for temporary public access):
   ```bash
   brew install ngrok
   ```

2. **Run your app**:
   ```bash
   python app.py
   ```

3. **Create public tunnel** (in another terminal):
   ```bash
   ngrok http 5001
   ```

4. **Share the HTTPS URL** that ngrok provides with your friends

The dashboard includes "Share Survey" buttons with copy-to-clipboard functionality for easy sharing.

## API Key Setup

### Claude API Key
1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `.env` file as `ANTHROPIC_API_KEY=your-key-here`

## Testing the System

1. Register an account at `http://localhost:5000/register`
2. Create a new survey with a main question
3. Share the survey link with test respondents
4. Answer questions to see dynamic follow-ups
5. Check insights on the dashboard