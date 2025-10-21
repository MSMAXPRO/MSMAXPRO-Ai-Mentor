# ==============================================================================
# --- Required Libraries ---
# ==============================================================================
import logging
import os
import google.generativeai as genai
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==============================================================================
# --- Secure Configuration ---
# ==============================================================================
# Load all secrets and configurations from environment variables set on the server (e.g., Azure).
# This keeps your code clean and your secrets safe.

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

try:
    # os.environ.get() returns a string. We MUST convert it to an integer for comparison.
    ADMIN_ID = int(os.environ.get('ADMIN_ID'))
except (ValueError, TypeError):
    logging.warning("ADMIN_ID environment variable not found or is not a valid number. Admin commands will be disabled.")
    ADMIN_ID = None

# ==============================================================================
# --- Initial Setup & Validation ---
# ==============================================================================

# Configure logging to monitor bot activity and errors.
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Critical check: If essential API keys are missing, the bot cannot run.
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.critical("CRITICAL ERROR: TELEGRAM_TOKEN or GEMINI_API_KEY environment variables are not set. Bot cannot start.")
    exit()

# Configure the Google AI model.
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    logging.info("Successfully configured Google AI (Gemini).")
except Exception as e:
    logging.error(f"FATAL: Could not configure Google AI. Error: {e}. Check if the API key is valid and enabled.")
    exit()

# In-memory dictionary for user tracking.
daily_users = {}

# ==============================================================================
# --- Helper Functions ---
# ==============================================================================

def track_user(user_id: int):
    """Tracks unique daily active users for the /stats command."""
    today = date.today()
    if today not in daily_users:
        daily_users[today] = set()
    daily_users[today].add(user_id)

async def safe_reply(update: Update, text: str, **kwargs):
    """A wrapper to safely send replies and log errors if they occur."""
    try:
        await update.message.reply_text(text, **kwargs)
    except Exception as e:
        logging.error(f"--- TELEGRAM REPLY FAILED --- \n Error: {e}")

# ==============================================================================
# --- Command Handlers ---
# ==============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message."""
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
        logging.error(f"Error in /start command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a list of available commands."""
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
        logging.error(f"Error in /help command: {e}")


async def website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a button to the main website."""
    try:
        track_user(update.effective_user.id)
        website_url = "https://codewithmsmaxpro.me"
        keyboard = [[InlineKeyboardButton("Visit Website", url=website_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_reply(update, "Click the button below to visit our official website!", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in /website command: {e}")

async def roadmaps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a button to the roadmaps page."""
    try:
        track_user(update.effective_user.id)
        roadmaps_url = "https://codewithmsmaxpro.me/roadmaps.html"
        keyboard = [[InlineKeyboardButton("View Roadmaps", url=roadmaps_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_reply(update, "Click the button below to explore all the career roadmaps!", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in /roadmaps command: {e}")

async def blog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a button to the blog page."""
    try:
        track_user(update.effective_user.id)
        blog_url = "https://codewithmsmaxpro.me/blog.html"
        keyboard = [[InlineKeyboardButton("Read Blog", url=blog_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_reply(update, "Click the button below to read our latest blog posts.", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in /blog command: {e}")

async def dsa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches a DSA problem from the AI."""
    track_user(update.effective_user.id)
    await safe_reply(update, "Finding a good DSA problem for you...")
    try:
        prompt = "Give me a beginner-friendly DSA (Data Structures and Algorithms) practice problem. State the problem clearly, provide a hint, but do not provide the solution."
        response = model.generate_content(prompt)
        await safe_reply(update, response.text)
    except Exception as e:
        logging.error(f"--- GEMINI ERROR (in /dsa) --- \n Error: {e}")
        await safe_reply(update, "Sorry, I couldn't find a problem right now. Please try again later.")
        
async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends social media links."""
    try:
        track_user(update.effective_user.id)
        github_url = "https://github.com/MSMAXPRO"
        linkedin_url = "https://linkedin.com/in/your-linkedin-username" # <-- IMPORTANT: Update this URL
        keyboard = [
            [InlineKeyboardButton("GitHub", url=github_url)],
            [InlineKeyboardButton("LinkedIn", url=linkedin_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_reply(update, "You can connect with me on these platforms:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error in /connect command: {e}")

async def idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches a project idea from the AI."""
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
    """Explains a concept using the AI."""
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
    """Informs the user on how to clear chat history."""
    try:
        track_user(update.effective_user.id)
        info_text = "For your privacy, a Telegram bot cannot clear your chat history.\n\nTo clear the chat, please tap the three dots (⋮) at the top right of this chat and select 'Clear history'."
        await safe_reply(update, info_text)
    except Exception as e:
        logging.error(f"Error in /clear command: {e}")

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receives feedback from a user."""
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
        logging.error(f"Error in /feedback command: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin-only command to get daily user stats."""
    # Check if ADMIN_ID is configured and if the user is the admin
    if ADMIN_ID and update.effective_user.id == ADMIN_ID:
        try:
            today = date.today()
            user_count = len(daily_users.get(today, set()))
            await safe_reply(update, f"📊 Today's unique active users: {user_count}")
        except Exception as e:
            logging.error(f"Error in /stats command: {e}")
    else:
        logging.warning(f"Unauthorized access attempt for /stats command by user {update.effective_user.id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles general text messages by sending them to the AI."""
    track_user(update.effective_user.id)
    user_message = update.message.text
    try:
        logging.info(f"Attempting to generate content for: '{user_message}'")
        response = model.generate_content(user_message)
        await safe_reply(update, response.text)
        logging.info("Successfully sent AI response.")
    except Exception as e:
        logging.error(f"--- DETAILED ERROR IN handle_message (GEMINI CALL) ---")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Error Details: {e}")
        logging.error(f"----------------------------------------------------")
        await safe_reply(update, "Sorry, I'm having trouble connecting to my AI brain right now. The admin has been notified.")

# ==============================================================================
# --- Main Bot Function ---
# ==============================================================================
def main() -> None:
    """Starts the bot and registers all handlers."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register all command handlers. This is where you tell the bot what commands to listen for.
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
    application.add_handler(CommandHandler("stats", stats)) # Admin command
    
    # Register a handler for all non-command text messages. This must be one of the last handlers added.
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot polling started...")
    # Start polling for updates from Telegram
    application.run_polling()

if __name__ == '__main__':
    main()