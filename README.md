# Slack Accountability Bot

A Slack bot that monitors posts in a channel and ensures they answer key questions about customer value and impact. Uses Claude AI to intelligently analyze messages.

## What It Does

The bot monitors a specific Slack channel and checks if posts answer these questions:
1. How will this be used by the customer?
2. If it's not customer facing, what will this eventually lead to for the customer?
3. Why did we spend time on this and what problem does it solve?

**If the post answers the questions:** Posts a "good job" message in the thread with positive feedback.

**If the post doesn't answer the questions:** Asks for an update with the missing information.

## Setup Instructions

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Give it a name (e.g., "Accountability Bot") and select your workspace
4. Click "Create App"

### 2. Configure Bot Permissions

1. In your app settings, go to "OAuth & Permissions"
2. Scroll to "Scopes" → "Bot Token Scopes"
3. Add these scopes:
   - `channels:history` - Read messages in public channels
   - `channels:read` - View basic channel info
   - `chat:write` - Send messages
   - `app_mentions:read` - See when bot is mentioned

### 3. Enable Socket Mode

1. Go to "Socket Mode" in the sidebar
2. Enable Socket Mode
3. Give it a token name (e.g., "accountability-bot-token")
4. Copy the **App-Level Token** (starts with `xapp-`) - you'll need this

### 4. Enable Events

1. Go to "Event Subscriptions"
2. Enable Events
3. Under "Subscribe to bot events", add:
   - `message.channels` - Listen to messages in public channels
   - `app_mention` - Listen when bot is mentioned

### 5. Install App to Workspace

1. Go to "Install App" in the sidebar
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`) - you'll need this

### 6. Get Your Channel ID

1. Open Slack in your browser
2. Navigate to the channel you want to monitor
3. The URL will look like: `https://yourworkspace.slack.com/messages/C1234567890`
4. Copy the part after `/messages/` (e.g., `C1234567890`)

### 7. Get Anthropic API Key

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Go to "API Keys"
4. Create a new key and copy it

### 8. Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your values:
   ```
   SLACK_BOT_TOKEN=xoxb-your-bot-token-from-step-5
   SLACK_APP_TOKEN=xapp-your-app-token-from-step-3
   ANTHROPIC_API_KEY=your-anthropic-key-from-step-7
   MONITORED_CHANNEL_ID=C1234567890-from-step-6
   ```

### 9. Test Locally

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python slack_bot.py
   ```

4. Post a test message in your monitored channel!

## Deploy to Railway

1. Create account at [https://railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account and select this repo
4. Add environment variables in Railway dashboard:
   - `SLACK_BOT_TOKEN`
   - `SLACK_APP_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `MONITORED_CHANNEL_ID`
5. Railway will automatically detect the `Procfile` and deploy

## Deploy to Render

1. Create account at [https://render.com](https://render.com)
2. Click "New" → "Background Worker"
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python slack_bot.py`
5. Add environment variables in the dashboard (same as above)
6. Click "Create Background Worker"

## How It Works

1. Bot listens to all messages in the monitored channel
2. When a new message is posted, it sends the message to Claude API
3. Claude analyzes if the post answers the three key questions
4. Bot responds in a thread with either:
   - Positive feedback if questions are answered
   - Request for more information if questions aren't answered

## Customization

### Change the Questions

Edit the `REQUIRED_QUESTIONS` variable in `slack_bot.py`:

```python
REQUIRED_QUESTIONS = """
1. Your first question?
2. Your second question?
3. Your third question?
"""
```

### Change the Claude Model

Edit line 63 in `slack_bot.py`:

```python
model="claude-sonnet-4-5-20250929",  # Change to claude-3-5-haiku-20241022 for faster/cheaper
```

### Change Response Messages

Edit the responses in the `handle_message_events` function (lines 95-103).

## Troubleshooting

**Bot isn't responding:**
- Check that Socket Mode is enabled
- Verify all environment variables are set correctly
- Make sure the bot is invited to the channel (`/invite @YourBotName`)
- Check logs for errors

**Getting API errors:**
- Verify your Anthropic API key is valid and has credits
- Check that your Slack tokens haven't expired

**Bot responds to old messages:**
- This is normal on startup - the bot processes recent messages
- To avoid this, you can add a timestamp check in the code

## Cost Considerations

- Claude API costs approximately $0.003 per message analyzed (using Sonnet)
- For a team posting 100 messages/day, this is ~$9/month
- Consider using Claude Haiku for lower costs (~$0.0003/message = $0.90/month)

## License

MIT - Use freely!
