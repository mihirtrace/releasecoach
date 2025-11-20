import os
import re
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Slack app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Channel to monitor
MONITORED_CHANNEL_ID = os.environ.get("MONITORED_CHANNEL_ID")

# The questions we want posts to answer
REQUIRED_QUESTIONS = """
1. How will this be used by the customer?
2. If it's not customer facing, what will this eventually lead to for the customer?
3. Why did we spend time on this and what problem does it solve?
"""


def analyze_post_with_claude(message_text: str) -> dict:
    """
    Use Claude to analyze if a post answers the required questions.
    Returns a dict with 'answers_questions' (bool) and 'feedback' (str).
    """
    prompt = f"""You are analyzing a team post to see if it addresses customer value and impact.

The post must answer these questions:
{REQUIRED_QUESTIONS}

Here is the post to analyze:
---
{message_text}
---

Analyze whether this post adequately answers all three questions.

Respond in this exact format:
ANSWERS_QUESTIONS: [YES or NO]
FEEDBACK: [Brief explanation of what's missing]
CONGRATULATIONS: [If YES, write a unique, personalized, encouraging 1-sentence message (10-15 words) that celebrates what they did well. Be specific and genuine. Vary your style - sometimes enthusiastic, sometimes thoughtful, sometimes appreciative. If NO, leave blank]

Be strict but fair - the post should clearly address customer value and impact."""

    try:
        message = anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse the response
        answers_match = re.search(r'ANSWERS_QUESTIONS:\s*(YES|NO)', response_text, re.IGNORECASE)
        feedback_match = re.search(r'FEEDBACK:\s*(.+?)(?=CONGRATULATIONS:|$)', response_text, re.DOTALL)
        congrats_match = re.search(r'CONGRATULATIONS:\s*(.+)', response_text, re.DOTALL)

        answers_questions = answers_match.group(1).upper() == 'YES' if answers_match else False
        feedback = feedback_match.group(1).strip() if feedback_match else "Could not parse feedback"
        congratulations = congrats_match.group(1).strip() if congrats_match else ""

        return {
            'answers_questions': answers_questions,
            'feedback': feedback,
            'congratulations': congratulations
        }
    except Exception as e:
        print(f"Error analyzing with Claude: {e}")
        return {
            'answers_questions': False,
            'feedback': f"Error analyzing post: {str(e)}",
            'congratulations': ""
        }


@app.event("message")
def handle_message_events(event, say, client):
    """Handle new messages in the monitored channel"""

    # Ignore bot messages and threaded replies
    if event.get("bot_id") or event.get("thread_ts"):
        return

    # Only monitor the specified channel
    if event.get("channel") != MONITORED_CHANNEL_ID:
        return

    message_text = event.get("text", "")
    message_ts = event.get("ts")

    # Skip empty messages
    if not message_text.strip():
        return

    print(f"Analyzing message: {message_text[:100]}...")

    # Analyze the message with Claude
    analysis = analyze_post_with_claude(message_text)

    if analysis['answers_questions']:
        # Post positive feedback in thread with personalized message
        response = f"✅ {analysis['congratulations']}"
    else:
        # Ask for more information in thread
        response = f"""📝 This post could use more detail about customer impact.

Please help us understand:
{REQUIRED_QUESTIONS}

_{analysis['feedback']}_"""

    # Post response as a thread reply
    try:
        client.chat_postMessage(
            channel=event["channel"],
            thread_ts=message_ts,
            text=response
        )
        print(f"Posted response: {'Positive' if analysis['answers_questions'] else 'Request for update'}")
    except Exception as e:
        print(f"Error posting message: {e}")


@app.event("app_mention")
def handle_mentions(event, say):
    """Handle when the bot is mentioned"""
    say(f"👋 Hi! I help ensure posts answer these key questions:\n{REQUIRED_QUESTIONS}")

def main():
    app_token = os.environ["SLACK_APP_TOKEN"]

    while True:
        try:
            handler = SocketModeHandler(app, app_token)
            print("⚡️ Slack Accountability Bot is running!")
            print(f"📊 Monitoring channel: {MONITORED_CHANNEL_ID}")
            handler.start()  # This blocks until the Socket Mode connection dies
        except Exception as e:
            print(f"Top-level SocketMode error: {e}. Restarting in 5 seconds...")
            time.sleep(5)


if __name__ == "__main__":
    main()
