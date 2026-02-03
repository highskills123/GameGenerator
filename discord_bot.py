#!/usr/bin/env python3
"""
Simple Discord Bot using Aibase API
This bot allows users to generate code by sending commands in Discord
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if discord.py is available
try:
    import discord
    from discord.ext import commands
except ImportError:
    print("Error: discord.py not installed")
    print("Install it with: pip install discord.py")
    exit(1)

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
AIBASE_API_URL = os.getenv('AIBASE_API_URL', 'http://localhost:5000/api/translate')

if not DISCORD_TOKEN:
    print("Error: DISCORD_BOT_TOKEN not found in .env file")
    print("Please add: DISCORD_BOT_TOKEN=your_discord_bot_token")
    exit(1)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')


@bot.command(name='code', help='Generate code from natural language description')
async def generate_code(ctx, language: str = 'python', *, description: str = None):
    """
    Generate code from a description.
    
    Usage:
        !code python create a function that calculates fibonacci
        !code javascript create an async function to fetch data
        !code create a sorting algorithm (defaults to Python)
    """
    # Handle case where language might be part of description
    if description is None:
        # User didn't specify language, treat language as description
        description = language
        language = 'python'
    
    if not description:
        await ctx.send("❌ Please provide a description of the code you want to generate.")
        await ctx.send("Usage: `!code [language] <description>`")
        await ctx.send("Example: `!code python create a function that checks if a number is prime`")
        return
    
    # Send "thinking" message
    thinking_msg = await ctx.send("🤔 Generating code...")
    
    try:
        # Call Aibase API
        response = requests.post(
            AIBASE_API_URL,
            json={
                "description": description,
                "language": language.lower()
            },
            timeout=30
        )
        
        result = response.json()
        
        if result.get("success"):
            code = result["code"]
            lang = result["language"]
            
            # Delete thinking message
            await thinking_msg.delete()
            
            # Check if code is too long for Discord (2000 char limit)
            if len(code) > 1900:
                # Split into multiple messages or send as file
                await ctx.send(f"✅ Generated {lang.upper()} code (sent as file due to length):")
                
                # Create a file with the code
                filename = f"code.{_get_file_extension(lang)}"
                with open(filename, 'w') as f:
                    f.write(code)
                
                await ctx.send(file=discord.File(filename))
                os.remove(filename)
            else:
                await ctx.send(f"✅ Generated {lang.upper()} code:")
                await ctx.send(f"```{lang}\n{code}\n```")
        else:
            error = result.get("error", "Unknown error")
            await thinking_msg.edit(content=f"❌ Error: {error}")
            
    except requests.exceptions.Timeout:
        await thinking_msg.edit(content="❌ Request timed out. The code generation took too long.")
    except requests.exceptions.ConnectionError:
        await thinking_msg.edit(content="❌ Could not connect to Aibase API. Make sure the server is running.")
    except Exception as e:
        await thinking_msg.edit(content=f"❌ An error occurred: {str(e)}")


@bot.command(name='languages', help='List supported programming languages')
async def list_languages(ctx):
    """List all supported programming languages."""
    try:
        response = requests.get('http://localhost:5000/api/languages', timeout=5)
        result = response.json()
        
        languages = result.get('languages', [])
        lang_list = ', '.join(languages)
        
        await ctx.send(f"🔧 Supported languages ({result.get('count', 0)}):\n{lang_list}")
        
    except Exception as e:
        await ctx.send(f"❌ Error fetching languages: {str(e)}")


@bot.command(name='help_aibase', help='Show help for Aibase bot')
async def help_command(ctx):
    """Show detailed help information."""
    help_text = """
**Aibase Discord Bot - Help**

Generate code from natural language descriptions!

**Commands:**
• `!code [language] <description>` - Generate code
• `!languages` - List supported languages
• `!help_aibase` - Show this help message

**Examples:**
• `!code create a function that checks if a number is prime`
• `!code python create a binary search function`
• `!code javascript create an async function to fetch user data`
• `!code java create a class for a stack data structure`

**Supported Languages:**
Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin

**Tips:**
• Be specific in your descriptions for better results
• You can omit the language to default to Python
• Complex code may be sent as a file
    """
    await ctx.send(help_text)


def _get_file_extension(language):
    """Get file extension for a programming language."""
    extensions = {
        'python': 'py',
        'javascript': 'js',
        'typescript': 'ts',
        'java': 'java',
        'cpp': 'cpp',
        'csharp': 'cs',
        'go': 'go',
        'rust': 'rs',
        'php': 'php',
        'ruby': 'rb',
        'swift': 'swift',
        'kotlin': 'kt'
    }
    return extensions.get(language, 'txt')


def main():
    """Run the Discord bot."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  Aibase Discord Bot                          ║
╚══════════════════════════════════════════════════════════════╝

Starting bot...

Make sure:
1. Aibase API server is running (python api_server.py)
2. DISCORD_BOT_TOKEN is set in .env file

Bot commands:
  !code [language] <description>  - Generate code
  !languages                      - List supported languages
  !help_aibase                    - Show help

Press Ctrl+C to stop the bot
""")
    
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
    except Exception as e:
        print(f"\n\nError running bot: {e}")


if __name__ == '__main__':
    main()
