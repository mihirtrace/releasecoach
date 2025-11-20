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

EXAMPLES OF GOOD POSTS THAT SHOULD GET "YES":

Example 1:
"New streamlined checkout for basketball cameras. Customers with player subscriptions get an email with a direct link. The new landing page removes unnecessary steps and decisions - just a simple modal flow. This helps customers buy basketball cameras faster with less confusion and fewer abandoned checkouts."

Example 2:
"Added auto-highlight detection for soccer games. Customers just upload their full game video and our AI finds the key moments (goals, near-misses, great saves). Saves parents 2+ hours of manual editing per game. Solves the problem of parents not having time to create highlight reels."

Example 3:
"Fixed bug where livestream would freeze on poor connections. Customers livestreaming games will see fewer dropouts and better quality. This was our #1 support complaint from parents trying to watch their kids' games remotely."

WHAT QUALIFIES AS "YES":
- The post explains WHO uses it and WHEN/HOW they'll use it (even if briefly)
- The post describes the customer benefit or outcome (even if it's indirect)
- The post explains why this matters or what problem it solves
- Information can be in ANY part of the post, not just labeled sections
- Give the benefit of the doubt if the answers are reasonably clear

WHAT REQUIRES "NO":
- Missing who will use this or how it will be used
- No explanation of customer benefit (direct or indirect)
- No rationale for why this matters or what problem it solves
- Purely technical details with no customer context

Here is the post to analyze:
---
{message_text}
---

Analyze whether this post adequately answers all three questions. Be fair and lenient - if the information is there in ANY form, even if not perfectly structured, answer YES.

Respond in this exact format:
ANSWERS_QUESTIONS: [YES or NO]
FEEDBACK: [Brief explanation of what's missing]
CONGRATULATIONS: [REQUIRED if YES - You MUST write a unique, personalized, encouraging 1-sentence message (10-15 words) celebrating what they did well. Be specific and genuine. DO NOT LEAVE BLANK if YES. If NO, write "N/A"]"""

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

        # Ensure we have a congratulations message for YES answers
        if answers_questions and (not congratulations or congratulations == "N/A"):
            congratulations = "Great job addressing customer value and impact in your post!"

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
