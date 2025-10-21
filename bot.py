# ==============================================================================
# --- Required Libraries ---
# ==============================================================================
import logging
import os
import google.generativeai as genai
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# ==============================================================================
# --- Secure Configuration ---
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
try:
    ADMIN_ID = int(os.environ.get('ADMIN_ID'))
except (ValueError, TypeError):
    ADMIN_ID = None

# ==============================================================================
# --- Initial Setup & Validation ---
# ==============================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.critical("CRITICAL ERROR: TELEGRAM_TOKEN or GEMINI_API_KEY environment variables are not set. Bot cannot start.")
    exit()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    # --- THIS IS THE FIX: Using the correct, specific model name ---
    model = genai.GenerativeModel('gemini-1.0-pro') 
    logging.info("Google AI configured successfully with model 'gemini-1.0-pro'.")
except Exception as e:
    logging.error(f"FATAL: Could not configure Google AI. Error: {e}")
    exit()

daily_users = {}

# ==============================================================================
# --- Helper Functions ---
# ==============================================================================

def track_user(user_id: int):
    """Tracks unique daily active users."""
    today = date.today()
    if today not in daily_users:
        daily_users[today] = set()
    daily_users[today].add(user_id)

async def safe_reply(update: Update, text: str, **kwargs):
    """Safely send replies and log any errors."""
    try:
        await update.message.reply_text(text, **kwargs)
    except Exception as e:
        logging.error(f"Telegram reply failed: {e}")

# ==============================================================================
# --- Command Handlers (Your Bot's Logic) ---
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user.id)
    user_name = update.effective_user.first_name
    await safe_reply(update, f"Hello {user_name}! I am your AI assistant. Ask me anything about coding or careers.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Restart the bot\n"
        "/help - Shows this list of commands\n"
        "/website - Visit our official website\n"
        "/roadmaps - Explore all career roadmaps\n"
        "/blog - Read the latest blog posts\n"
        "/dsa - Get a random DSA practice problem\n"
        "/connect - Connect with the developer\n"
        "/idea - Get a new project idea\n"
        "/explain [concept] - Ask the AI to explain a concept\n"
        "/clear - Get info on how to clear your chat history\n"
        "/feedback [message] - Send your feedback"
    )
    await safe_reply(update, help_text)

async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    website_url = "https://codewithmsmaxpro.me"
    keyboard = [[InlineKeyboardButton("Visit Website", url=website_url)]]
    await safe_reply(update, "Click the button below to visit our official website!", reply_markup=InlineKeyboardMarkup(keyboard))

async def roadmaps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    roadmaps_url = "https://codewithmsmaxpro.me/roadmaps.html"
    keyboard = [[InlineKeyboardButton("View Roadmaps", url=roadmaps_url)]]
    await safe_reply(update, "Click the button below to explore all the career roadmaps!", reply_markup=InlineKeyboardMarkup(keyboard))

async def blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    blog_url = "https://codewithmsmaxpro.me/blog.html"
    keyboard = [[InlineKeyboardButton("Read Blog", url=blog_url)]]
    await safe_reply(update, "Click the button below to read our latest blog posts.", reply_markup=InlineKeyboardMarkup(keyboard))

async def dsa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(update, "Finding a good DSA problem for you...")
    try:
        prompt = "Give me a beginner-friendly DSA (Data Structures and Algorithms) practice problem. State the problem clearly, provide a hint, but do not provide the solution."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /dsa) --- \n Error: {e}")
        await safe_reply(update, "Sorry, I couldn't find a problem right now. Please try again later.")
        
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    github_url = "https://github.com/MSMAXPRO"
    linkedin_url = "https://linkedin.com/in/your-linkedin-username" # <-- IMPORTANT: Update this URL
    keyboard = [
        [InlineKeyboardButton("GitHub", url=github_url)],
        [InlineKeyboardButton("LinkedIn", url=linkedin_url)]
    ]
    await safe_reply(update, "You can connect with me on these platforms:", reply_markup=InlineKeyboardMarkup(keyboard))

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await safe_reply(update, "Thinking of a new idea for you...")
    try:
        prompt = "Give me a simple but interesting project idea for a beginner programmer. Explain it in 2-3 lines."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /idea) --- \n Error: {e}")
        await safe_reply(update, "Sorry, I couldn't think of an idea right now. Please try again later.")

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await safe_reply(update, "Please provide a concept to explain. Example: /explain Python lists")
        return
    
    concept = ' '.join(context.args)
    await safe_reply(update, f"Thinking... Let me explain '{concept}' for you.")
    try:
        prompt = f"Explain the concept of '{concept}' in a simple and easy-to-understand way for a beginner student."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /explain) --- \n Error: {e}")
        await safe_reply(update, f"Sorry, I couldn't explain '{concept}' right now. Please try again later.")

async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info_text = "For your privacy, a Telegram bot cannot clear your chat history.\n\nTo clear the chat, please tap the three dots (⋮) at the top right of this chat and select 'Clear history'."
    await safe_reply(update, info_text)

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await safe_reply(update, "Please write your feedback after the command. Example: /feedback This is a great bot!")
        return
    
    feedback_message = ' '.join(context.args)
    user_name = update.effective_user.username or update.effective_user.first_name
    logging.info(f"FEEDBACK Received from {user_name}: {feedback_message}")
    await safe_reply(update, "Thank you for your feedback! It has been sent to the developer.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID and update.effective_user.id == ADMIN_ID:
        user_count = len(daily_users.get(date.today(), set()))
        await safe_reply(update, f"📊 Today's unique active users: {user_count}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user.id)
    user_message = update.message.text
    try:
        logging.info(f"Generating content for: '{user_message}'")
        response = model.generate_content(user_message)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR --- \n Error Details: {e}")
        await safe_reply(update, "Sorry, I'm having an issue with my AI brain. The admin has been notified.")

# ==============================================================================
# --- NEW: Dummy Web Server to Keep Azure Happy ---
# ==============================================================================
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Hello! The Telegram Bot is running in the background."

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    flask_app.run(host='0.0.0.0', port=port)
    
# ==============================================================================
# --- Main Application Logic ---
# ==============================================================================
def run_bot():
    """Initializes and runs the Telegram bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register all command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("website", website))
    application.add_handler(CommandHandler("roadmaps", roadmaps))
    application.add_handler(CommandHandler("blog", blog))
    application.add_handler(CommandHandler("dsa", dsa))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(CommandHandler("idea", idea))
    application.add_handler(CommandHandler("explain", explain))
    application.add_handler(CommandHandler("clear", clear_chat))
    application.add_handler(CommandHandler("feedback", feedback))
    application.add_handler(CommandHandler("stats", stats))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot polling started...")
    application.run_polling()

if __name__ == '__main__':
    logging.info("Starting application...")

    web_server_thread = threading.Thread(target=run_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()
    logging.info("Web server started in a background thread.")

    run_bot()

