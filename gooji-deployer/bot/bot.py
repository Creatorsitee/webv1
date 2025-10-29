import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = "https://ojicloud.vercel.app" # Ganti dengan URL Vercel Anda setelah deploy
BOT_SECRET_KEY = os.getenv("BOT_SECRET_KEY")

async def signin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /signin command."""
    # Extract email from the command
    if not context.args:
        await update.message.reply_text("Please provide your email. Usage: /signin your.email@example.com")
        return
    
    email = context.args[0]
    
    # Simple email validation
    if "@" not in email or "." not in email:
        await update.message.reply_text("Invalid email format. Please try again.")
        return

    await update.message.reply_text("Processing your request...")

    # Call our backend API to register the user
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/register",
            json={"email": email},
            headers={"X-Bot-Secret-Key": BOT_SECRET_KEY}
        )
        response.raise_for_status() # Raise an exception for bad status codes
        
        data = response.json()
        if data.get("success"):
            username = data.get("username")
            password = data.get("password")
            reply_message = (
                f"✅ Signin successful!\n\n"
                f"Here are your account details to login on the Gooji website:\n\n"
                f"👤 Username/Email: {username}\n"
                f"🔑 Password: {password}\n\n"
                f"You can change your username and password after logging in.\n"
                f"Login here: {BACKEND_URL}"
            )
            await update.message.reply_text(reply_message)
        else:
            error_message = data.get("error", "An unknown error occurred.")
            await update.message.reply_text(f"❌ Registration failed: {error_message}")

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Could not connect to the server. Please try again later. Error: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ An unexpected error occurred: {e}")

def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("signin", signin))
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()