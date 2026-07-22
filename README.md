# Google Chat Signals Notifier 

Inflight signals are a critical performance metric for our Technical Support Representatives (TSRs). This automated Python bot ensures no signal gets left behind. 

By reading pending cases from Google Sheets and sending grouped, interactive Google Chat Cards directly to each agent, it makes it incredibly easy for TSRs to spot missing actions, click the embedded link, fill out the required form, and keep their metrics in the green.

## Why this matters & Features

Boosts Metric Compliance: Delivers targeted, impossible-to-miss reminders directly to the agent's chat, drastically reducing overdue signals.
Frictionless Action: The interactive Cards V2 feature direct "Link Form" buttons. Agents can fix their pending cases with a single click right from the chat.
Anti-Spam & Grouping: Prevents channel fatigue by grouping all pending tasks by agent. If an agent has many pending cases, the bot uses native `collapsible` widgets (Show more / Show less) to keep the chat clean.
Google Sheets Integration: Fetches live data from specific spreadsheet ranges, extracting embedded `=HYPERLINK()` formulas seamlessly.
Rate Limit Handling: Built-in payload chunking and `time.sleep()` delays to respect Google Chat's webhook rate limits (prevents HTTP 400 and 429 errors).

## Tech Stack

Language: Python 3.9+
Data Processing: Pandas
APIs: Google Sheets API v4, Google Workspace Chat API (Webhooks)
Deployment: Google Cloud Run (Jobs) & Cloud Scheduler

## Setup and Local Execution

### Configuration
Before running, you need to configure your environment. 
Create a `.env` file in the root directory:
```env
SPREADSHEET_ID=your_sheet_id
SHEET_NAME=[NEW] Pending Signals
WEBHOOK_URL=your_google_chat_webhook

<img width="749" height="424" alt="Screenshot 2026-07-21 6 35 43 PM" src="https://github.com/user-attachments/assets/3fe6c91e-e8f3-42ab-a0cb-750f028a7614" />
