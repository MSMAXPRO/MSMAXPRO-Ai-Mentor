# ==============================================================================
# --- Required Libraries ---
# ==============================================================================
import logging
import os
import google.generativeai as genai
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask      # For Azure health check
import threading             # To run bot and web server together

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
    model = genai.GenerativeModel('gemini-1.0-pro') # Use 'gemini-1.0-pro'
    # --- END OF FIX ---
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
    # logging.info(f"Today's unique users: {len(daily_users[today])}") # Reduce log noise

async def safe_reply(update: Update, text: str, **kwargs):
    """Safely send replies and log any errors."""
    if not update or not update.message:
        logging.warning("safe_reply called with invalid update object.")
        return
    try:
        await update.message.reply_text(text, **kwargs)
    except Exception as e:
        logging.error(f"Telegram reply failed: {e}")

# ==============================================================================
# --- Command Handlers (Your Bot's Logic) ---
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        track_user(update.effective_user.id)
        user_name = update.effective_user.first_name
        welcome_message = (
            f"Hello {user_name}! Main aapka AI dost hoon.\n\n"
            "Coding, career, ya padhai se juda koi sawaal hai to pooch sakte ho!\n\n"
            "Please use this bot responsibly. Use /help to see all available commands."
        )
        await safe_reply(update, welcome_message)
    except Exception as e:
        logging.error(f"Error in /start: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        track_user(update.effective_user.id)
        help_text = (
            "Here are the available commands:\n\n"
            "/start - To start or restart the bot\n"
            "/help - Shows this list of commands\n"
            "/website - Visit our official website\n"
            "/roadmaps - Get a link to all career roadmaps\n"
            "/blog - Get a link to our blog posts\n"
            "/dsa - Get a random DSA practice problem\n"
            "/connect - Connect with the developer\n"
            "/idea - Get a new project idea\n"
            "/explain [concept] - Ask the AI to explain a concept\n"
            "/clear - Information on how to clear chat\n"
            "/feedback [message] - Send your feedback"
        )
        await safe_reply(update, help_text)
    except Exception as e:
        logging.error(f"Error in /help: {e}")

async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        track_user(update.effective_user.id)
        website_url = "https://codewithmsmaxpro.me"
        keyboard = [[InlineKeyboardButton("Visit Website", url=website_url)]]
        await safe_reply(update, "Click the button below to visit our official website!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logging.error(f"Error in /website: {e}")

async def roadmaps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        track_user(update.effective_user.id)
        roadmaps_url = "https://codewithmsmaxpro.me/roadmaps.html"
        keyboard = [[InlineKeyboardButton("View Roadmaps", url=roadmaps_url)]]
        await safe_reply(update, "Click the button below to explore all the career roadmaps!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logging.error(f"Error in /roadmaps: {e}")

async def blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        track_user(update.effective_user.id)
        blog_url = "https://codewithmsmaxpro.me/blog.html"
        keyboard = [[InlineKeyboardButton("Read Blog", url=blog_url)]]
        await safe_reply(update, "Click the button below to read our latest blog posts.", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logging.error(f"Error in /blog: {e}")

async def dsa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    track_user(update.effective_user.id) # Track usage for AI commands too
    await safe_reply(update, "Finding a good DSA problem for you...")
    try:
        prompt = "Give me a beginner-friendly DSA (Data Structures and Algorithms) practice problem. State the problem clearly, provide a hint, but do not provide the solution."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /dsa) --- \n Error: {e}")
        await safe_reply(update, "Sorry, I couldn't find a problem right now. Please try again later.")
        
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        track_user(update.effective_user.id)
        github_url = "https://github.com/MSMAXPRO"
        linkedin_url = "https://linkedin.com/in/your-linkedin-username" # <-- IMPORTANT: Update this URL
        keyboard = [
            [InlineKeyboardButton("GitHub", url=github_url)],
            [InlineKeyboardButton("LinkedIn", url=linkedin_url)]
        ]
        await safe_reply(update, "You can connect with me on these platforms:", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logging.error(f"Error in /connect: {e}")

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    track_user(update.effective_user.id)
    await safe_reply(update, "Thinking of a new idea for you...")
    try:
        prompt = "Give me a simple but interesting project idea for a beginner programmer. Explain it in 2-3 lines."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /idea) --- \n Error: {e}")
        await safe_reply(update, "Sorry, I couldn't think of an idea right now. Please try again later.")

async def explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    track_user(update.effective_user.id)
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
    try:
        track_user(update.effective_user.id)
        info_text = "For your privacy, a Telegram bot cannot clear your chat history.\n\nTo clear the chat, please tap the three dots (⋮) at the top right of this chat and select 'Clear history'."
        await safe_reply(update, info_text)
    except Exception as e:
        logging.error(f"Error in /clear: {e}")


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        track_user(update.effective_user.id)
        if not context.args:
            await safe_reply(update, "Please write your feedback after the command. Example: /feedback This is a great bot!")
            return
        
        feedback_message = ' '.join(context.args)
        user_name = update.effective_user.username or update.effective_user.first_name
        logging.info(f"FEEDBACK Received from {user_name}: {feedback_message}")
        await safe_reply(update, "Thank you for your feedback! It has been sent to the developer.")
    except Exception as e:
        logging.error(f"Error in /feedback: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID and update.effective_user.id == ADMIN_ID:
        try:
            user_count = len(daily_users.get(date.today(), set()))
            await safe_reply(update, f"📊 Today's unique active users: {user_count}")
        except Exception as e:
            logging.error(f"Error in /stats: {e}")
    else:
        logging.warning(f"Unauthorized access attempt for /stats by user {update.effective_user.id}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles non-command messages by sending them to the Gemini AI."""
    if not update.message or not update.message.text:
        logging.warning("Received an update without a message text.")
        return # Ignore updates without text

    track_user(update.effective_user.id)
    user_message = update.message.text
    try:
        logging.info(f"Attempting Gemini generation for: '{user_message}'")
        if 'model' not in globals():
             logging.error("FATAL: Gemini 'model' is not defined globally.")
             await safe_reply(update, "Internal configuration error. Please contact admin.")
             return

        response = model.generate_content(user_message) # Make the AI call
        await safe_reply(update, response.text)
        logging.info("Successfully sent Gemini AI response.")
    except Exception as e:
        logging.error(f"--- GEMINI ERROR ---")
        logging.error(f"Failed to get AI response for message: '{user_message}'")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Error Details: {e}")
        logging.error(f"--------------------")
        await safe_reply(update, "Sorry, I'm having an issue connecting to my AI brain right now. The admin has been notified.")

# ==============================================================================
# --- Dummy Web Server (For Azure Health Check) ---
# ==============================================================================
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    logging.info("Web server health check received.")
    return "Hello! The Telegram Bot is running in the background."

def run_web_server():
    port = int(os.environ.get("PORT", 8000))
    logging.info(f"Starting Flask web server on port {port}.")
    try:
        flask_app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logging.error(f"Web server failed to start: {e}")
    
# ==============================================================================
# --- Main Application Start ---
# ==============================================================================
def run_bot():
    """Initializes and runs the Telegram bot's polling mechanism."""
    try:
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
        
        logging.info("Bot polling starting...")
        application.run_polling() 
        logging.info("Bot polling stopped.") 

    except Exception as e:
        logging.critical(f"CRITICAL ERROR starting Telegram bot: {e}")
        exit() 

if __name__ == '__main__':
    logging.info("Starting application...")

    web_server_thread = threading.Thread(target=run_web_server)
    web_server_thread.daemon = True 
    web_server_thread.start()
    logging.info("Web server thread started.")

    run_bot()

