# Webhook Setup Guide

Your bot has been updated to use webhooks instead of Socket Mode. This is more reliable and efficient for Railway deployment.

## Setup Steps

### 1. Get Your Railway URL

Once Railway deploys the new code, get your app's public URL:
- Go to your Railway project
- Click on your service
- Under "Settings" → "Networking" → Copy the public domain
- It should look like: `https://your-app-name.up.railway.app`

### 2. Update Slack App Configuration

Go to https://api.slack.com/apps and select your ReleaseCoach app:

#### A. Disable Socket Mode
1. Go to **Socket Mode** (in left sidebar)
2. Toggle it **OFF**

#### B. Enable Event Subscriptions
1. Go to **Event Subscriptions** (in left sidebar)
2. Toggle **Enable Events** to **ON**
3. In **Request URL**, enter:
   ```
   https://your-app-name.up.railway.app/slack/events
   ```
   Replace `your-app-name` with your actual Railway URL
4. Wait for the **Verified** ✅ checkmark
5. Under **Subscribe to bot events**, ensure you have:
   - `message.channels` (for public channels)
   - OR `message.groups` (for private channels)
   - `app_mention`
6. Click **Save Changes** at the bottom

#### C. Verify OAuth Scopes
1. Go to **OAuth & Permissions** (in left sidebar)
2. Under **Bot Token Scopes**, ensure you have:
   - `chat:write`
   - `channels:history` (for public) OR `groups:history` (for private)
   - `channels:read` OR `groups:read`
   - `app_mentions:read`

### 3. Update Environment Variables in Railway

In Railway, you **no longer need** `SLACK_APP_TOKEN`. Update your environment variables:

**Keep these:**
- `SLACK_BOT_TOKEN` (starts with `xoxb-`)
- `ANTHROPIC_API_KEY`
- `MONITORED_CHANNEL_ID`

**Remove this (not needed anymore):**
- `SLACK_APP_TOKEN` ❌

**Optional - Add if you want extra security:**
- `SLACK_SIGNING_SECRET` (from Slack App Settings → Basic Information)

### 4. Redeploy

Railway should auto-deploy the new code. You can verify it's running by:
1. Check Railway logs for: "⚡️ Slack Accountability Bot is running!"
2. Visit: `https://your-app-name.up.railway.app/health`
3. You should see: `{"status": "ok", "monitoring_channel": "C01CMR89Q9L"}`

### 5. Test It!

Post a test message in your monitored Slack channel. The bot should respond in a thread!

## Benefits of Webhooks

✅ **More reliable** - No persistent connection to maintain
✅ **More scalable** - Only runs when events arrive
✅ **Better for Railway** - Uses fewer resources
✅ **No connection drops** - HTTP is stateless and robust

## Troubleshooting

### "URL verification failed"
- Make sure Railway has finished deploying
- Check that the URL is exactly: `https://your-domain.up.railway.app/slack/events`
- Check Railway logs for errors

### "Bot not responding"
- Verify the webhook URL shows "Verified ✅" in Slack
- Check Railway logs when you post a message
- Make sure the bot is invited to the channel

### "Challenge failed"
- This is normal during initial setup
- Slack sends a challenge request to verify the URL
- The Flask adapter automatically handles this
- Just wait for the "Verified ✅" checkmark

## What Changed?

**Before (Socket Mode):**
- Persistent WebSocket connection
- Required `SLACK_APP_TOKEN`
- Always running

**After (Webhooks):**
- HTTP endpoints
- No persistent connection
- Only processes when events arrive
- More reliable and efficient
