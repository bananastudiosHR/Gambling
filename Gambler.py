import discord
from discord.ext import commands, tasks
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import aiohttp
import asyncio
import json
import time
import datetime
import math
import os
import uuid
import cv2
import numpy as np
from wand.image import Image as WandImage
from wand.drawing import Drawing
import pymunk
import psutil
import platform

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

ADMIN_IDS = [978024161689608202, 962451361058930780]
DM_ID = 978024161689608202
PUBLIC_ACCESS = True

bot.remove_command('help')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_FILE = os.path.join(BASE_DIR, "user_data.json")
FRIENDS_FILE = os.path.join(BASE_DIR, "friends.json")

# Global Gambling Race State Tracking Variables
GLOBAL_GAME_COUNTER = 0
RACE_ACTIVE = False
RACE_WINNERS_BOOST = {} # Stores user_id: expiration_timestamp
RACE_SCORES = {}
USER_DATA = {}
LOBBIES = {}
FRIENDS = {}
SOLOBJ_GAMES = {}
MINE_GAMES = {}
VIEWPORT_SESSIONS = {}
USER_ACKNOWLEDGED_HELP = set()


LATEST_UPDATE = {
    "version": "v1.9.0",
    "date": "June 25, 2026",
    "time": "9:35 pm MST",
    "summary": "Fixed some commands not working, added some QoL (quality of life) updates to some commands, added new gambling commands and more!",
    "notes": "None",
}

UPDATE_LOGS = {
    "v1.9.0": """
**Detailed Changelog for v1.9.0:**

1. **Bug Fixes:**
- Fixed an issue causing `!bj` to not work.
- Fixed an issue causing `!bj` picture generation to draw random lines and made the playing cards look more realistic (still being worked on)
- Fixed a issue with some gifs/pictures not generating or working propperly.
- Fixed `!profile` command not showing correct information.

2. **QoL Updates:**
- Added a new `!help` command to provide a more user-friendly experience and a better understanding on how to use the bot.
- Added a embed to every command saying how to use the current command and what it does.
- Updated the `!profile` command to show your current debt.

3. **New Features:**
- Added a new badge and achievement system, you can see all your badges/achievements on your `!profile` and see all possible badges/achievements by doing `!rewards`.
- Added new items to `!shop` including new boosts.
- Added a passive mode, This stops you from being robbed from `!rob` but also makes it so you cant use `!rob`.

4. **Gambling Updates:**
- Added a new gambling command called `!dice <bet> <guess 1-6>` where you need to guess what number the dice will land on, guess correctly and you win 5x your bet, guess wrong and you lose 2x your bet.
- Added a new gambling command called `!keno <bet>` where you pick 20 different numbers (1-80) and the more matches you have with the bot, the more money you get.
- Added a new gambling command called `!coinflip <bet> <side>` where you guess what side the coin will land on, if you win you get 2x your bet, if you lose you lose your bet.
- Added a new gambling command called `!mines <bet> <amount of mines>` where you need to avoid the mines, the more you dig the higher multiplier you get on your bet.

5. **Command Updates:**
- Updated `!pay` so there is now a 2FA (two-factor authentication) system to prevent accidents, you can enable/disable this in your `!settings`.
- Updated `!settings` to add a toggle for `!pay` 2fa, a toggle for passive mode, and a toggle to who can `!pay` you.
- Updated `!bj` so there is now a "fast play" button after playing 3 rounds, fast play records what buttons you press when making a **multiplayer** lobby and instead of having to press the buttons over and over again you can simply press the fast play button to do it automatically.
- Added a `!feedback <your feedback>` command to give feedback to the bot developer.
- Added a `!survey` command to take a 15 question survey to give more feedback on the bot.
- Added a `!pyl` command to play a new game called "Press Your Luck" where you can win up to $2,000 per round.
- Added a `!pir` command to play a new game called "The Price is Right" where you can win up to $12,000 per round.
- Updated `!profile` command to re work leveling system

6. **Commands Coming Soon:**
- `!cups` - A game with 3 cups and 1 ball, at the start of all 3 rounds the ball will be under the middle cup, you need to follow the cup with the ball to win up to $20,000.
- `!poker` - A multiplayer poker game where you can play against other players and win up to $10,000 per round.
- `!limbo <bet> <target>` - Place a bet and pick a target, if it is equal to or higher then your number then you win your bet multiplied by your target, if you lose then you lose your bet multiplied by half your target
- `!pachinko <bet> <slots>` - Can you predict where the ball is going to land and win upwards to $100,000? (like plinko but you get to pick what slots are "good" slots)
- `!fantan <bet> <1-4>` - Can you predict how many objects are left over in the cup? To play the game, you pick how many objects you think will be under the cup, 1, 2, 3, or 4, then the dealer places a huge pile of small objects like buttons or beads on the table and covers a random amount with a cup, then the dealer removes the cup and groups all the objects in groubs of 4, how ever many objects are left will determin if you win or lose.

7. **Features Coming Soon:**
- None
"""
}

evaluate_multiplayer_dealer_resolutions = {}
update_all_player_boards_and_dms = {}
GLOBAL_SETTINGS = {"xp_enabled": True}

LOTTERY_POOL = 0
RACE_POT = 0
RACE_PARTICIPANTS = {} # user_id: profit_in_race
RACE_END_TIME = 0
DOUBLE_PROFIT_END = 0
DEBT_PAYOFF_END = 0

try:
    font_large = ImageFont.truetype("arial.ttf", 60)
    font_medium = ImageFont.truetype("arial.ttf", 40)
    font_xl = ImageFont.truetype("arial.ttf", 80)
except:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_xl = ImageFont.load_default()

# The available shop upgrades
SHOP_ITEMS = {
    "plinko_boost": {
        "name": "🔴 Plinko Multiplier Boost (+0.1x)",
        "description": "Permanently adds +0.1x to every single bucket on the Plinko board.",
        "cost": 50000,
        "max_level": 5
    },
    "slots_boost": {
        "name": "🎰 Slots Payout Boost (+5%)",
        "description": "Permanently boosts all winning slot machine payouts by 5%.",
        "cost": 75000,
        "max_level": 150
    },
    "xp_booster": {
        "name": "⚡ XP Boost (+25%)",
        "description": "Permanently increases all XP gained from playing games by 25%.",
        "cost": 25000,
        "max_level": 4
    },
    "vip_lounge": {
        "name": "💎 Permanet VIP",
        "description": "Unlocks permanent VIP status on your profile.",
        "cost": 500000,
        "max_level": 1
    },
    "bribe": {
        "name": "📜 Bribe",
        "description": "Removes $5,000 debt.",
        "cost": 1000,
        "max_level": 9999999999
    },
    "vip_1day": {
        "name": "💎 24-Hour VIP Pass",
        "description": "Grants VIP status for 24 hours, giving you access to exclusive features and a special profile badge.",
        "cost": 10000,
        "max_level": 9999999999
    },
    "vip_3day": {
        "name": "💎 3-Day VIP Pass",
        "description": "Grants VIP status for 3 days, giving you access to exclusive features and a special profile badge.",
        "cost": 25000,
        "max_level": 9999999999
    },
    "vip_7day": {
        "name": "💎 7-Day VIP Pass",
        "description": "Grants VIP status for 7 days, giving you access to exclusive features and a special profile badge.",
        "cost": 50000,
        "max_level": 9999999999
    },
    "vip_30day": {
        "name": "💎 30-Day VIP Pass",
        "description": "Grants VIP status for 30 days, giving you access to exclusive features and a special profile badge.",
        "cost": 150000,
        "max_level": 9999999999
    },
    "slots_winboost": {
        "name": "🎰 Slots Win Boost",
        "description": "Permanently increases your chances of hitting a winning combination on the slot machine by 0.5%. Stacks additively.",
        "cost": 20000,
        "max_level": 5
    },
    "roulette_boost": {
        "name": "🎡 Roulette Win Boost",
        "description": "Permanently increases your chances of winning on the roulette wheel by 0.5%. Stacks additively.",
        "cost": 20000,
        "max_level": 20
    },
    "bank_boost": {
        "name": "🏦 Store more in the bank",
        "description": "Permanently increases your bank storage limit by $10,000, allowing you to keep more of your winnings safe from theft and loss.",
        "cost": 10000,
        "max_level": 995
    }
}

BADGE_ITEMS = {
    "owner": {"name": "👑 Owner", "description": "The creator of the casino."},
    "staff": {"name": "🛡️ Staff", "description": "A trusted member of the casino staff."},
    "vip": {"name": "💎 VIP", "description": "A high-roller pass holder."},
    "og": {"name": "🌟 OG", "description": "An original member of the community."},
    "winner": {"name": "🏆 Jackpot Winner", "description": "Won a major server-wide lottery."}
}

ACHIEVEMENT_ITEMS = {
    "newbie": {"name": "🐣 Newbie", "description": "Play your first game."},
    "gambler": {"name": "🎲 Gambler", "description": "Play 50 games."},
    "gambling_god": {"name": "🧓 Gambling god", "description": "Play 200 games."},
    "high_roller": {"name": "💰 High Roller", "description": "Win a bet over $10,000."},
    "banker": {"name": "🏦 Banker", "description": "Reach $100,000 in the bank."},
    "debt_free": {"name": "🛡️ Debt Free", "description": "Pay off all loan shark debts."}
}

EVENTS_CONFIG = {
    "race": {
        "name": "Grand Derby Race",
        "description": "A 10-minute race where participants compete for the highest profit.",
        "interval": 5400,
        "duration": 600
    },
    "lottery": {
        "name": "Global Lottery",
        "description": "A recurring pot draw that is claimed by the system periodically.",
        "interval": 1800,
        "duration": 0
    },
    "interest": {
        "name": "Debt Interest",
        "description": "Calculates and applies compounding interest to user debts.",
        "interval": 600,
        "duration": 0
    }
}

SURVEY_QUESTIONS = [
    "Which game out of all 13 is your absolute favorite to play?",
    "What are your top 3 favorite games on the bot?",
    "If you had to remove 2 features or games from the bot (besides cooldowns), what would they be and why?",
    "What is the main reason that keeps you coming back to play?",
    "Do you prefer playing singleplayer against the house or multiplayer against other players?",
    "Have you run into any bugs that made a game feel unplayable or low quality, if so what is it and/or how do i reproduce it?",
    "On a scale of 1-5, how clear are the rules and instructions for each game?",
    "On a scale of 1-5, how hard is it to get rich? (1 = Way too easy, 5 = Impossible)",
    "Which game do you think is the worst right now and needs a complete rework?",
    "Do you prefer the bot sending visual images or pure text, or a mix of both",
    "What is your preferred way of interacting with the bot",
    "If you could add any new feature or game to the bot right now, what would it be and why?",
    "Which game command is the most annoying or hardest to type out?",
    "What device do you mainly use to play? (Desktop, Mobile, or Console)",
    "Do you have anything else? (a bug, a feature you want to see added or removed, etc)"
]

wyr_questions = [
    {"A": "Be able to fly at 30 MPH.", "B": "Be able to teleport but only to places you have already visited."},
    {"A": "Have telekinesis (moving things with your mind)", "B": "Be able to read minds but only of people you are in close proximity to."},
    {"A": "Be able to time travel but only to your own past", "B": "Be able to time travel but only to your own future."},
    {"A": "Have the ability to become invisible", "B": "Have the ability to become invincible for 10 seconds at a time."},
    {"A": "Be able to control the weather", "B": "Be able to communicate with animals."},
    {"A": "Be able to breathe underwater", "B": "Be able to survive in space without a suit for 10 minutes."},
    {"A": "Be able to speak any language fluently", "B": "Be able to understand any language perfectly."},
    {"A": "Have a completely photographic memory.", "B": "Be able to instantly learn any physical skill."},
    {"A": "Never have to stand in a line again", "B": "Never have to sit in traffic again."},
    {"A": "Give up all social media forever", "B": "Give up streaming movies and TV forever."},
    {"A": "Have every traffic light you approach turn green", "B": "Always find the perfect parking spot immediately."},
    {"A": "Have your internet history exposed to your boss", "B": "Have your inner thoughts broadcasted out loud for a week."},
    {"A": "Sneeze forcefully everytime someone says your name", "B": "Hiccup loudly every time you start speaking."},
    {"A": "Get your dream job but get paid below minimum wage", "B": "Get the opposite of your dream job but get paid 100k everytime you almost get fired (if you get fired you lose it all)"},
]

quiz_questions = [
    {
        "question": "What game does the developer like the most?",
        "options": ["blackjack", "slots", "plinko", "coinflip"],
        "correct": "blackjack",
        "reward": 1000
    },
    {
        "question": "When was the bot made?",
        "options": ["Jannuary 16, 2026", "June 19, 2026", "June 16, 2026", "July 16, 2026"],
        "correct": "June 16, 2026",
        "reward": 100
    },
    {
        "question": "Is the developer a morning person or a night owl?",
        "options": ["Morning person", "Night owl"],
        "correct": "Night owl",
        "reward": 2000
    },
    {
        "question": "What was the best glitch the bot has had so far?",
        "options": ["Slots gif glitching", "Images not loading", "", ""],
        "correct": "Slots gif glitching",
        "reward": 500
    },
    {
        "question": "If the developer is completely ghosting the server, what are they most likely doing?",
        "options": ["Coding", "playing a game", "Watching videos", "Sleeping"],
        "correct": "Coding",
        "reward": 5000
    },
]

PRESS_YOUR_LUCK_BOARD = [
    {"type": "cash", "val": 300, "disp": "💵 300"},
    {"type": "cash", "val": 500, "disp": "💵 500"},
    {"type": "cash", "val": 750, "disp": "💵 750"},
    {"type": "cash", "val": 1000, "disp": "💵 1,000"},
    {"type": "cash", "val": 1500, "disp": "💵 1,500"},
    {"type": "cash", "val": 2000, "disp": "💵 2,000"},
    {"type": "whammy", "val": 0, "disp": "👹 WHAMMY!"},
    {"type": "whammy", "val": 0, "disp": "👹 WHAMMY!"}
]

PRICE_IS_RIGHT_ITEMS = [
    {"name": "Gaming PC Setup (RTX 5090, 64GB RAM, 4K OLED Monitor)", "min": 3500, "max": 5500, "actual": 4850},
    {"name": "Luxury Swiss Chronograph Automatic Watch", "min": 6000, "max": 9500, "actual": 7400},
    {"name": "Designer Italian Leather Sectional Sofa", "min": 2000, "max": 4500, "actual": 3200},
    {"name": "Premium Electric Smart Scooter", "min": 800, "max": 1800, "actual": 1250},
    {"name": "Professional mirrorless Camera with 24-70mm Lens", "min": 2500, "max": 4000, "actual": 3150},
    {"name": "Ultra-Thin 85\" 8K QLED Smart Television", "min": 3000, "max": 6000, "actual": 4499},
    {"name": "High-End All-Inclusive 7-Day Maldives Resort Pass", "min": 7000, "max": 12000, "actual": 9800}
]

ITEMS_DATABASE = {
    "loan_bribe": {
        "name": "💰 Loan Bribe",
        "description": "Allows you to pay off your debt completely.",
        "rarity": "Rare",
        "usable": True,
        "cost": 50000
    },
    "anti_rob": {
        "name": "🔄 Anti-Rob Uno Reverse",
        "description": "If used, it pulls an absolute uno reverse card and steals from the person attempting to rob you.",
        "rarity": "Common",
        "usable": True,
        "cost": 5000
    },
    "damned_soul": {
        "name": "👻 Damned Soul",
        "description": "Prevents you from being robbed entirely, but decreases your chances of winning other games.",
        "rarity": "Unique",
        "usable": True,
        "cost": 669000000
    }
}

AUCTION_HOUSE = {}
AUCTION_BLACKLIST = set()

SKILL_TREE = {
    # =========================================================================
    # CENTER ANCHOR: THE ORIGIN
    # =========================================================================
    "nexus": {
        "name": "NEXUS CORE",
        "desc": "The foundational anchor of your progression matrix.",
        "cost": 0,
        "max_level": 1,
        "prereqs": [],
        "icon": "nexus",
        "pos": (500, 500)
    },

    # =========================================================================
    # NORTH BRANCH: BLACKJACK STRATEGY (Upward from center)
    # =========================================================================
    "double_down": {
        "name": "DOUBLE DOWN",
        "desc": "Unlocks critical Blackjack Double Down choice mechanisms.",
        "cost": 5,
        "max_level": 1,
        "prereqs": ["nexus"],
        "icon": "double_down",
        "pos": (500, 240)
    },
    "lucky_seven": {
        "name": "LUCKY SEVENS",
        "desc": "+5% Hitting bonus payout calculations per tier level.",
        "cost": 3,
        "max_level": 3,
        "prereqs": ["double_down"],
        "icon": "lucky_seven",
        "pos": (240, 120)
    },
    "high_roller": {
        "name": "HIGH ROLLER",
        "desc": "Raises default table maximum bet limit thresholds.",
        "cost": 4,
        "max_level": 2,
        "prereqs": ["double_down"],
        "icon": "high_roller",
        "pos": (760, 120)
    },
    "split_decision": {
        "name": "SPLIT DECISION",
        "desc": "Allows splitting matching pairs into two separate playable hands.",
        "cost": 6,
        "max_level": 1,
        "prereqs": ["lucky_seven"],
        "icon": "split_hand",
        "pos": (100, 0)
    },
    "insurance_policy": {
        "name": "INSURANCE POLICY",
        "desc": "Unlocks Dealer Insurance options and cuts insurance costs by 10% per tier.",
        "cost": 3,
        "max_level": 3,
        "prereqs": ["high_roller"],
        "icon": "shield_bet",
        "pos": (900, 0)
    },
    "card_shark": {
        "name": "CARD SHARK ACTIVE",
        "desc": "Enables preview of the dealer's next shoe card.",
        "cost": 10,
        "max_level": 1,
        "prereqs": ["lucky_seven", "high_roller"],
        "icon": "card_shark",
        "pos": (500, -20)
    },
    "sleight_of_hand": {
        "name": "SLEIGHT OF HAND",
        "desc": "Once per shoe, swap your worst card with a random draw from the deck.",
        "cost": 15,
        "max_level": 1,
        "prereqs": ["card_shark"],
        "icon": "magic_hand",
        "pos": (500, -180)
    },

    # =========================================================================
    # WEST BRANCH: COINFLIP STREAKS & RISK (Leftward from center)
    # =========================================================================
    "coinflip_mastery": {
        "name": "COINFLIP MASTER",
        "desc": "Unlocks subtle streak multipliers for Coinflip games.",
        "cost": 3,
        "max_level": 3,
        "prereqs": ["nexus"],
        "icon": "coin_gold",
        "pos": (200, 500)
    },
    "edge_case": {
        "name": "EDGE CASE",
        "desc": "Adds a 0.5% chance per tier for a coin to land on its side, paying out 10x.",
        "cost": 5,
        "max_level": 3,
        "prereqs": ["coinflip_mastery"],
        "icon": "coin_edge",
        "pos": (0, 380)
    },
    "momentum_shift": {
        "name": "MOMENTUM SHIFT",
        "desc": "Losing a coinflip increases your next coinflip win payout by +15%.",
        "cost": 6,
        "max_level": 2,
        "prereqs": ["coinflip_mastery"],
        "icon": "arrow_trend",
        "pos": (0, 620)
    },
    "perfect_call": {
        "name": "PERFECT CALLER",
        "desc": "Reaching a 5x Coinflip streak instantly rewards a massive bonus token bundle.",
        "cost": 12,
        "max_level": 1,
        "prereqs": ["edge_case", "momentum_shift"],
        "icon": "streak_fire",
        "pos": (-160, 500)
    },

    # =========================================================================
    # EAST BRANCH: SLOT MACHINES & VARIANCE (Rightward from center)
    # =========================================================================
    "slots_efficiency": {
        "name": "SLOT MACHINE REELS",
        "desc": "Slightly reduces row-match variance for Slot matches.",
        "cost": 4,
        "max_level": 2,
        "prereqs": ["nexus"],
        "icon": "slots_lever",
        "pos": (800, 500)
    },
    "wild_card_reels": {
        "name": "WILD CARD REELS",
        "desc": "Introduces a 'Wild' icon to the slot pool that substitutes for any symbol.",
        "cost": 6,
        "max_level": 1,
        "prereqs": ["slots_efficiency"],
        "icon": "wild_star",
        "pos": (1000, 380)
    },
    "cherry_bomb": {
        "name": "CHERRY BOMB METER",
        "desc": "Every dead/losing slot spin charges a meter; when full, forces a win.",
        "cost": 5,
        "max_level": 3,
        "prereqs": ["slots_efficiency"],
        "icon": "cherry_bomb",
        "pos": (1000, 620)
    },
    "jackpot_fever": {
        "name": "JACKPOT FEVER",
        "desc": "Permanently boosts the ultimate Grand Jackpot payout value by 25%.",
        "cost": 14,
        "max_level": 1,
        "prereqs": ["wild_card_reels", "cherry_bomb"],
        "icon": "jackpot_crown",
        "pos": (1180, 500)
    },

    # =========================================================================
    # SOUTH BRANCH: DICE & REWARD WHEELS (Downward from center)
    # =========================================================================
    "dice_manipulation": {
        "name": "LOADED DICE TACTICS",
        "desc": "Unlocks roll-reroll mechanics once per complete daily cycle.",
        "cost": 6,
        "max_level": 1,
        "prereqs": ["nexus"],
        "icon": "dice_loaded",
        "pos": (500, 760)
    },
    "snake_eyes": {
        "name": "SNAKE EYES RECOVERY",
        "desc": "Rolling a double 1 converts the catastrophic loss into a full bet refund.",
        "cost": 4,
        "max_level": 2,
        "prereqs": ["dice_manipulation"],
        "icon": "dice_one",
        "pos": (240, 880)
    },
    "wheel_fortune": {
        "name": "FORTUNE WHEEL",
        "desc": "Unlocks access to spin the hidden high-tier reward wheel.",
        "cost": 5,
        "max_level": 2,
        "prereqs": ["dice_manipulation"],
        "icon": "wheel_spins",
        "pos": (500, 1020)
    },
    "overdrive_spin": {
        "name": "OVERDRIVE SPIN",
        "desc": "Allows spending double points on the wheel to completely erase the 'Bankruptcy' segment.",
        "cost": 8,
        "max_level": 1,
        "prereqs": ["wheel_fortune"],
        "icon": "wheel_fire",
        "pos": (500, 1180)
    },

    # =========================================================================
    # OUTER ENDGAME OUTER EDGE CRUST: HYBRID CAPSTONES
    # =========================================================================
    "pit_boss_nemesis": {
        "name": "PIT BOSS NEMESIS",
        "desc": "Passive: All betting games across the entire bot have their table house edge reduced by 2.5%.",
        "cost": 25,
        "max_level": 1,
        "prereqs": ["sleight_of_hand", "jackpot_fever"],
        "icon": "boss_skull",
        "pos": (900, -100)
    },
    "infinite_bankroll": {
        "name": "THE SYNDICATE BANKROLL",
        "desc": "Every winning bet of any kind has a 5% chance to trigger an instant double payout.",
        "cost": 30,
        "max_level": 1,
        "prereqs": ["perfect_call", "overdrive_spin"],
        "icon": "infinity_vault",
        "pos": (100, 1000)
    }
}




ACTIVE_EVENT_STATES = {
    "race": {"end_time": 0, "participants": {}},
    "lottery": {"last_run": 0},
    "interest": {"last_run": 0}
}
def load_all_data():
    global USER_DATA, FRIENDS
    
    if not os.path.exists(USER_DATA_FILE):
        USER_DATA = {}
    else:
        try:
            with open(USER_DATA_FILE, "r") as f:
                data = json.load(f)
                USER_DATA = {int(k): v for k, v in data.items() if k.isdigit()}
        except Exception as e:
            print(f"CRITICAL ERROR loading data: {e}")
            USER_DATA = {}

    # --- Load FRIENDS ---
    if not os.path.exists(FRIENDS_FILE):
        FRIENDS = {}
    else:
        try:
            with open(FRIENDS_FILE, "r") as f:
                data = json.load(f)
                FRIENDS = {int(k): v for k, v in data.items() if k.isdigit()}
        except Exception as e:
            print(f"CRITICAL ERROR loading friends: {e}")
            FRIENDS = {}

file_lock = asyncio.Lock()

async def save_user_data():
    """Saves the current USER_DATA state safely using an async lock and atomic write."""
    async with file_lock:
        try:
            # Create a string-keyed copy to ensure JSON compatibility
            export_data = {str(k): v for k, v in USER_DATA.items()}
            temp_file = USER_DATA_FILE + ".tmp"
            
            # Write to temporary file
            with open(temp_file, "w") as f:
                json.dump(export_data, f, indent=4)
            
            # Atomically replace the real file (prevents file corruption)
            os.replace(temp_file, USER_DATA_FILE)
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to save USER_DATA: {e}")

async def save_friends_data():
    """Saves the current FRIENDS state safely using an async lock and atomic write."""
    async with file_lock:
        try:
            export_data = {str(k): v for k, v in FRIENDS.items()}
            temp_file = FRIENDS_FILE + ".tmp"
            
            with open(temp_file, "w") as f:
                json.dump(export_data, f, indent=4)
            
            os.replace(temp_file, FRIENDS_FILE)
        except Exception as e:
            print(f"Error saving FRIENDS: {e}")

async def get_user_rank(user_id: int) -> str:
    await ensure_user(user_id) # Added await
    if USER_DATA[user_id]["rank_override"]:
        return USER_DATA[user_id]["rank_override"]
    
    xp = USER_DATA[user_id]["xp"]
    if xp >= 200:
        return "Advanced"
    elif xp >= 50:
        return "Intermediate"
    else:
        return "Beginner"

async def add_xp(user_id: int, amount: int):
    if not GLOBAL_SETTINGS["xp_enabled"]:
        return
    await ensure_user(user_id) # Added await
    USER_DATA[user_id]["xp"] += amount

async def ensure_user(user_id: int):
    """Ensures a user has a valid profile structure and pushes updates immediately to files."""
    mutated = False
    
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {
            "balance": 5000, 
            "total_games": 0, 
            "wins": 0, 
            "net_earnings": 0,
            "xp": 0,
            "rank_override": None,
            "strikes": 0,
            "trespassed": False,
            "settings": {"dm_notifications": True, "public_profile": True, "transfer_2fa": False, "passive_mode": False},
            "daily_cost": 1000,
            "vip_status": False,
            "scratch_history": 0,
            "crash_history": 0,
            "last_command_timestamp": 0.0,
            "loan_debt": 0,
            "has_ever_had_debt": False,
            "upgrades": {"plinko_boost": 0, "slots_boost": 0, "xp_booster": 0, "vip_lounge": 0, "slots_winboost": 0, "roulette_boost": 0, "bank_boost": 0},
            "vault": 0,
            "badges": [],
            "achievements": [],
            "streak": 0,
            "last_daily_timestamp": 0.0,
            "last_interest_time": 0.0,
            "last_lottery_time": 0.0,
            "last_race_time": 0.0,
            "last_rob_time": 0.0,
            "flags": [],
            "history_actions": [],
            "moderation_history": [],
            "wyr_cooldowns": [],
            "private_inventory": "everyone",
            "friends": [],
            "inventory": {},
            "reputation": 0,
            "debt": 0,

        }
        mutated = True
    
    if "flags" not in USER_DATA[user_id]:
        USER_DATA[user_id]["flags"] = []
        mutated = True
    
    if "moderation_history" not in USER_DATA[user_id]:
        USER_DATA[user_id]["moderation_history"] = []
        mutated = True

    if "history_actions" not in USER_DATA[user_id]:
        USER_DATA[user_id]["history_actions"] = []
        mutated = True

    if "wyr_cooldowns" not in USER_DATA[user_id]:
        USER_DATA[user_id]["wyr_cooldowns"] = []
        mutated = True

    if "private_inventory" not in USER_DATA[user_id]:
        USER_DATA[user_id]["private_inventory"] = "everyone"
        mutated = True

    if "friends" not in USER_DATA[user_id]:
        USER_DATA[user_id]["friends"] = []
        mutated = True

    if "inventory" not in USER_DATA[user_id]:
        USER_DATA[user_id]["inventory"] = {}
        mutated = True
        
    if user_id not in FRIENDS:
        FRIENDS[user_id] = {"requests_in": {}, "requests_out": {}}
        await save_friends_data()
    
    if "reputation" not in USER_DATA:
        USER_DATA[user_id]["Reputation"] = []
        mutated = True
        
    if mutated:
        await save_user_data()

async def check_flagged_win(user_id, amount, game_name, ctx):
    await ensure_user(user_id)
    if USER_DATA[user_id]["flags"]:
        try:
            staff_member = await bot.fetch_user(DM_ID)
            reasons = ", ".join(USER_DATA[user_id]["flags"])
            dm_embed = discord.Embed(title="🚩 Flagged User Activity", color=0xFF0000)
            dm_embed.add_field(name="User", value=f"<@{user_id}>", inline=False)
            dm_embed.add_field(name="Action", value=f"Won {amount} in {game_name}", inline=False)
            dm_embed.add_field(name="Current Flags", value=reasons, inline=False)
            await staff_member.send(embed=dm_embed)
        except:
            pass

async def check_milestones(user_id: int):
    """Checks USER_DATA against defined milestones and grants achievements."""
    await ensure_user(user_id)
    user_data = USER_DATA[user_id]
    awarded_list = user_data.get("achievements", [])
    
    mutated = False
    newly_awarded = []

    # Initialize tracking flag for debt if it doesn't exist
    if "has_ever_had_debt" not in user_data:
        user_data["has_ever_had_debt"] = False
        mutated = True
    
    # Update tracking flag if they currently have debt
    if user_data.get("loan_debt", 0) > 0:
        user_data["has_ever_had_debt"] = True
        mutated = True

    # Newbie - Play your first game.
    if "newbie" not in awarded_list and user_data["total_games"] >= 1:
        newly_awarded.append("newbie")
        mutated = True

    # Gambler - Play 50 games.
    if "gambler" not in awarded_list and user_data["total_games"] >= 50:
        newly_awarded.append("gambler")
        mutated = True

    # High Roller - reach $10,000 balance
    if "high_roller" not in awarded_list and user_data["balance"] >= 10000:
        newly_awarded.append("high_roller")
        mutated = True

    # Banker - Reach $100,000 in the vault.
    if "banker" not in awarded_list and user_data["vault"] >= 100000:
        newly_awarded.append("banker")
        mutated = True

    # Debt Free - Pay off all loan shark debts.
    # Requirement: Must have had debt (>0 in the past) and currently have 0 debt.
    if "debt_free" not in awarded_list and user_data.get("has_ever_had_debt", False) and user_data.get("loan_debt", 0) == 0:
        newly_awarded.append("debt_free")
        mutated = True

    if mutated:
        user_data["achievements"].extend(newly_awarded)
        USER_DATA[user_id]["achievements"] = list(set(user_data["achievements"]))
        await save_user_data()
        return newly_awarded
        
    return []

@tasks.loop(minutes=2)
async def event_status_updater():
    guild = bot.get_guild(1316963497099268096)
    if not guild: return
    channel = guild.get_channel(1519106214078709781)
    if not channel: return
    
    global LOTTERY_POOL, RACE_END_TIME
    embed = discord.Embed(title="⏰ Live Event Status Updates", color=0x3b82f6)
    
    if RACE_END_TIME > time.time():
        rem = int(RACE_END_TIME - time.time())
        embed.add_field(name=f"🏁 {EVENTS_CONFIG['race']['name']}", value=f"Active! Ends in {rem//60}m {rem%60}s.", inline=False)
    
    pot_val = f"${LOTTERY_POOL:,}" if LOTTERY_POOL > 0 else "Empty"
    embed.add_field(name=f"🎟️ {EVENTS_CONFIG['lottery']['name']}", value=f"Current Pot: {pot_val}", inline=False)
        
    await channel.send(embed=embed)

async def fetch_avatar_image(user: discord.Member) -> Image.Image:
    avatar_url = user.display_avatar.with_format("png").with_size(512).url
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    avatar_bytes = await resp.read()
                    avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
                    return avatar_img.resize((400, 400))
    except:
        pass
    fallback = Image.new("RGBA", (400, 400), "#5865F2")
    f_draw = ImageDraw.Draw(fallback)
    f_draw.ellipse([(40, 40), (360, 360)], fill="#ffffff")
    return fallback

def generate_balance_image(username, balance, width=2000, height=800):
    img = Image.new("RGB", (2000, 800), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(40, 40), (1960, 760)], outline="#eab308", width=16)
    draw.rectangle([(64, 64), (1936, 736)], outline="#1e293b", width=8)
    draw.text((140, 120), "MY PERSONAL WALLET", fill="#94a3b8", font=font_medium)
    draw.text((140, 220), f"ACCOUNT OWNER: {username.upper()}", fill="#ffffff", font=font_large)
    draw.line([(140, 360), (1860, 360)], fill="#eab308", width=8)
    draw.text((140, 420), "AVAILABLE CASH BALANCE", fill="#94a3b8", font=font_medium)
    draw.text((140, 520), f"${balance:,} USD", fill="#22c55e", font=font_xl)
    if img.size != (width, height):
        img = img.resize((width, height))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="balance.png")

def draw_card(draw, card, x, y, width=300, height=420, hidden=False):
    if hidden:
        draw.rectangle([(x, y), (x + width, y + height)], fill="#b22222", outline="#ffffff", width=8)
        draw.text((x + 40, y + 160), "HIDDEN", fill="#ffffff", font=font_large)
        return
    draw.rectangle([(x, y), (x + width, y + height)], fill="#ffffff", outline="#000000", width=8)
    color = "#ff0000" if card[1] in ["♦", "♥"] else "#000000"
    rank, suit = card
    draw.text((x + 20, y + 20), rank, fill=color, font=font_large)
    draw.text((x + 20, y + 80), suit, fill=color, font=font_large)
    draw.text((x + width - 70, y + height - 140), rank, fill=color, font=font_large)
    draw.text((x + width - 70, y + height - 80), suit, fill=color, font=font_large)
    draw.text((x + 70, y + 120), rank, fill=color, font=font_xl)

def generate_blackjack_image(player_cards, dealer_cards, show_dealer_hidden=False, width=2400, height=1200):
    img = Image.new("RGB", (2400, 1200), "#0f5132")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(40, 40), (2360, 560)], outline="#d4af37", width=12)
    draw.rectangle([(40, 640), (2360, 1160)], outline="#d4af37", width=12)
    draw.text((80, 80), "DEALER HAND", fill="#ffffff", font=font_large)
    draw.text((80, 680), "PLAYER HAND", fill="#ffffff", font=font_large)
    x_offset = 400
    for i, card in enumerate(dealer_cards):
        is_hidden = (i == 1 and not show_dealer_hidden)
        draw_card(draw, card, x_offset, 120, width=300, height=420, hidden=is_hidden)
        x_offset += 360
    x_offset = 400
    for card in player_cards:
        draw_card(draw, card, x_offset, 720, width=300, height=420, hidden=False)
        x_offset += 360
    if img.size != (width, height):
        img = img.resize((width, height))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="blackjack.png")

def bj_text_size(draw, text, font):
    try:
        bbox = draw.textbbox((0, 0), str(text), font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        return draw.textsize(str(text), font=font)

def bj_centered_text(draw, box, text, fill, font):
    x1, y1, x2, y2 = box
    tw, th = bj_text_size(draw, text, font)
    draw.text((x1 + ((x2 - x1 - tw) / 2), y1 + ((y2 - y1 - th) / 2)), str(text), fill=fill, font=font)

def draw_blackjack_chip(draw, x, y, amount, fill="#d4af37"):
    draw.ellipse([(x, y), (x + 120, y + 120)], fill=fill, outline="#fff7ed", width=8)
    draw.ellipse([(x + 18, y + 18), (x + 102, y + 102)], outline="#7c2d12", width=5)
    bj_centered_text(draw, (x + 12, y + 35, x + 108, y + 85), f"${amount}", "#111827", font_medium)

def draw_blackjack_status_pill(draw, x, y, label, fill):
    try:
        draw.rounded_rectangle([(x, y), (x + 270, y + 76)], radius=26, fill=fill, outline="#f8fafc", width=3)
    except:
        draw.rectangle([(x, y), (x + 270, y + 76)], fill=fill, outline="#f8fafc", width=3)
    bj_centered_text(draw, (x, y + 4, x + 270, y + 72), label, "#ffffff", font_medium)

def draw_blackjack_card(draw, card, x, y, width=240, height=340, hidden=False):
    try:
        draw.rounded_rectangle([(x + 12, y + 16), (x + width + 12, y + height + 16)], radius=28, fill="#06281b")
        draw.rounded_rectangle([(x, y), (x + width, y + height)], radius=28, fill="#f8fafc", outline="#111827", width=7)
    except:
        draw.rectangle([(x + 12, y + 16), (x + width + 12, y + height + 16)], fill="#06281b")
        draw.rectangle([(x, y), (x + width, y + height)], fill="#f8fafc", outline="#111827", width=7)
    if hidden:
        try:
            # Base dark red background drawn first
            draw.rounded_rectangle([(x + 14, y + 14), (x + width - 14, y + height - 14)], radius=22, fill="#7f1d1d")
        except:
            draw.rectangle([(x + 14, y + 14), (x + width - 14, y + height - 14)], fill="#7f1d1d")
        
        pad = 14
        min_x = x + pad
        max_x = x + width - pad
        min_y = y + pad
        max_y = y + height - pad
        
        # Stripes loop drawn second using a more vibrant visible color (#cc1111)
        for offset in range(0, (width + height), 35):
            x1 = min_x + offset
            y1 = min_y
            
            if x1 > max_x:
                y1 = min_y + (x1 - max_x)
                x1 = max_x
                
            x2 = min_x
            y2 = min_y + offset
            
            if y2 > max_y:
                x2 = min_x + (y2 - max_y)
                y2 = max_y
                
            if x1 >= min_x and x1 <= max_x and y1 >= min_y and y1 <= max_y and x2 >= min_x and x2 <= max_x and y2 >= min_y and y2 <= max_y:
                if x1 != x2 or y1 != y2:
                    draw.line([(x1, y1), (x2, y2)], fill="#cc1111", width=14)
                    
        # White ring/mask to perfectly clean up and cover up line bleed onto the white card face area
        try:
            draw.rounded_rectangle([(x + 10, y + 10), (x + width - 10, y + height - 10)], radius=24, fill=None, outline="#f8fafc", width=5)
        except:
            draw.rectangle([(x + 10, y + 10), (x + width - 10, y + height - 10)], fill=None, outline="#f8fafc", width=5)

        # Yellow and gold highlights drawn last so they sit cleanly on top of everything
        try:
            draw.rounded_rectangle([(x + 14, y + 14), (x + width - 14, y + height - 14)], radius=22, fill=None, outline="#fbbf24", width=5)
        except:
            draw.rectangle([(x + 14, y + 14), (x + width - 14, y + height - 14)], fill=None, outline="#fbbf24", width=5)
            
        bj_centered_text(draw, (x + 20, y + 115, x + width - 20, y + 225), "CASINO", "#ffffff", font_medium)
        return
    rank, suit = card
    suit_color = "#dc2626" if suit in ["\u2665", "\u2666"] else "#111827"
    corner_font = font_large
    center_font = font_xl
    
    # Left Corner Index (Rank over Suit)
    draw.text((x + 18, y + 16), str(rank), fill=suit_color, font=corner_font)
    rw_top, rh_top = bj_text_size(draw, str(rank), corner_font)
    draw.text((x + 18 + (rw_top // 2) - 10, y + 20 + rh_top), str(suit), fill=suit_color, font=corner_font)
    
    # Right Corner Index (Rank over Suit)
    rw_bot, rh_bot = bj_text_size(draw, str(rank), corner_font)
    sw_bot, sh_bot = bj_text_size(draw, str(suit), corner_font)
    draw.text((x + width - 18 - rw_bot, y + height - 34 - rh_bot - sh_bot), str(rank), fill=suit_color, font=corner_font)
    draw.text((x + width - 18 - rw_bot + (rw_bot // 2) - 10, y + height - 28 - sh_bot), str(suit), fill=suit_color, font=corner_font)
    
    # Expanded internal layout margins matching the larger 240x340 space to maximize separation
    inner_left = x + 72
    inner_right = x + width - 72
    inner_center_x = x + (width // 2)
    
    inner_top = y + 75
    inner_bottom = y + height - 75
    inner_center_y = y + (height // 2)
    
    # Proportional rows for high card counts (6, 7, 8, 9, 10) to spread them out beautifully
    row_top_inner = y + 125
    row_bottom_inner = y + height - 125

    # Determine pip grid layout arrangement by parsing rank matching
    pips = []
    try:
        num_rank = int(rank)
    except ValueError:
        if rank in ["A", "1"]:
            num_rank = 1
        else:
            num_rank = 0  # Face cards

    # Dynamic scaling: Sets specialized font boundaries across individual density tiers
    if num_rank == 1:
        pip_font = center_font   # Massive scale for single pip cards
    elif num_rank <= 3:
        pip_font = font_large    # Large scale for low count pips
    elif num_rank <= 5:
        pip_font = font_medium   # Medium scale to allow spacing comfort
    elif num_rank <= 10:
        pip_font = corner_font   # Clean index scale for heavy count cards to block any close crowding
    else:
        pip_font = center_font   # Single giant centered asset for face cards (J, Q, K)

    if num_rank == 1:
        pips = [(inner_center_x, inner_center_y)]
    elif num_rank == 2:
        pips = [(inner_center_x, inner_top), (inner_center_x, inner_bottom)]
    elif num_rank == 3:
        pips = [(inner_center_x, inner_top), (inner_center_x, inner_center_y), (inner_center_x, inner_bottom)]
    elif num_rank == 4:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 5:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_center_x, inner_center_y), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 6:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, inner_center_y), (inner_right, inner_center_y), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 7:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, inner_center_y), (inner_right, inner_center_y), 
                (inner_center_x, (inner_top + inner_center_y) // 2), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 8:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, row_top_inner), (inner_right, row_top_inner), 
                (inner_left, row_bottom_inner), (inner_right, row_bottom_inner), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 9:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, row_top_inner), (inner_right, row_top_inner), 
                (inner_center_x, inner_center_y), 
                (inner_left, row_bottom_inner), (inner_right, row_bottom_inner), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    elif num_rank == 10:
        pips = [(inner_left, inner_top), (inner_right, inner_top), 
                (inner_left, row_top_inner), (inner_right, row_top_inner), 
                (inner_center_x, (inner_top + row_top_inner) // 2), 
                (inner_center_x, (inner_bottom + row_bottom_inner) // 2), 
                (inner_left, row_bottom_inner), (inner_right, row_bottom_inner), 
                (inner_left, inner_bottom), (inner_right, inner_bottom)]
    else:
        # Jack, Queen, King face cards get one prominent stylized center layout
        pips = [(inner_center_x, inner_center_y)]

    # Draw localized pip icons centered securely on calculated vector nodes
    for px, py in pips:
        pw, ph = bj_text_size(draw, str(suit), pip_font)
        draw.text((px - (pw // 2), py - (ph // 2)), str(suit), fill=suit_color, font=pip_font)

def blackjack_status_label(status):
    if status == "busted":
        return "BUST", "#dc2626"
    if status == "standing":
        return "STAND", "#16a34a"
    if status == "playing":
        return "PLAYING", "#ca8a04"
    return "DONE", "#475569"

def generate_blackjack_table_image(player_hands, dealer_cards, show_dealer_hidden=False, player_names=None, statuses=None, bet=None, title="BLACKJACK TABLE", result_text=None, width=2400, height=1400):
    if isinstance(player_hands, dict):
        hand_items = list(player_hands.items())
    else:
        hand_items = list(enumerate(player_hands if player_hands and isinstance(player_hands[0], list) else [player_hands]))
    player_names = player_names or {}
    statuses = statuses or {}
    img = Image.new("RGB", (2400, 1400), "#073b29")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (2400, 1400)], fill="#073b29")
    draw.ellipse([(-360, -240), (2760, 1700)], fill="#0f5132", outline="#d4af37", width=28)
    draw.ellipse([(-260, -130), (2660, 1580)], outline="#14532d", width=16)
    draw.rectangle([(0, 0), (2400, 150)], fill="#111827")
    draw.text((90, 42), title, fill="#f8fafc", font=font_large)
    if bet is not None:
        draw_blackjack_chip(draw, 2060, 16, bet)
    if result_text:
        bj_centered_text(draw, (620, 36, 1780, 112), result_text, "#fde68a", font_medium)
    dealer_score = calculate_blackjack_hand(dealer_cards if show_dealer_hidden else dealer_cards[:1]) if dealer_cards else 0
    dealer_score_text = f"DEALER  |  {dealer_score}" if show_dealer_hidden else f"DEALER  |  {dealer_score} + HIDDEN"
    draw.text((120, 215), dealer_score_text, fill="#f8fafc", font=font_medium)
    dealer_start_x = max(120, 1200 - (len(dealer_cards) * 240) // 2)
    for index, card in enumerate(dealer_cards):
        draw_blackjack_card(draw, card, dealer_start_x + (index * 240), 300, hidden=(index == 1 and not show_dealer_hidden))
    draw.line([(150, 670), (2250, 670)], fill="#d4af37", width=10)
    max_players = max(1, len(hand_items))
    panel_width = 2100 // max_players
    panel_width = max(500, min(1000, panel_width))
    total_width = panel_width * max_players
    first_x = 1200 - (total_width // 2)
    for index, (player_key, hand) in enumerate(hand_items):
        panel_x = first_x + (index * panel_width)
        panel_y = 740
        name = player_names.get(player_key, f"PLAYER {index + 1}")
        status = statuses.get(player_key, "playing")
        status_label, status_color = blackjack_status_label(status)
        score = calculate_blackjack_hand(hand)
        try:
            draw.rounded_rectangle([(panel_x + 20, panel_y), (panel_x + panel_width - 20, panel_y + 560)], radius=26, fill="#082f25", outline="#94a3b8", width=4)
        except:
            draw.rectangle([(panel_x + 20, panel_y), (panel_x + panel_width - 20, panel_y + 560)], fill="#082f25", outline="#94a3b8", width=4)
        draw.text((panel_x + 56, panel_y + 35), str(name)[:18].upper(), fill="#ffffff", font=font_medium)
        draw.text((panel_x + 56, panel_y + 105), f"SCORE: {score}", fill="#fde68a", font=font_medium)
        draw_blackjack_status_pill(draw, panel_x + panel_width - 330, panel_y + 38, status_label, status_color)
        card_start_x = panel_x + 60
        card_y = panel_y + 190
        card_gap = 190 if len(hand) > 4 else 220
        for card_index, card in enumerate(hand):
            draw_blackjack_card(draw, card, card_start_x + (card_index * card_gap), card_y, width=180, height=255)
    draw.text((120, 1322), "Hit to draw another card  |  Stand to hold your hand  |  Dealer stands on 17", fill="#d1d5db", font=font_medium)
    if img.size != (width, height):
        img = img.resize((width, height))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="blackjack.png")

def generate_roulette_image(winning_number, winning_color, width=1600, height=600):
    img = Image.new("RGB", (1600, 600), "#0f5132")
    draw = ImageDraw.Draw(img)
    bg_color = "#228b22"
    if winning_color == "red":
        bg_color = "#b22222"
    elif winning_color == "black":
        bg_color = "#1a1a1a"
    draw.ellipse([(500, 40), (1100, 560)], fill=bg_color, outline="#d4af37", width=20)
    draw.text((660, 180), str(winning_number), fill="#ffffff", font=font_xl)
    draw.text((600, 400), winning_color.upper(), fill="#ffffff", font=font_large)
    if img.size != (width, height):
        img = img.resize((width, height))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="roulette.png")

def get_slots_base():
    return Image.new("RGB", (1800, 900), "#1a1a1a")

def draw_slots_frame(draw, rows, highlight_reel=None):
    font_slots = ImageFont.truetype("arial.ttf", 60) if hasattr(draw, 'font') else None
    try:
        if not font_slots:
            font_slots = ImageFont.load_default()
    except:
        font_slots = None
    for col in range(3):
        x_start = 160 + (col * 520)
        outline_color = "#ffdd00" if (highlight_reel is not None and highlight_reel == col) else "#d4af37"
        fill_color = "#333333" if (highlight_reel is not None and highlight_reel >= col) else "#222222"
        width = 20 if outline_color == "#ffdd00" else 12
        draw.rectangle([(x_start, 80), (x_start + 440, 820)], fill=fill_color, outline=outline_color, width=width)
        for row in range(3):
            y_start = 120 + (row * 220)
            symbol = rows[row][col]
            draw.text((x_start + 130, y_start + 40), symbol, fill="#ffffff", font=font_slots)
    draw.line([(100, 450), (1700, 450)], fill="#ff0000", width=16)

def calculate_blackjack_hand(hand):
    value = 0
    aces = 0
    for card, suit in hand:
        if card in ["J", "Q", "K"]: value += 10
        elif card == "A": value += 11; aces += 1
        else: value += int(card)
    while value > 21 and aces:
        value -= 10; aces -= 1
    return value

def make_deck():
    suits = ["♠", "♥", "♦", "♣"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    deck = [(rank, suit) for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

async def log_moderation_action(action_type: str, target_user_id: int, details: str):
    """Log all moderation actions to admin"""
    admin_id = 978024161689608202
    admin = bot.get_user(admin_id)
    if not admin:
        return
    
    target_user = bot.get_user(target_user_id)
    target_name = target_user.mention if target_user else f"User {target_user_id}"
    
    embed = discord.Embed(
        title=f"📋 Moderation Action: {action_type.upper()}",
        description=f"**Target:** {target_name}\n{details}",
        color=0xff9800
    )
    embed.set_footer(text=f"Timestamp: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        await admin.send(embed=embed)
    except:
        pass

class BjBetModal(discord.ui.Modal, title="Enter Blackjack Bet"):
    """Modal to input blackjack bet amount"""
    bet_input = discord.ui.TextInput(
        label="Bet Amount (minimum 10)",
        placeholder="Enter amount...",
        required=True,
    )
    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.bet_input.value)
            if bet < 10:
                await interaction.response.send_message("❌ **Bet must be at least 10 chips!**", ephemeral=True)
                return
            if USER_DATA[interaction.user.id]["balance"] < bet:
                await interaction.response.send_message(f"❌ **You don't have enough! Balance: ${USER_DATA[interaction.user.id]['balance']:,}**", ephemeral=True)
                return
            
            await interaction.response.send_message("⏳ **Loading, Please Wait...**", ephemeral=True)
            embed = discord.Embed(
                title="🎮 Select Game Mode",
                description=f"**Bet Confirmed:** ${bet:,}\n\nChoose whether to play on your own table or open a multiplayer lobby.",
                color=0x0f5132
            )
            await interaction.edit_original_response(content=None, embed=embed, view=BjGameModeSelectView(interaction.user, bet))
        except ValueError:
            await interaction.response.send_message("❌ **Please enter a valid number!**", ephemeral=True)

class BjGameModeSelectView(discord.ui.View):
    """Choose between singleplayer and multiplayer"""
    def __init__(self, user, bet):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet

    @discord.ui.button(label="Play Alone (Singleplayer)", style=discord.ButtonStyle.primary, emoji="👤")
    async def play_alone(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        await interaction.response.send_message("⏳ **Loading, Please Wait...**", ephemeral=True)
        channel = interaction.channel
        code = None
        lobby_type = "singleplayer"
        LOBBIES[channel.id] = {
            "host": self.user,
            "bet": self.bet,
            "type": lobby_type,
            "join_code": code,
            "players": [self.user],
            "state": "active",
            "hands": {},
            "status": {},
            "dealer_hand": [],
            "deck": [],
            "main_board_msg_id": None,
            "game_message_id": None,
            "mode": "vs_dealer",
            "current_turn_index": 0,
            "dm_messages": {}
        }
        lobby = LOBBIES[channel.id]
        lobby["deck"] = make_deck()
        lobby["dealer_hand"] = [lobby["deck"].pop(), lobby["deck"].pop()]
        USER_DATA[self.user.id]["total_games"] += 1
        await add_xp(self.user.id, 1)
        lobby["hands"][self.user.id] = [lobby["deck"].pop(), lobby["deck"].pop()]
        lobby["status"][self.user.id] = "playing"
        
        board_msg = await channel.send("🃏 Game Starting...", view=BjGameView(channel.id))
        lobby["game_message_id"] = board_msg.id
        await asyncio.sleep(1)
        await update_game_board(channel.id)

    @discord.ui.button(label="Play With Others (Multiplayer)", style=discord.ButtonStyle.success, emoji="👥")
    async def play_others(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        embed = discord.Embed(
            title="⚔️ Select Multiplayer Target",
            description="Choose your play format style:\n\n**Against Dealer:** Everyone shares a single channel board and views everyone's cards.\n**Against Each Other:** Strict turn-based order where hands are private via DMs and you play directly to beat other players.",
            color=0x0f5132
        )
        await interaction.response.edit_message(embed=embed, view=BjMultiplayerTargetView(self.user, self.bet))

class BjMultiplayerTargetView(discord.ui.View):
    """Choose between vs dealer or vs each other"""
    def __init__(self, user, bet):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet

    @discord.ui.button(label="Against Dealer", style=discord.ButtonStyle.primary, emoji="🤖")
    async def vs_dealer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        embed = discord.Embed(
            title="🌍 Select Lobby Visibility",
            description="Choose public to allow anyone to join, or private to limit entry.",
            color=0x0f5132
        )
        await interaction.response.edit_message(embed=embed, view=BjLobbyVisibilityView(self.user, self.bet, "vs_dealer"))

    @discord.ui.button(label="Against Each Other", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def vs_each_other(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        embed = discord.Embed(
            title="🌍 Select Lobby Visibility",
            description="Choose public to allow anyone to join, or private to limit entry.",
            color=0x0f5132
        )
        await interaction.response.edit_message(embed=embed, view=BjLobbyVisibilityView(self.user, self.bet, "vs_each_other"))

class BjLobbyVisibilityView(discord.ui.View):
    """Choose between Public and Private lobbies"""
    def __init__(self, user, bet, target_mode):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet
        self.target_mode = target_mode

    @discord.ui.button(label="Public Lobby", style=discord.ButtonStyle.success, emoji="🌍")
    async def public_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        await interaction.response.send_message("⏳ **Loading, Please Wait...**", ephemeral=True)
        await create_bj_lobby(interaction, self.user, self.bet, "public", self.target_mode)

    @discord.ui.button(label="Private Lobby", style=discord.ButtonStyle.danger, emoji="🔒")
    async def private_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        embed = discord.Embed(
            title="🔐 Private Lobby Options",
            description="**Friends Only:** Only people you added via `!friends` can enter.\n**Code Only:** Direct-messages you a secret code to share.",
            color=0x0f5132
        )
        await interaction.response.edit_message(embed=embed, view=BjPrivateSubView(self.user, self.bet, self.target_mode))

class BjPrivateSubView(discord.ui.View):
    """Sub-options for private lobbies"""
    def __init__(self, user, bet, target_mode):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet
        self.target_mode = target_mode

    @discord.ui.button(label="Friends Only", style=discord.ButtonStyle.primary, emoji="🤝")
    async def friends_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        await interaction.response.send_message("⏳ **Loading, Please Wait...**", ephemeral=True)
        await create_bj_lobby(interaction, self.user, self.bet, "private_friends", self.target_mode)

    @discord.ui.button(label="Code Only", style=discord.ButtonStyle.secondary, emoji="🔑")
    async def code_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return
        await interaction.response.send_message("⏳ **Loading, Please Wait...**", ephemeral=True)
        await create_bj_lobby(interaction, self.user, self.bet, "private_code", self.target_mode)

class BjLobbyTypeView(discord.ui.View):
    """Select lobby type after bet"""
    def __init__(self, user, bet):
        super().__init__(timeout=None)
        self.user = user
        self.bet = bet
    
    @discord.ui.button(label="Public Lobby", style=discord.ButtonStyle.success, emoji="🌍")
    async def public_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.stop()
        await create_bj_lobby(interaction, self.user, self.bet, "public", "vs_dealer")
    
    @discord.ui.button(label="Private (Code)", style=discord.ButtonStyle.secondary, emoji="🔐")
    async def private_code_lobby(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id: return
        self.stop()
        await create_bj_lobby(interaction, self.user, self.bet, "private_code", "vs_dealer")

class BjJoinCodeModal(discord.ui.Modal, title="Enter Lobby Code"):
    code_input = discord.ui.TextInput(
        label="Enter Code",
        placeholder="Type the 4 digit lobby code here...",
        required=True,
        min_length=4,
        max_length=4,
    )
    async def on_submit(self, interaction: discord.Interaction):
        code = self.code_input.value.strip()
        found_lobby_id = None
        for ch_id, lobby in LOBBIES.items():
            if lobby['state'] == 'lobby' and lobby['type'] == 'private_code' and str(lobby['join_code']) == code:
                found_lobby_id = ch_id
                break
        if not found_lobby_id:
            await interaction.response.send_message("**That code is either invalid or the lobby has already started.**", ephemeral=True)
            return
        lobby = LOBBIES[found_lobby_id]
        if interaction.user.id in [p.id for p in lobby['players']]:
            await interaction.response.send_message("**You are already in this lobby.**", ephemeral=True)
            return
        if USER_DATA[interaction.user.id]["balance"] < lobby["bet"]:
            await interaction.response.send_message("**You do not have enough money to match this lobby's bet.**", ephemeral=True)
            return
        lobby["players"].append(interaction.user)
        channel = bot.get_channel(found_lobby_id)
        if channel:
            embed = discord.Embed(
                title="🏛️ PLAYER JOINED VIA CODE",
                description=f"{interaction.user.mention} entered the correct lobby code and joined {lobby['host'].mention}'s game table.",
                color=0x3b82f6
            )
            await channel.send(embed=embed)
        
        await update_lobby_message(found_lobby_id)
        await interaction.response.send_message("**✅ Joined! Check the channel where the lobby was created.**", ephemeral=True)

class BjHubView(discord.ui.View):
    """Main hub for starting a blackjack game"""
    def __init__(self, user_id=None):
        super().__init__(timeout=None)
        self.user_id = user_id
        
        # Check if the user has an automated fast play preference available
        if user_id:
            preferred = determine_preferred_action(user_id)
            if preferred:
                self.add_item(FastPlayButton(preferred))
    
    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, emoji="🎮", row=0)
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BjBetModal())
    
    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        found = []
        for ch_id, lobby in LOBBIES.items():
            if lobby['state'] == 'lobby':
                mode_lbl = "vs Dealer" if lobby.get("mode") == "vs_dealer" else "vs Each Other"
                if lobby['type'] == 'public':
                    ch = bot.get_channel(ch_id)
                    ch_name = ch.name if ch else "Unknown"
                    found.append((ch_id, f"**{lobby['host'].name}** - ${lobby['bet']:,} bet ({mode_lbl}) (#{ch_name}) [Public]"))
                elif lobby['type'] == 'private_friends':
                    if interaction.user.id in USER_DATA[lobby['host'].id].get("friends", {}):
                        ch = bot.get_channel(ch_id)
                        ch_name = ch.name if ch else "Unknown"
                        found.append((ch_id, f"**{lobby['host'].name}** - ${lobby['bet']:,} bet ({mode_lbl}) (#{ch_name}) [Friends-Only]"))
        
        if not found:
            await interaction.response.send_message("❌ **No open accessible lobbies right now.**", ephemeral=True)
            return
        
        embed = discord.Embed(title="Available Lobbies", description="\n".join([l[1] for l in found]), color=0x0f5132)
        view = BjLobbySelectView([l[0] for l in found])
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="Enter Code", style=discord.ButtonStyle.secondary, emoji="🔐", row=0)
    async def enter_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BjJoinCodeModal())


class FastPlayButton(discord.ui.Button):
    def __init__(self, action_pattern):
        super().__init__(
            label=f"Fast Play ({action_pattern.upper().replace('_', ' ')})", 
            style=discord.ButtonStyle.blurple, 
            emoji="⚡",
            row=1
        )
        self.action_pattern = action_pattern

    async def callback(self, interaction: discord.Interaction):
        if self.view.user_id and interaction.user.id != self.view.user_id:
            await interaction.response.send_message("❌ **This menu belongs to someone else!**", ephemeral=True)
            return
            
        modal = FastPlayBetModal(self.action_pattern)
        await interaction.response.send_modal(modal)


class FastPlayBetModal(discord.ui.Modal, title="Fast Play Wager"):
    bet_input = discord.ui.TextInput(label="Bet Amount", placeholder="Enter your wager...", default="100", required=True)
    
    def __init__(self, action_pattern):
        super().__init__()
        self.action_pattern = action_pattern
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet_amt = int(str(self.bet_input.value).strip().replace(",", ""))
            if bet_amt <= 0:
                await interaction.response.send_message("❌ **Your bet must be greater than 0!**", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ **Please provide a valid number for your bet.**", ephemeral=True)
            return
            
        if USER_DATA[interaction.user.id]["balance"] < bet_amt:
            await interaction.response.send_message("❌ **You do not have enough money for that bet!**", ephemeral=True)
            return
            
        await interaction.response.send_message(f"⚡ **Fast Play Activated! Launching configuration: {self.action_pattern.upper().replace('_', ' ')}**", ephemeral=True)
        
        # Determine parameters mapping directly from historical trends 
        if self.action_pattern == "solo":
            await create_bj_lobby(interaction, interaction.user, bet_amt, "singleplayer", "vs_dealer")
        elif self.action_pattern == "multiplayer_versus":
            await create_bj_lobby(interaction, interaction.user, bet_amt, "public", "vs_each_other")
        else: # Default fallback configuration matching multiplayer_dealer
            await create_bj_lobby(interaction, interaction.user, bet_amt, "public", "vs_dealer")


class BjLobbySelectView(discord.ui.View):
    """Select a lobby to join"""
    def __init__(self, lobby_ids):
        super().__init__(timeout=None)
        self.lobby_ids = lobby_ids
    
    @discord.ui.button(label="Join Selected Lobby", style=discord.ButtonStyle.success, emoji="✅")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.lobby_ids:
            await interaction.response.send_message("❌ **No lobbies available.**", ephemeral=True)
            return
        
        lobby_id = self.lobby_ids[0]
        lobby = LOBBIES.get(lobby_id)
        
        if not lobby:
            await interaction.response.send_message("❌ **Lobby no longer exists.**", ephemeral=True)
            return
        
        if interaction.user.id in [p.id for p in lobby['players']]:
            await interaction.response.send_message("❌ **You're already in this lobby!**", ephemeral=True)
            return
        
        if lobby['type'] == 'private_friends' and interaction.user.id not in USER_DATA[lobby['host'].id].get("friends", {}):
            await interaction.response.send_message("❌ **This lobby is for friends of the host only!**", ephemeral=True)
            return
            
        if USER_DATA[interaction.user.id]["balance"] < lobby["bet"]:
            await interaction.response.send_message(f"❌ **Need ${lobby['bet']:,} to join!**", ephemeral=True)
            return
        
        lobby["players"].append(interaction.user)
        await interaction.response.send_message(f"✅ **Joined {lobby['host'].name}'s lobby!**", ephemeral=True)
        await update_lobby_message(lobby_id)


def track_user_game_action(user_id, action_taken):
    """Appends structural action metrics tracking across a player's last 5 rounds"""
    # Convert string key representations matching potential JSON loads safely
    target_key = user_id
    if target_key not in USER_DATA and str(user_id) in USER_DATA:
        target_key = str(user_id)
        
    if target_key not in USER_DATA:
        return
        
    if "history_actions" not in USER_DATA[target_key]:
        USER_DATA[target_key]["history_actions"] = []
        
    USER_DATA[target_key]["history_actions"].append(action_taken)
    if len(USER_DATA[target_key]["history_actions"]) > 5:
        USER_DATA[target_key]["history_actions"].pop(0)


def determine_preferred_action(user_id):
    """Evaluates action patterns to see if automated criteria matches"""
    target_key = user_id
    if target_key not in USER_DATA and str(user_id) in USER_DATA:
        target_key = str(user_id)
        
    if target_key not in USER_DATA or len(USER_DATA[target_key].get("history_actions", [])) < 5:
        return None
        
    actions = USER_DATA[target_key]["history_actions"]
    return max(set(actions), key=actions.count)


async def create_bj_lobby(interaction: discord.Interaction, host: discord.User, bet: int, lobby_type: str, target_mode: str = "vs_dealer"):
    """Create a blackjack lobby"""
    channel = interaction.channel
    code = random.randint(1000, 9999) if lobby_type == "private_code" else None
    
    LOBBIES[channel.id] = {
        "host": host,
        "bet": bet,
        "type": lobby_type,
        "join_code": code,
        "players": [host],
        "state": "lobby",
        "hands": {},
        "status": {},
        "dealer_hand": [],
        "deck": [],
        "main_board_msg_id": None,
        "game_message_id": None,
        "mode": target_mode,
        "current_turn_index": 0,
        "dm_messages": {}
    }
    
    if lobby_type == "public":
        type_str = "Public"
    elif lobby_type == "private_friends":
        type_str = "Private (Friends Only)"
    else:
        type_str = "Private (Code Only)"

    mode_str = "Against Dealer" if target_mode == "vs_dealer" else "Against Each Other"
    description = f"**Host:** {host.mention}\n**Bet:** ${bet:,}\n**Type:** {type_str}\n**Format:** **{mode_str}**\n\n"
    description += "Players waiting to join:\n"
    description += f"• {host.name}\n\n"
    
    if lobby_type == "private_code":
        description += "The entry code was sent securely to the host's direct messages!"
        try:
            await host.send(f"🔒 **Your Private Blackjack Lobby Code:** ||{code}||\n\nShare this code with players whom you want to join!")
        except:
            pass
    elif lobby_type == "private_friends":
        description += "Only players listed on the host's `!friends` network can join via the hub dashboard."
    else:
        description += "Other players can join with `!bj` → Click Join!"
    
    embed = discord.Embed(
        title="🏛️ Blackjack Lobby Created",
        description=description,
        color=0xd4af37
    )
    
    msg = await channel.send(embed=embed, view=BjLobbyActionsView(channel.id))
    LOBBIES[channel.id]["main_board_msg_id"] = msg.id

class BjLobbyActionsView(discord.ui.View):
    """Actions in a lobby"""
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
    
    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary, emoji="➕")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby = LOBBIES.get(self.channel_id)
        if not lobby:
            await interaction.response.send_message("❌ **Lobby no longer exists.**", ephemeral=True)
            return
        if interaction.user.id in [p.id for p in lobby["players"]]:
            await interaction.response.send_message("❌ **You're already in this lobby!**", ephemeral=True)
            return
        if lobby['type'] == 'private_friends' and interaction.user.id not in USER_DATA[lobby['host'].id].get("friends", {}):
            await interaction.response.send_message("❌ **This lobby is restricted to friends of the host only!**", ephemeral=True)
            return
        if lobby['type'] == 'private_code':
            await interaction.response.send_message("❌ **Please click 'Enter Code' on the main `!bj` hub window to join code-based tables.**", ephemeral=True)
            return
        
        if USER_DATA[interaction.user.id]["balance"] < lobby["bet"]:
            await interaction.response.send_message(f"❌ **You need ${lobby['bet']:,} to join!**", ephemeral=True)
            return
        
        lobby["players"].append(interaction.user)
        await interaction.response.send_message(f"✅ **Joined {lobby['host'].name}'s lobby!**", ephemeral=True)
        await update_lobby_message(self.channel_id)
    
    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, emoji="▶️")
    async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby = LOBBIES[self.channel_id]
        if interaction.user.id != lobby["host"].id:
            await interaction.response.send_message("❌ **Only the host can start the game!**", ephemeral=True)
            return
        
        if lobby["state"] != "lobby":
            await interaction.response.send_message("❌ **Game already started!**", ephemeral=True)
            return
        
        if len(lobby["players"]) < 1:
            await interaction.response.send_message("❌ **Need at least 1 player!**", ephemeral=True)
            return
        
        lobby["state"] = "active"
        lobby["deck"] = make_deck()
        lobby["dealer_hand"] = [lobby["deck"].pop(), lobby["deck"].pop()]
        lobby["current_turn_index"] = 0
        
        for player in lobby["players"]:
            USER_DATA[player.id]["total_games"] += 1
            await add_xp(player.id, 1)
            lobby["hands"][player.id] = [lobby["deck"].pop(), lobby["deck"].pop()]
            lobby["status"][player.id] = "playing"
        
        await interaction.response.defer()
        await start_active_game(self.channel_id, interaction)

async def update_lobby_message(channel_id):
    """Update the lobby display message"""
    lobby = LOBBIES.get(channel_id)
    channel = bot.get_channel(channel_id)
    
    if not channel or not lobby or not lobby["main_board_msg_id"]:
        return
    
    try:
        msg = await channel.fetch_message(lobby["main_board_msg_id"])
        players_list = "\n".join([f"• {p.name}" for p in lobby["players"]])
        
        if lobby["type"] == "public":
            type_str = "Public"
        elif lobby["type"] == "private_friends":
            type_str = "Private (Friends Only)"
        else:
            type_str = "Private (Code Only)"
            
        mode_lbl = "Against Dealer" if lobby.get("mode") == "vs_dealer" else "Against Each Other"
        
        embed = discord.Embed(
            title="🏛️ Blackjack Lobby",
            description=f"**Host:** {lobby['host'].mention}\n**Bet:** ${lobby['bet']:,}\n**Type:** {type_str}\n**Format:** **{mode_lbl}**\n\n**Players ({len(lobby['players'])}):**\n{players_list}",
            color=0xd4af37
        )
        await msg.edit(embed=embed)
    except:
        pass

async def start_active_game(channel_id, interaction):
    """Start an active blackjack game"""
    lobby = LOBBIES[channel_id]
    channel = bot.get_channel(channel_id)
    
    if lobby.get("mode") == "vs_each_other":
        board_msg = await channel.send("⚔️ Multiplayer Head-to-Head Active! Check your Direct Messages for your secure hand panels.")
        lobby["game_message_id"] = board_msg.id
        for p in lobby["players"]:
            try:
                dm_m = await p.send("🃏 Dispatching your private hand display window...", view=BjGameView(channel_id))
                lobby["dm_messages"][p.id] = dm_m.id
            except:
                await channel.send(f"⚠️ {p.mention} **Could not send you a Direct Message panel! Please toggle allow messages from server members.**")
    else:
        board_msg = await channel.send("🃏 Game Starting...", view=BjGameView(channel_id))
        lobby["game_message_id"] = board_msg.id
        
    await asyncio.sleep(1)
    await update_game_board(channel_id)

class BjGameView(discord.ui.View):
    """Game action buttons"""
    def __init__(self, channel_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        
    def check_player_turn(self, interaction: discord.Interaction, lobby):
        if lobby.get("mode") == "vs_each_other":
            idx = lobby.get("current_turn_index", 0)
            players = lobby["players"]
            if idx < len(players):
                if players[idx].id != interaction.user.id:
                    return False
            return True
        return True
    
    @discord.ui.button(label="HIT", style=discord.ButtonStyle.danger, emoji="🎴")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby = LOBBIES.get(self.channel_id)
        if not lobby or lobby["status"].get(interaction.user.id) != "playing":
            await interaction.response.send_message("❌ **It's not your turn or game is over!**", ephemeral=True)
            return
            
        if not self.check_player_turn(interaction, lobby):
            await interaction.response.send_message("❌ **It is not your active turn yet in this Head-to-Head game order!**", ephemeral=True)
            return
        
        if "history_actions" not in USER_DATA[interaction.user.id]:
            USER_DATA[interaction.user.id]["history_actions"] = []
        track_user_game_action(interaction.user.id, "hit")
        
        if len(lobby["deck"]) == 0:
            lobby["deck"] = make_deck()
        
        lobby["hands"][interaction.user.id].append(lobby["deck"].pop())
        score = calculate_blackjack_hand(lobby["hands"][interaction.user.id])
        
        if score > 21:
            lobby["status"][interaction.user.id] = "busted"
            USER_DATA[interaction.user.id]["balance"] -= lobby["bet"]
            USER_DATA[interaction.user.id]["net_earnings"] -= lobby["bet"]
            await save_user_data() # Force save on bust
            await interaction.response.send_message(f"💥 **BUST! Score: {score}** (You lost ${lobby['bet']:,})", ephemeral=True)
            if lobby.get("mode") == "vs_each_other":
                lobby["current_turn_index"] += 1
        else:
            await save_user_data()
            await interaction.response.send_message(f"🎴 **HIT! New score: {score}**", ephemeral=True)
        
        await update_game_board(self.channel_id)
        
        all_done = all(lobby["status"].get(p.id, "done") != "playing" for p in lobby["players"])
        if all_done or (lobby.get("mode") == "vs_each_other" and lobby["current_turn_index"] >= len(lobby["players"])):
            await finish_game(self.channel_id)
    
    @discord.ui.button(label="STAND", style=discord.ButtonStyle.success, emoji="✋")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby = LOBBIES.get(self.channel_id)
        if not lobby or lobby["status"].get(interaction.user.id) != "playing":
            await interaction.response.send_message("❌ **It's not your turn or game is over!**", ephemeral=True)
            return
            
        if not self.check_player_turn(interaction, lobby):
            await interaction.response.send_message("❌ **It is not your active turn yet in this Head-to-Head game order!**", ephemeral=True)
            return
        
        if "history_actions" not in USER_DATA[interaction.user.id]:
            USER_DATA[interaction.user.id]["history_actions"] = []
        track_user_game_action(interaction.user.id, "stand")
        
        lobby["status"][interaction.user.id] = "standing"
        await save_user_data()
        await interaction.response.send_message("✅ **STAND! Locked in your hand.**", ephemeral=True)
        if lobby.get("mode") == "vs_each_other":
            lobby["current_turn_index"] += 1
        
        await update_game_board(self.channel_id)
        
        all_done = all(lobby["status"].get(p.id, "done") != "playing" for p in lobby["players"])
        if all_done or (lobby.get("mode") == "vs_each_other" and lobby["current_turn_index"] >= len(lobby["players"])):
            await finish_game(self.channel_id)

    @discord.ui.button(label="DOUBLE", style=discord.ButtonStyle.primary, emoji="💰")
    async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lobby = LOBBIES.get(self.channel_id)
        if not lobby or lobby["status"].get(interaction.user.id) != "playing":
            await interaction.response.send_message("❌ **It's not your turn or game is over!**", ephemeral=True)
            return
            
        if lobby.get("type") != "singleplayer":
            await interaction.response.send_message("❌ **Double down mechanical updates are restricted to singleplayer matches!**", ephemeral=True)
            return
            
        current_hand = lobby["hands"].get(interaction.user.id, [])
        if len(current_hand) != 2:
            await interaction.response.send_message("❌ **You can only double down on your first turning deal sequence!**", ephemeral=True)
            return
            
        double_bet = lobby["bet"]
        if USER_DATA[interaction.user.id]["balance"] < (double_bet * 2):
            await interaction.response.send_message(f"❌ **Insufficient funds to process double operation! Required: ${double_bet:,} extra.**", ephemeral=True)
            return
            
        if "history_actions" not in USER_DATA[interaction.user.id]:
            USER_DATA[interaction.user.id]["history_actions"] = []
        track_user_game_action(interaction.user.id, "double")
        
        lobby["bet"] = double_bet * 2
        if len(lobby["deck"]) == 0:
            lobby["deck"] = make_deck()
            
        lobby["hands"][interaction.user.id].append(lobby["deck"].pop())
        score = calculate_blackjack_hand(lobby["hands"][interaction.user.id])
        
        if score > 21:
            lobby["status"][interaction.user.id] = "busted"
            USER_DATA[interaction.user.id]["balance"] -= lobby["bet"]
            USER_DATA[interaction.user.id]["net_earnings"] -= lobby["bet"]
            await save_user_data() # Force save on bust
            await interaction.response.send_message(f"💥 **BUSTED ON DOUBLE DOWN! Score: {score}** (You lost ${lobby['bet']:,}**)", ephemeral=True)
        else:
            lobby["status"][interaction.user.id] = "standing"
            await save_user_data()
            await interaction.response.send_message(f"💰 **DOUBLE DOWN locked in at score {score}! Bet increased to ${lobby['bet']:,}**", ephemeral=True)
            
        await update_game_board(self.channel_id)
        await finish_game(self.channel_id)
class BjPlayAgainView(discord.ui.View):
    """Play again refresh capability button window after match finishes"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Play Again / Refresh Hub", style=discord.ButtonStyle.success, emoji="🔄")
    async def play_again_hub(self, interaction: discord.Interaction, button: discord.ui.Button):
        await ensure_user(interaction.user.id)
        if USER_DATA[interaction.user.id].get("trespassed", False):
            embed = discord.Embed(title="❌ Access Denied", description="You are **Trespassed** from this establishment. Security will not allow you to play.", color=0xff0000)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        embed = discord.Embed(
            title="🃏 BLACKJACK HUB",
            description="Choose an option to get started:",
            color=0x0f5132
        )
        await interaction.response.send_message(embed=embed, view=BjHubView(), ephemeral=False)

def format_hand_visual(hand, hide_second=False):
    """Format a hand as visual card emoji blocks for embed display"""
    cards = []
    for i, (rank, suit) in enumerate(hand):
        if i == 1 and hide_second:
            cards.append("🂠")
        else:
            suit_emoji = {"♠": "♠️", "♥": "♥️", "♦": "♦️", "♣": "♣️"}.get(suit, suit)
            cards.append(f"`{rank}{suit_emoji}`")
    return "  ".join(cards)

def score_display(score, status=None):
    """Return a prominent score string with status indicator"""
    if status == "busted":
        return f"**💥 {score} — BUST**"
    elif status == "standing":
        return f"**✋ {score} — STANDING**"
    elif status == "playing":
        return f"**⏳ {score} — YOUR TURN**"
    else:
        return f"**{score}**"

async def update_game_board(channel_id):
    """Update the game board with current status"""
    lobby = LOBBIES.get(channel_id)
    channel = bot.get_channel(channel_id)
    
    if not channel or not lobby:
        return
        
    vs_each_other = (lobby.get("mode") == "vs_each_other")
    
    if vs_each_other:
        for player in lobby["players"]:
            try:
                msg_id = lobby["dm_messages"].get(player.id)
                if not msg_id:
                    continue
                
                embed = discord.Embed(
                    title="⚔️ Blackjack Head-to-Head Private Table Panel",
                    color=0x1e3a8a
                )
                embed.add_field(
                    name="━━━━━━━━━━━━━━━━━━━━━━━",
                    value=f"**Bet stake:** 💰 ${lobby['bet']:,}  |  **Host table:** {lobby['host'].name}",
                    inline=False
                )
                
                turn_idx = lobby.get("current_turn_index", 0)
                current_player = lobby["players"][turn_idx] if turn_idx < len(lobby["players"]) else None
                turn_status = f"🟢 **Your Active Turn!**" if current_player and current_player.id == player.id else f"⏳ Waiting on turn: **{current_player.name if current_player else 'Dealer'}**"
                embed.add_field(name="📋 Current Board Turn Order Position", value=turn_status, inline=False)
                
                p_hand = lobby["hands"].get(player.id, [])
                p_score = calculate_blackjack_hand(p_hand)
                p_status = lobby["status"].get(player.id, "done")
                
                embed.add_field(
                    name=f"🃏 Your Private Hand Info",
                    value=f"{format_hand_visual(p_hand)}\n> Score: {score_display(p_score, p_status)}",
                    inline=False
                )
                
                player_hands = {player.id: p_hand}
                player_names = {player.id: player.name}
                p_statuses = {player.id: p_status}
                
                table_file = generate_blackjack_table_image(
                    player_hands,
                    [], 
                    show_dealer_hidden=False,
                    player_names=player_names,
                    statuses=p_statuses,
                    bet=lobby["bet"],
                    title=f"PRIVATE HAND PANELS - {player.name.upper()}"
                )
                
                embed.set_image(url="attachment://blackjack.png")
                
                try:
                    old_dm = await player.dm_channel.fetch_message(msg_id)
                    await old_dm.delete()
                except:
                    pass
                    
                new_dm = await player.send(file=table_file, embed=embed, view=BjGameView(channel_id))
                lobby["dm_messages"][player.id] = new_dm.id
            except:
                pass
    else:
        if not lobby["game_message_id"]:
            return
        try:
            msg = await channel.fetch_message(lobby["game_message_id"])
            dealer_visible_score = calculate_blackjack_hand([lobby["dealer_hand"][0]])
            dealer_hand_str = format_hand_visual(lobby["dealer_hand"], hide_second=True)
            
            embed = discord.Embed(
                title="🃏 Blackjack — Game In Progress",
                color=0x0f5132
            )
            embed.add_field(
                name="━━━━━━━━━━━━━━━━━━━━━━━",
                value=f"**Bet:** 💰 ${lobby['bet']:,}  |  **Host:** {lobby['host'].mention}",
                inline=False
            )
            embed.add_field(
                name="🤖  DEALER",
                value=f"{dealer_hand_str}\n> Score: **{dealer_visible_score}** *(one card hidden)*",
                inline=False
            )
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
            
            for player in lobby["players"]:
                hand = lobby["hands"].get(player.id, [])
                score = calculate_blackjack_hand(hand)
                status = lobby["status"].get(player.id, "done")
                hand_str = format_hand_visual(hand)
                score_str = score_display(score, status)
                
                if status == "playing":
                    name_prefix = "🟡"
                elif status == "standing":
                    name_prefix = "🟢"
                else:
                    name_prefix = "🔴"
                
                embed.add_field(
                    name=f"{name_prefix}  {player.name}",
                    value=f"{hand_str}\n> {score_str}",
                    inline=True
                )
            
            embed.set_footer(text="🟡 Playing  •  🟢 Standing  •  🔴 Busted  |  Use the buttons below to Hit or Stand")
            player_hands = {player.id: lobby["hands"].get(player.id, []) for player in lobby["players"]}
            player_names = {player.id: player.name for player in lobby["players"]}
            table_file = generate_blackjack_table_image(
                player_hands,
                lobby["dealer_hand"],
                show_dealer_hidden=False,
                player_names=player_names,
                statuses=lobby["status"],
                bet=lobby["bet"],
                title="BLACKJACK - GAME IN PROGRESS"
            )
            embed.set_image(url="attachment://blackjack.png")
            await msg.delete()
            new_msg = await channel.send(file=table_file, embed=embed, view=BjGameView(channel_id))
            lobby["game_message_id"] = new_msg.id
        except:
            pass

async def finish_game(channel_id):
    """Finish the game and calculate results"""
    lobby = LOBBIES.get(channel_id)
    if not lobby:
        return
    
    channel = bot.get_channel(channel_id)
    vs_each_other = (lobby.get("mode") == "vs_each_other")
    
    dealer_score = calculate_blackjack_hand(lobby["dealer_hand"])
    any_standing = any(lobby["status"].get(p.id) == "standing" for p in lobby["players"])
    if any_standing:
        while dealer_score < 17:
            if len(lobby["deck"]) == 0:
                lobby["deck"] = make_deck()
            lobby["dealer_hand"].append(lobby["deck"].pop())
            dealer_score = calculate_blackjack_hand(lobby["dealer_hand"])
    
    dealer_hand_str = format_hand_visual(lobby["dealer_hand"])
    
    embed = discord.Embed(
        title="🏁  BLACKJACK — GAME OVER",
        color=0x111827
    )
    embed.add_field(
        name="🤖  DEALER FINAL HAND",
        value=f"{dealer_hand_str}\n> Final Score: **{dealer_score}**{'  💥 BUST' if dealer_score > 21 else ''}",
        inline=False
    )
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    
    for player in lobby["players"]:
        hand = lobby["hands"].get(player.id, [])
        score = calculate_blackjack_hand(hand)
        status = lobby["status"].get(player.id)
        bet = lobby["bet"]
        hand_str = format_hand_visual(hand)
        
        if status == "busted":
            result_icon = "❌"
            result_line = f"**BUSTED  —  -{bet:,}**"
        elif dealer_score > 21:
            USER_DATA[player.id]["balance"] += bet
            USER_DATA[player.id]["net_earnings"] += bet
            USER_DATA[player.id]["wins"] += 1
            result_icon = "🎉"
            result_line = f"**DEALER BUSTED  —  +{bet:,}**"
        elif score > dealer_score:
            USER_DATA[player.id]["balance"] += bet
            USER_DATA[player.id]["net_earnings"] += bet
            USER_DATA[player.id]["wins"] += 1
            result_icon = "🎉"
            result_line = f"**WIN  —  +{bet:,}**"
        elif score < dealer_score:
            USER_DATA[player.id]["balance"] -= bet
            USER_DATA[player.id]["net_earnings"] -= bet
            result_icon = "❌"
            result_line = f"**LOSS  —  -{bet:,}**"
        else:
            result_icon = "🤝"
            result_line = f"**PUSH (TIE)  —  ±0**"
        
        new_bal = USER_DATA[player.id]["balance"]
        embed.add_field(
            name=f"{result_icon}  {player.name}",
            value=f"{hand_str}\n> Score: **{score}** vs  Dealer: **{dealer_score}**\n> {result_line}\n> Balance: **${new_bal:,}**",
            inline=True
        )
        
        if vs_each_other:
            try:
                msg_id = lobby["dm_messages"].get(player.id)
                if msg_id:
                    old_dm = await player.dm_channel.fetch_message(msg_id)
                    await old_dm.delete()
            except:
                pass
    
    if channel:
        player_hands = {player.id: lobby["hands"].get(player.id, []) for player in lobby["players"]}
        player_names = {player.id: player.name for player in lobby["players"]}
        table_file = generate_blackjack_table_image(
            player_hands,
            lobby["dealer_hand"],
            show_dealer_hidden=True,
            player_names=player_names,
            statuses=lobby["status"],
            bet=lobby["bet"],
            title="BLACKJACK - GAME OVER",
            result_text="FINAL TABLE"
        )
        embed.set_image(url="attachment://blackjack.png")
        try:
            if lobby.get("game_message_id"):
                old_msg = await channel.fetch_message(lobby["game_message_id"])
                await old_msg.delete()
        except:
            pass
        await save_user_data() # Force save on final payout
        await channel.send(file=table_file, embed=embed, view=BjPlayAgainView())
    
    del LOBBIES[channel_id]

@bot.event
async def on_message(message):
    if message.author.bot: 
        return
    await ensure_user(message.author.id)
    
    if isinstance(message.channel, discord.DMChannel):
        content = message.content.lower().strip()
        
        # Check for solo blackjack game
        if message.author.id in SOLOBJ_GAMES:
            game = SOLOBJ_GAMES[message.author.id]
            if content == "hit":
                if len(game["deck"]) == 0:
                    game["deck"] = make_deck()
                game["player_hand"].append(game["deck"].pop())
                p_score = calculate_blackjack_hand(game["player_hand"])
                
                track_user_game_action(message.author.id, "hit")
                
                if p_score > 21:
                    USER_DATA[message.author.id]["balance"] -= game["bet"]
                    USER_DATA[message.author.id]["net_earnings"] -= game["bet"]
                    hand_str = format_hand_visual(game["player_hand"])
                    embed = discord.Embed(title="💥 BLACKJACK — BUST!", color=0xff0000)
                    embed.add_field(name="Your Hand", value=f"{hand_str}", inline=False)
                    embed.add_field(name="Your Score", value=f"## 💥 {p_score} — BUST!", inline=False)
                    embed.add_field(name="Result", value=f"❌ **You busted and lost ${game['bet']:,}**", inline=False)
                    embed.add_field(name="New Balance", value=f"**${USER_DATA[message.author.id]['balance']:,}**", inline=False)
                    table_file = generate_blackjack_table_image(
                        {message.author.id: game["player_hand"]},
                        game["dealer_hand"],
                        show_dealer_hidden=True,
                        player_names={message.author.id: message.author.name},
                        statuses={message.author.id: "busted"},
                        bet=game["bet"],
                        title="BLACKJACK - BUST",
                        result_text="YOU BUSTED"
                    )
                    embed.set_image(url="attachment://blackjack.png")
                    await save_user_data()
                    await message.author.send(file=table_file, embed=embed)
                    del SOLOBJ_GAMES[message.author.id]
                else:
                    hand_str = format_hand_visual(game["player_hand"])
                    dealer_visible = format_hand_visual(game["dealer_hand"], hide_second=True)
                    dealer_visible_score = calculate_blackjack_hand([game["dealer_hand"][0]])
                    embed = discord.Embed(title="♣️ BLACKJACK — HIT", color=0x0f5132)
                    embed.add_field(name="🤖  Dealer", value=f"{dealer_visible}\n> Score: **{dealer_visible_score}** *(one card hidden)*", inline=False)
                    embed.add_field(name="** **", value="** **", inline=False)
                    embed.add_field(name="🃏  Your Hand", value=f"{hand_str}", inline=False)
                    embed.add_field(name="Your Score", value=f"## ⏳ {p_score}", inline=False)
                    embed.set_footer(text="Type  hit  to draw another card  •  Type  stand  to hold")
                    table_file = generate_blackjack_table_image(
                        {message.author.id: game["player_hand"]},
                        game["dealer_hand"],
                        show_dealer_hidden=False,
                        player_names={message.author.id: message.author.name},
                        statuses={message.author.id: "playing"},
                        bet=game["bet"],
                        title="BLACKJACK - HIT"
                    )
                    embed.set_image(url="attachment://blackjack.png")
                    await save_user_data()
                    await message.author.send(file=table_file, embed=embed)
                return
                
            elif content == "stand":
                game["player_done"] = True
                p_score = calculate_blackjack_hand(game["player_hand"])
                d_score = calculate_blackjack_hand(game["dealer_hand"])
                
                track_user_game_action(message.author.id, "stand")
                
                while d_score < 17:
                    game["dealer_hand"].append(game["deck"].pop())
                    d_score = calculate_blackjack_hand(game["dealer_hand"])
                
                player_hand_str = format_hand_visual(game["player_hand"])
                dealer_hand_str = format_hand_visual(game["dealer_hand"])
                
                result_embed = discord.Embed(title="🏁 BLACKJACK — GAME OVER", color=0x111827)
                result_embed.add_field(
                    name="🤖  Dealer Final Hand",
                    value=f"{dealer_hand_str}\n> Final Score: **{d_score}**{'  💥 BUST' if d_score > 21 else ''}",
                    inline=False
                )
                result_embed.add_field(name="━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
                result_embed.add_field(
                    name="🃏  Your Hand",
                    value=f"{player_hand_str}\n> Your Score: **{p_score}**",
                    inline=False
                )
                
                if p_score > 21:
                    outcome = "❌  **BUST — YOU LOST**"
                    USER_DATA[message.author.id]["balance"] -= game["bet"]
                    USER_DATA[message.author.id]["net_earnings"] -= game["bet"]
                elif d_score > 21:
                    outcome = "🎉  **DEALER BUSTED — YOU WIN!**"
                    USER_DATA[message.author.id]["balance"] += game["bet"]
                    USER_DATA[message.author.id]["net_earnings"] += game["bet"]
                    USER_DATA[message.author.id]["wins"] += 1
                elif p_score > d_score:
                    outcome = "🎉  **YOU WIN!**"
                    USER_DATA[message.author.id]["balance"] += game["bet"]
                    USER_DATA[message.author.id]["net_earnings"] += game["bet"]
                    USER_DATA[message.author.id]["wins"] += 1
                elif p_score < d_score:
                    outcome = "❌  **YOU LOST**"
                    USER_DATA[message.author.id]["balance"] -= game["bet"]
                    USER_DATA[message.author.id]["net_earnings"] -= game["bet"]
                else:
                    outcome = "🤝  **PUSH — TIE**"
                
                result_embed.add_field(name="━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
                result_embed.add_field(name="Result", value=f"## {outcome}", inline=False)
                result_embed.add_field(name="Bet Amount", value=f"**${game['bet']:,}**", inline=True)
                result_embed.add_field(name="New Balance", value=f"**${USER_DATA[message.author.id]['balance']:,}**", inline=True)
                table_file = generate_blackjack_table_image(
                    {message.author.id: game["player_hand"]},
                    game["dealer_hand"],
                    show_dealer_hidden=True,
                    player_names={message.author.id: message.author.name},
                    statuses={message.author.id: "standing"},
                    bet=game["bet"],
                    title="BLACKJACK - GAME OVER",
                    result_text="FINAL HAND"
                )
                result_embed.set_image(url="attachment://blackjack.png")
                await save_user_data()
                await message.author.send(file=table_file, embed=result_embed)
                del SOLOBJ_GAMES[message.author.id]
                return
        
        # Check for multiplayer blackjack
        if content in ["hit", "stand"]:
            target_lobby_id = None
            for ch_id, lobby in LOBBIES.items():
                if lobby["state"] == "active" and message.author in lobby["players"]:
                    if lobby["status"][message.author.id] == "playing":
                        target_lobby_id = ch_id
                        break
            
            if target_lobby_id:
                lobby = LOBBIES[target_lobby_id]
                player_id = message.author.id
                if content == "hit":
                    if len(lobby["deck"]) == 0:
                        lobby["deck"] = make_deck()
                    lobby["hands"][player_id].append(lobby["deck"].pop())
                    score = calculate_blackjack_hand(lobby["hands"][player_id])
                    
                    track_user_game_action(player_id, "hit")
                    
                    if score > 21:
                        lobby["status"][player_id] = "busted"
                        USER_DATA[player_id]["balance"] -= lobby["bet"]
                        USER_DATA[player_id]["net_earnings"] -= lobby["bet"]
                        await save_user_data()
                        await message.author.send("💥 **You went over 21 and busted! Your results have been updated on the main channel board.**")
                    else:
                        await save_user_data()
                        await message.author.send(f"✅ **You hit! Your new score is: {score}**")
                elif content == "stand":
                    lobby["status"][player_id] = "standing"
                    
                    track_user_game_action(player_id, "stand")
                    await save_user_data()
                    
                    await message.author.send("✅ **Selection locked. Standing with your current cards.**")
                
                await asyncio.sleep(0.5)
                all_done = all(lobby["status"][p.id] != "playing" for p in lobby["players"])
                if all_done: 
                    await evaluate_multiplayer_dealer_resolutions(target_lobby_id)
                else: 
                    await update_all_player_boards_and_dms(target_lobby_id)
                return
    
    await bot.process_commands(message)

@bot.command()
async def bj(ctx):
    """Blackjack hub - start, join, or enter a private game"""
    await ensure_user(ctx.author.id)
    await save_user_data() # Persist the user state upon entry
    
    if USER_DATA[ctx.author.id].get("trespassed", False):
        embed = discord.Embed(title="❌ Access Denied", description="You are **Trespassed** from this establishment. Security will not allow you to play.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title="🃏 BLACKJACK HUB",
        description="Choose an option to get started:",
        color=0x0f5132
    )
    
    preferred = determine_preferred_action(ctx.author.id)
    if preferred:
        embed.add_field(
            name="🎰 Fast Play Ready", 
            value=f"You frequently choose to **{preferred.upper()}**. Press the Fast Play shortcut below to launch instantly!", 
            inline=False
        )
        
    await ctx.send(embed=embed, view=BjHubView(ctx.author.id))

@bot.command()
async def wyr(ctx, amount: str = "50"):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    now = datetime.datetime.utcnow().timestamp()
    day_in_seconds = 24 * 60 * 60
    
    USER_DATA[user_id]["wyr_cooldowns"] = [t for t in USER_DATA[user_id]["wyr_cooldowns"] if now - t < day_in_seconds]
    
    if len(USER_DATA[user_id]["wyr_cooldowns"]) >= 10:
        oldest_reset = USER_DATA[user_id]["wyr_cooldowns"][0] + day_in_seconds
        time_left = oldest_reset - now
        hours, remainder = divmod(int(time_left), 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(f"You have already done 10 Would You Rather questions today! Try again in {hours}h {minutes}m {seconds}s.")
        return

    current_balance = USER_DATA[user_id]["balance"]
    if amount.endswith("%"):
        try:
            percentage = float(amount[:-1])
            calculated_reward = int(current_balance * (percentage / 100))
        except ValueError:
            await ctx.send("Invalid percentage format. Use a number followed by '%'.")
            return
    else:
        try:
            calculated_reward = int(amount)
        except ValueError:
            await ctx.send("Invalid amount format. Enter a flat number or a percentage ending in '%'.")
            return

    if calculated_reward < 0:
        await ctx.send("The reward amount cannot be negative.")
        return

    USER_DATA[user_id]["wyr_cooldowns"].append(now)
    
    question = random.choice(wyr_questions)
    
    embed = discord.Embed(
        title="Would You Rather?", 
        description=f"Reward: {calculated_reward} coins\n\n**Option A:** {question['A']}\n\n**Option B:** {question['B']}", 
        color=discord.Color.blue()
    )
    
    class WYRView(discord.ui.View):
        def __init__(self, author_id):
            super().__init__(timeout=30.0)
            self.author_id = author_id
            self.value = None
            self.message = None
            self.update_button_states()

        def update_button_states(self):
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    if self.value is not None:
                        child.disabled = True

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Only the command author can use these buttons.", ephemeral=True)
                return False
            return True
            
        @discord.ui.button(label="Option A", style=discord.ButtonStyle.blurple, custom_id="wyr_option_a")
        async def option_a(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = "A"
            self.update_button_states()
            USER_DATA[user_id]["balance"] += calculated_reward
            await save_user_data()
            await interaction.response.edit_message(content=f"You chose **Option A**: {question['A']}! (+{calculated_reward} coins)", embed=embed, view=self)
            self.stop()
            
        @discord.ui.button(label="Option B", style=discord.ButtonStyle.blurple, custom_id="wyr_option_b")
        async def option_b(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.value = "B"
            self.update_button_states()
            USER_DATA[user_id]["balance"] += calculated_reward
            await save_user_data()
            await interaction.response.edit_message(content=f"You chose **Option B**: {question['B']}! (+{calculated_reward} coins)", embed=embed, view=self)
            self.stop()

        async def on_timeout(self):
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            if self.message:
                try:
                    await self.message.edit(content="You took too long to pick an option!", embed=embed, view=self)
                except Exception:
                    pass
            
    view = WYRView(ctx.author.id)
    message = await ctx.send(embed=embed, view=view)
    view.message = message


@bot.command()
async def quiz(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    question = random.choice(quiz_questions)
    
    options_text = ""
    styles = ["🔹", "🔸", "🔺", "🔷"]
    for i, opt in enumerate(question["options"]):
        options_text += f"{styles[i]} **[{i+1}]** {opt}\n"

    embed = discord.Embed(
        title="⚡ BOT TRIVIA CHALLENGE ⚡",
        description=f"Prove your knowledge and secure the bounty!\n\n"
                    f"╔═════════════════════════════════════════╗\n"
                    f"  **QUESTION:**\n"
                    f"  *{question['question']}*\n"
                    f"╚═════════════════════════════════════════╝\n\n"
                    f"{options_text}\n"
                    f"💵 **Bounty:** `{question['reward']}` coins",
        color=0x00ffcc  
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    embed.set_footer(text="Type 1, 2, 3, 4 in chat OR click a matching button below! • 20s")

    class QuizButtonView(discord.ui.View):
        def __init__(self, author_id):
            super().__init__(timeout=20.0)
            self.author_id = author_id
            self.value = None
            self.message = None
            
            for i in range(len(question["options"])):
                btn = discord.ui.Button(
                    label=f"Option {i+1}", 
                    style=discord.ButtonStyle.blurple, 
                    custom_id=f"quiz_btn_{i}"
                )
                btn.callback = self.make_callback(i)
                self.add_item(btn)

        def make_callback(self, idx):
            async def callback(interaction: discord.Interaction):
                self.value = question["options"][idx]
                self.stop()
            return callback

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Only the command author can use these buttons.", ephemeral=True)
                return False
            return True

        async def on_timeout(self):
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            if self.message:
                try:
                    await self.message.edit(content=f"⏰ **Time's up!** The correct answer was **{question['correct']}**.", view=self)
                except Exception:
                    pass

    view = QuizButtonView(ctx.author.id)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

    def check(m):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content in ["1", "2", "3", "4"]

    try:
        task_chat = asyncio.create_task(bot.wait_for("message", check=check, timeout=20.0))
        task_view = asyncio.create_task(view.wait())

        done, pending = await asyncio.wait(
            [task_chat, task_view],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        if task_chat in done:
            msg = task_chat.result()
            selected_idx = int(msg.content) - 1
            chosen_answer = question["options"][selected_idx]
            try:
                await msg.delete()  
            except Exception:
                pass
        else:
            chosen_answer = view.value

        for child in view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        if chosen_answer is None:
            await message.edit(content=f"⏰ **Time's up!** The correct answer was **{question['correct']}**.", view=view)
        elif chosen_answer == question["correct"]:
            reward = question["reward"]
            USER_DATA[user_id]["balance"] += reward
            await save_user_data()
            
            success_embed = discord.Embed(
                title="🎉 CORE MATRIX OUTCOME: SUCCESS 🎉",
                description=f"╠══> **Your Input:** `{chosen_answer}`\n"
                            f"╠══> **Bounty Claimed:** `+{reward}` coins\n\n"
                            f"Your credentials match up. Balance updated successfully.",
                color=0x00ff00
            )
            await message.edit(embed=success_embed, view=view)
        else:
            fail_embed = discord.Embed(
                title="❌ CORE MATRIX OUTCOME: BREACH ❌",
                description=f"╠══> **Your Input:** `{chosen_answer}`\n"
                            f"╠══> **Correct Record:** `{question['correct']}`\n\n"
                            f"Incorrect authorization parameter sequence provided.",
                color=0xff0033
            )
            await message.edit(embed=fail_embed, view=view)

    except asyncio.timeoutError:
        for child in view.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await message.edit(content=f"⏰ **Time's up!** The correct answer was **{question['correct']}**.", view=view)

@bot.command()
async def pyl(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)

    current_pot = 0
    spins_taken = 0

    def generate_board_render(highlight_idx=None):
        items = [x["disp"] for x in PRESS_YOUR_LUCK_BOARD]
        random.shuffle(items)
        if highlight_idx is not None:
            items[highlight_idx] = f"👉 **{items[highlight_idx]}** 👈"
        
        grid = (
            f"┌──────────────┬──────────────┬──────────────┐\n"
            f"│  {items[0]:<10}  │  {items[1]:<10}  │  {items[2]:<10}  │\n"
            f"├──────────────┼──────────────┼──────────────┤\n"
            f"│  {items[3]:<10}  │  🎰 BOARD    │  {items[4]:<10}  │\n"
            f"├──────────────┼──────────────┼──────────────┤\n"
            f"│  {items[5]:<10}  │  {items[6]:<10}  │  {items[7]:<10}  │\n"
            f"└──────────────┴──────────────┴──────────────┘"
        )
        return f"```text\n{grid}\n```"

    embed = discord.Embed(
        title="🛑 PRESS YOUR LUCK: BIG BOARD 🛑",
        description=f"Accumulate massive bankrolls but avoid the **Whammy**! Walk away whenever you choose.\n\n"
                    f"{generate_board_render()}\n"
                    f"💰 **Current Pot:** `0` coins\n"
                    f"🔄 **Spins Taken:** `0` / `5` max",
        color=0xffcc00
    )
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

    class GameView(discord.ui.View):
        def __init__(self, author_id):
            super().__init__(timeout=45.0)
            self.author_id = author_id
            self.message = None
            self.ended = False

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("Only the player can make action selections.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Spin Board", style=discord.ButtonStyle.success, custom_id="pyl_spin")
        async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_pot, spins_taken
            spins_taken += 1
            
            selected_idx = random.randint(0, len(PRESS_YOUR_LUCK_BOARD) - 1)
            square = PRESS_YOUR_LUCK_BOARD[selected_idx]

            if square["type"] == "whammy":
                self.ended = True
                for child in self.children:
                    child.disabled = True
                
                loss_embed = discord.Embed(
                    title="👹 WHAMMY ATTACK! 👹",
                    description=f"The Whammy cleared your bank account!\n\n"
                                f"You lost everything in the pot.\n"
                                f"❌ **Final Winnings:** `0` coins\n"
                                f"🔄 **Spins Survived:** `{spins_taken - 1}`",
                    color=0xff0033
                )
                await interaction.response.edit_message(embed=loss_embed, view=self)
                self.stop()
                return

            current_pot += square["val"]
            
            if spins_taken >= 5:
                self.ended = True
                for child in self.children:
                    child.disabled = True
                
                USER_DATA[user_id]["balance"] += current_pot
                await save_user_data()
                
                max_embed = discord.Embed(
                    title="🏁 MAX SPINS REACHED 🏁",
                    description=f"You survived all 5 rounds and must bank your funds!\n\n"
                                f"🎉 **Total Earnings Banked:** `+{current_pot}` coins",
                    color=0x00ff00
                )
                await interaction.response.edit_message(embed=max_embed, view=self)
                self.stop()
                return

            next_embed = discord.Embed(
                title="🛑 PRESS YOUR LUCK: BIG BOARD 🛑",
                description=f"You hit: **{square['disp']}**!\n\n"
                            f"{generate_board_render(selected_idx)}\n"
                            f"💰 **Current Pot:** `{current_pot}` coins\n"
                            f"🔄 **Spins Taken:** `{spins_taken}` / `5` max",
                color=0xffcc00
            )
            await interaction.response.edit_message(embed=next_embed, view=self)

        @discord.ui.button(label="Bank & Cash Out", style=discord.ButtonStyle.danger, custom_id="pyl_cashout")
        async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_pot
            self.ended = True
            for child in self.children:
                child.disabled = True

            if current_pot > 0:
                USER_DATA[user_id]["balance"] += current_pot
                await save_user_data()

            win_embed = discord.Embed(
                title="💰 SMART CASHOUT SUCCESS 💰",
                description=f"You walked away before the Whammy got you!\n\n"
                            f"🎉 **Total Earnings Banked:** `+{current_pot}` coins\n"
                            f"🔄 **Spins Taken:** `{spins_taken}`",
                color=0x00ff00
            )
            await interaction.response.edit_message(embed=win_embed, view=self)
            self.stop()

        async def on_timeout(self):
            if self.ended:
                return
            for child in self.children:
                child.disabled = True
            if self.message:
                try:
                    await self.message.edit(content="⏳ **Game closed due to inactivity.** Remaining pot abandoned.", view=self)
                except Exception:
                    pass

    view = GameView(ctx.author.id)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@bot.command()
async def pay(ctx, member: discord.Member, amount: str):
    await ensure_user(ctx.author.id)
    await ensure_user(member.id)
    
    author_balance = USER_DATA[ctx.author.id]["balance"]
    amount_clean = amount.lower().strip()
    
    if amount_clean == "all":
        amount_val = author_balance
    elif amount_clean.endswith("%"):
        try:
            percentage = float(amount_clean[:-1])
            if percentage <= 0 or percentage > 100:
                await ctx.send("❌ **Percentage must be between 1% and 100%!**")
                return
            amount_val = int(author_balance * (percentage / 100))
        except ValueError:
            await ctx.send("❌ **Invalid percentage format!**")
            return
    else:
        try:
            amount_val = int(amount_clean)
        except ValueError:
            await ctx.send("❌ **Invalid amount format! Use a whole number, percentage (e.g., 25%), or 'all'.**")
            return

    amount = amount_val

    if member.id == ctx.author.id:
        await ctx.send("❌ **You cannot wire chips to yourself!**")
        return

    if amount <= 0:
        await ctx.send("❌ **Amount must be greater than 0!**")
        return
        
    if USER_DATA[ctx.author.id]["balance"] < amount:
        await ctx.send(f"❌ **You don't have enough chips! Your balance is ${USER_DATA[ctx.author.id]['balance']:,}.**")
        return

    target_perm = USER_DATA[member.id]["settings"].get("pay_permissions", "everyone")
    if target_perm == "no_one":
        await ctx.send(f"❌ **{member.display_name} has turned off incoming chips transfers from everyone.**")
        return
    elif target_perm == "friends":
        is_friend = False
        if "friends_list" in USER_DATA[member.id]:
            if ctx.author.id in USER_DATA[member.id]["friends_list"]:
                is_friend = True
        if not is_friend:
            await ctx.send(f"❌ **{member.display_name} only accepts direct wire transfers from users on their friends list.**")
            return

    confirm_embed = discord.Embed(
        title="💳 Pending Chip Transfer",
        description=f"Are you sure you want to send **${amount:,} chips** to {member.mention}?",
        color=0xeab308
    )
    confirm_embed.set_footer(text="This confirmation expires in 60 seconds.")
    
    view = PayConfirmationView(ctx.author.id, member, amount)
    confirm_msg = await ctx.send(embed=confirm_embed, view=view)
    
    await view.wait()
    
    if view.confirmed is not True:
        await confirm_msg.edit(content="❌ **Transfer cancelled or timed out.**", embed=None, view=None)
        return

    if USER_DATA[ctx.author.id]["balance"] < amount:
        await confirm_msg.edit(content=f"❌ **Transfer failed! You no longer have enough chips.**", embed=None, view=None)
        return

    use_2fa = USER_DATA[ctx.author.id]["settings"].get("transfer_2fa", False)
    if use_2fa:
        code = str(random.randint(100000, 999999))
        try:
            await ctx.author.send(f"🔒 **Security Code for Transfer:**\nYou are attempting to pay **${amount:,} chips** to {member.display_name}.\nEnter this one-time code in the server chat to authenticate: `{code}`")
            await confirm_msg.edit(content=f"🔒 {ctx.author.mention}, **a 6-digit authentication code has been sent to your DMs.** Please type it here to finalize the transaction.", embed=None, view=None)
        except discord.Forbidden:
            await confirm_msg.edit(content="❌ **Failed to send verification code! Please enable your Direct Messages and try again.**", embed=None, view=None)
            return

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.strip() == code

        try:
            await ctx.bot.wait_for('message', check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send(f"❌ {ctx.author.mention}, **verification timed out!** The payment transaction has been canceled.")
            return

    USER_DATA[ctx.author.id]["balance"] -= amount
    USER_DATA[member.id]["balance"] += amount
    await save_user_data()
    
    success_embed = discord.Embed(
        title="✅ Transfer Complete",
        description=f"**Successfully paid ${amount:,} chips to {member.mention}!**",
        color=0x22c55e
    )
    await confirm_msg.edit(content=None, embed=success_embed, view=None)

class ShopPageModal(discord.ui.Modal, title="Go to Shop Page"):
    page_input = discord.ui.TextInput(
        label="Enter Page Number",
        placeholder="Type a page number...",
        min_length=1,
        max_length=5,
        required=True
    )

    def __init__(self, total_pages, shop_command_callback):
        super().__init__()
        self.total_pages = total_pages
        self.shop_command_callback = shop_command_callback

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_page = int(self.page_input.value)
            if target_page < 1:
                target_page = 1
            elif target_page > self.total_pages:
                target_page = self.total_pages
            
            await self.shop_command_callback(interaction, target_page)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid whole number.", ephemeral=True)


class BulkAmountModal(discord.ui.Modal, title="Configure Multi-Item Buy"):
    amount_input = discord.ui.TextInput(
        label="Quantity per item",
        placeholder="Type an exact integer number, or 'max'...",
        default="1",
        min_length=1,
        max_length=10,
        required=True
    )
    
    manual_input = discord.ui.TextInput(
        label="Manually Type Missing Item IDs (Optional)",
        placeholder="e.g., custom_booster, rare_upgrade (separated by commas)",
        required=False,
        max_length=200
    )

    def __init__(self, selected_items, user_id, ctx_or_interaction):
        super().__init__()
        self.selected_items = list(selected_items)
        self.user_id = user_id
        self.ctx_or_interaction = ctx_or_interaction

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
            return

        await interaction.response.defer()

        raw_manual = self.manual_input.value.strip()
        if raw_manual:
            manual_tags = [t.strip().lower() for t in raw_manual.replace(",", " ").split() if t.strip()]
            for tag in manual_tags:
                if tag in SHOP_ITEMS and tag not in self.selected_items:
                    self.selected_items.append(tag)
                elif tag not in SHOP_ITEMS:
                    self.selected_items.append(f"__INVALID__{tag}")

        if not self.selected_items:
            await interaction.followup.send("❌ No items selected or manually entered.", ephemeral=True)
            return

        amt_str = self.amount_input.value.strip().lower()
        success_log = []
        fail_log = []
        total_spent = 0
        initial_balance = USER_DATA[self.user_id]["balance"]

        for item_key in self.selected_items:
            if item_key.startswith("__INVALID__"):
                bad_tag = item_key.replace("__INVALID__", "")
                fail_log.append(f"• `{bad_tag}`: Item does not exist inside shop registry.")
                continue

            item_data = SHOP_ITEMS[item_key]
            current_level = USER_DATA[self.user_id]["upgrades"].get(item_key, 0)

            if current_level >= item_data["max_level"]:
                fail_log.append(f"• `{item_data['name']}`: Already maxed out.")
                continue

            if amt_str == "max":
                amount = 0
                item_cost = 0
                temp_balance = USER_DATA[self.user_id]["balance"] - total_spent
                
                while (current_level + amount) < item_data["max_level"]:
                    next_lvl_cost = item_data["cost"] * (current_level + 1 + amount)
                    if temp_balance >= next_lvl_cost:
                        temp_balance -= next_lvl_cost
                        item_cost += next_lvl_cost
                        amount += 1
                    else:
                        break
                
                if amount == 0:
                    fail_log.append(f"• `{item_data['name']}`: Cannot afford any levels.")
                    continue
            else:
                try:
                    amount = max(1, int(amt_str))
                except ValueError:
                    amount = 1
                amount = min(amount, item_data["max_level"] - current_level)
                
                item_cost = 0
                for i in range(amount):
                    item_cost += item_data["cost"] * (current_level + 1 + i)

            if (USER_DATA[self.user_id]["balance"] - total_spent) < item_cost:
                fail_log.append(f"• `{item_data['name']}`: Insufficient funds (Needs ${item_cost:,} chips).")
                continue

            total_spent += item_cost
            USER_DATA[self.user_id]["upgrades"][item_key] = current_level + amount
            success_log.append(f"• `{item_data['name']}` **+{amount}** levels (Now Lvl {current_level + amount})")

        if total_spent > 0:
            USER_DATA[self.user_id]["balance"] -= total_spent
            await save_user_data()

        embed = discord.Embed(title="🛒 Bulk Checkout Results", color=0x10b981 if total_spent > 0 else 0xef4444)
        if success_log:
            embed.add_field(name="✅ Successful Purchases", value="\n".join(success_log), inline=False)
        if fail_log:
            embed.add_field(name="❌ Skipped / Failed", value="\n".join(fail_log), inline=False)
        
        embed.add_field(name="💰 Transaction Summary", value=f"Total Debited: **{total_spent:,}** chips\nRemaining Balance: **{USER_DATA[self.user_id]['balance']:,}** chips", inline=False)
        
        await interaction.followup.send(embed=embed)


class BulkItemSelectView(discord.ui.View):
    def __init__(self, user_id, ctx_or_interaction):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.ctx_or_interaction = ctx_or_interaction
        self.selected_items = []
        self.build_select()

    def build_select(self):
        options = []
        for key, item in SHOP_ITEMS.items():
            options.append(discord.SelectOption(
                label=item["name"],
                value=key,
                description=f"Max Lvl: {item['max_level']} | Base: {item['cost']:,} chips"
            ))
        
        select = discord.ui.Select(
            placeholder="Check items you wish to buy...",
            min_values=0,
            max_values=len(options),
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)
        
        skip_btn = discord.ui.Button(label="Type Manually Instead ✏️", style=discord.ButtonStyle.secondary)
        skip_btn.callback = self.skip_to_modal_callback
        self.add_item(skip_btn)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
            return
        self.selected_items = interaction.data["values"]
        modal = BulkAmountModal(self.selected_items, self.user_id, self.ctx_or_interaction)
        await interaction.response.send_modal(modal)

    async def skip_to_modal_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
            return
        modal = BulkAmountModal([], self.user_id, self.ctx_or_interaction)
        await interaction.response.send_modal(modal)


class ShopPaginator(discord.ui.View):
    def __init__(self, user_id, total_pages, current_page, shop_command_callback, ctx_or_interaction):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.total_pages = total_pages
        self.current_page = current_page
        self.shop_command_callback = shop_command_callback
        self.ctx_or_interaction = ctx_or_interaction
        self.build_buttons()

    def build_buttons(self):
        for p in range(1, self.total_pages + 1):
            is_current = (p == self.current_page)
            btn = discord.ui.Button(
                label=str(p),
                style=discord.ButtonStyle.primary if is_current else discord.ButtonStyle.secondary,
                disabled=is_current,
                custom_id=f"shop_page_{p}"
            )
            btn.callback = self.make_page_callback(p)
            self.add_item(btn)

        goto_btn = discord.ui.Button(
            label="Go To Page... 📂",
            style=discord.ButtonStyle.secondary,
            custom_id="shop_goto_modal"
        )
        goto_btn.callback = self.goto_modal_callback
        self.add_item(goto_btn)

        bulk_btn = discord.ui.Button(
            label="Bulk Buy 🛒",
            style=discord.ButtonStyle.success,
            custom_id="shop_bulk_select"
        )
        bulk_btn.callback = self.bulk_select_callback
        self.add_item(bulk_btn)

    def make_page_callback(self, page_num):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
                return
            await self.shop_command_callback(interaction, page_num)
        return callback

    async def goto_modal_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
            return
        modal = ShopPageModal(self.total_pages, self.shop_command_callback)
        await interaction.response.send_modal(modal)

    async def bulk_select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This interaction is not for you.", ephemeral=True)
            return
        view = BulkItemSelectView(self.user_id, self.ctx_or_interaction)
        await interaction.response.send_message("📋 Select upgrades from the menu or choose to type item tags manually:", view=view, ephemeral=True)


@bot.command()
async def shop(ctx, action: str = None, *, buy_arguments: str = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    await save_user_data()
    
    if USER_DATA[user_id].get("trespassed", False):
        embed = discord.Embed(title="❌ Access Denied", description="You are **Trespassed** from this establishment.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    if "upgrades" not in USER_DATA[user_id]:
        USER_DATA[user_id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "slots_winboost": 0, "roulette_boost": 0, "xp_booster": 0}
        await save_user_data()

    async def render_shop_page(target_source, target_page: int):
        items_per_page = 5
        shop_keys = list(SHOP_ITEMS.keys())
        total_items = len(shop_keys)
        total_pages = max(1, math.ceil(total_items / items_per_page))
        
        if target_page < 1:
            target_page = 1
        elif target_page > total_pages:
            target_page = total_pages

        embed = discord.Embed(
            title="🏪 The Casino Upgrade Shop 🏪", 
            description=f"Invest your chips into permanent passive boosters!\nPage **{target_page}** of **{total_pages}**", 
            color=0x00ffff
        )
        embed.set_footer(text="Use `!shop buy <id> <amt>` or multi-buy: `!shop buy id1 amt, id2 max`")
        
        start_index = (target_page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_keys = shop_keys[start_index:end_index]
        
        for key in page_keys:
            item = SHOP_ITEMS[key]
            current_level = USER_DATA[user_id]["upgrades"].get(key, 0)
            max_lvl = item["max_level"]
            
            if current_level >= max_lvl:
                cost_text = "✨ **MAXED OUT** ✨"
            else:
                scaled_cost = item["cost"] * (current_level + 1)
                cost_text = f"Cost per level: **{scaled_cost:,}** chips"
                
            colors = ["⬛", "🟩", "🟨", "🟦", "🟪", "🟥", "🟧", "🟫"]
            full_loops = current_level // 10
            remainder = current_level % 10
            foreground_color = colors[min(full_loops + 1, len(colors) - 1)]
            background_color = colors[min(full_loops, len(colors) - 1)]
            
            if current_level >= max_lvl:
                status_bar = foreground_color * 10
            else:
                status_bar = (foreground_color * remainder) + (background_color * (10 - remainder))
            
            field_value = (
                f"{item['description']}\n"
                f"Progress: {status_bar} ({current_level}/{max_lvl})\n"
                f"{cost_text}\n"
                f"ID Tag: `{key}`"
            )
            embed.add_field(name=item["name"], value=field_value, inline=False)
            
        embed.add_field(name="💰 Your Wallet", value=f"Balance: **{USER_DATA[user_id]['balance']:,}** chips", inline=False)
        
        view = ShopPaginator(user_id, total_pages, target_page, render_shop_page, ctx)
        
        if isinstance(target_source, discord.Interaction):
            await target_source.response.edit_message(embed=embed, view=view)
        else:
            await target_source.send(embed=embed, view=view)

    if action is None or action.isdigit():
        requested_page = int(action) if (action and action.isdigit()) else 1
        await render_shop_page(ctx, requested_page)
        return

    if action.lower() == "buy":
        if buy_arguments is None:
            embed = discord.Embed(title="❌ Missing Arguments", description="Please provide an item ID and quantity.\nExample: `!shop buy plinko_boost 5` or mass buy: `!shop buy plinko_boost 2, slots_boost max`", color=0xff0000)
            await ctx.send(embed=embed)
            return

        orders = buy_arguments.split(",")
        success_log = []
        fail_log = []
        total_cost = 0
        current_wallet = USER_DATA[user_id]["balance"]

        for order in orders:
            parts = order.strip().split()
            if len(parts) < 2:
                fail_log.append(f"• `{order.strip()}`: Invalid format. Must be `<id> <quantity>`.")
                continue
                
            item_id = parts[0].lower()
            amount_str = parts[1].lower()

            if item_id not in SHOP_ITEMS:
                fail_log.append(f"• `{item_id}`: Unknown item ID tag.")
                continue

            item_data = SHOP_ITEMS[item_id]
            current_level = USER_DATA[user_id]["upgrades"].get(item_id, 0)

            if current_level >= item_data["max_level"]:
                fail_log.append(f"• `{item_data['name']}`: Upgrade already fully maxed out.")
                continue

            if amount_str == "max":
                amount = 0
                item_accumulated_cost = 0
                temp_balance = current_wallet - total_cost
                
                while (current_level + amount) < item_data["max_level"]:
                    next_lvl_cost = item_data["cost"] * (current_level + 1 + amount)
                    if temp_balance >= next_lvl_cost:
                        temp_balance -= next_lvl_cost
                        item_accumulated_cost += next_lvl_cost
                        amount += 1
                    else:
                        break
                
                if amount == 0:
                    fail_log.append(f"• `{item_data['name']}`: Cannot afford a single level.")
                    continue
            else:
                try:
                    amount = max(1, int(amount_str))
                except ValueError:
                    amount = 1
                amount = min(amount, item_data["max_level"] - current_level)
                
                item_accumulated_cost = 0
                for i in range(amount):
                    item_accumulated_cost += item_data["cost"] * (current_level + 1 + i)

            if (current_wallet - total_cost) < item_accumulated_cost:
                fail_log.append(f"• `{item_data['name']}`: Insufficient chips (Requires ${item_accumulated_cost:,}).")
                continue

            total_cost += item_accumulated_cost
            USER_DATA[user_id]["upgrades"][item_id] = current_level + amount
            success_log.append(f"• `{item_data['name']}` **+{amount}** (New Level: {current_level + amount})")

        if total_cost > 0:
            USER_DATA[user_id]["balance"] -= total_cost
            await save_user_data()

        embed = discord.Embed(title="🛍️ Shop Purchase Summary", color=0x00ff00 if total_cost > 0 else 0xff0000)
        if success_log:
            embed.add_field(name="✅ Successful Additions", value="\n".join(success_log), inline=False)
        if fail_log:
            embed.add_field(name="❌ Errors / Failures", value="\n".join(fail_log), inline=False)
            
        embed.add_field(name="💰 Payment Log", value=f"Total Deducted: **-{total_cost:,}** chips\nCurrent Wallet Balance: **{USER_DATA[user_id]['balance']:,}** chips", inline=False)
        await ctx.send(embed=embed)
class AntiMacroMathView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        num1 = random.randint(10, 50)
        num2 = random.randint(5, 20)
        self.correct_answer = num1 + num2
        
        wrong1 = self.correct_answer + random.choice([-3, -2, 2, 3, 5])
        wrong2 = self.correct_answer + random.choice([-5, -4, 4, 6, 7])
        if wrong1 == self.correct_answer or wrong1 == wrong2:
            wrong1 += 1
        if wrong2 == self.correct_answer or wrong1 == wrong2:
            wrong2 += 2
            
        choices = [self.correct_answer, wrong1, wrong2]
        random.shuffle(choices)
        
        for index, choice in enumerate(choices):
            button = discord.ui.Button(label=str(choice), style=discord.ButtonStyle.primary, custom_id=f"math_{index}_{choice}")
            button.callback = self.make_callback(choice)
            self.add_item(button)

    def make_callback(self, choice: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ **This minigame is not for you!**", ephemeral=True)
                return
            self.stop()
            for child in self.children:
                child.disabled = True
            await ensure_user(self.user_id)
            if choice == self.correct_answer:
                reward = random.randint(1500, 3000)
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="🎉 VERIFICATION SUCCESSFUL!",
                    description=f"You successfully solved the arithmetic equation! You have been awarded **${reward:,}** chips.",
                    color=0x22c55e
                )
            else:
                reward = 250
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="❌ VERIFICATION FAILED",
                    description=f"Incorrect answer! You receive a reduced standard relief grant of **${reward:,}** chips.",
                    color=0xf43f5e
                )
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

class AntiMacroSequenceView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.emojis_pool = ["🍎", "🍌", "🍇", "🍒", "🥝"]
        random.shuffle(self.emojis_pool)
        self.target_sequence = self.emojis_pool[:3]
        self.user_clicks = []
        
        buttons_pool = list(self.target_sequence)
        random.shuffle(buttons_pool)
        
        for emoji in buttons_pool:
            button = discord.ui.Button(emoji=emoji, style=discord.ButtonStyle.secondary, custom_id=f"seq_{emoji}")
            button.callback = self.make_callback(emoji)
            self.add_item(button)

    def make_callback(self, emoji: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ **This minigame is not for you!**", ephemeral=True)
                return
            
            self.user_clicks.append(emoji)
            for child in self.children:
                if child.emoji and str(child.emoji) == emoji:
                    child.disabled = True
            
            if len(self.user_clicks) < 3:
                await interaction.response.edit_message(view=self)
                return
                
            self.stop()
            for child in self.children:
                child.disabled = True
                
            await ensure_user(self.user_id)
            if self.user_clicks == self.target_sequence:
                reward = random.randint(1500, 3000)
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="🎉 PATTERN MATCHED!",
                    description=f"You successfully clicked the sequence in the exact order requested! You have been awarded **${reward:,}** chips.",
                    color=0x22c55e
                )
            else:
                reward = 250
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="❌ PATTERN FAILED",
                    description=f"You entered the wrong order. You receive a standard baseline relief grant of **${reward:,}** chips.",
                    color=0xf43f5e
                )
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

class AntiMacroGridView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.labels = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India"]
        random.shuffle(self.labels)
        self.target_label = random.choice(self.labels)
        
        for label in self.labels:
            style = discord.ButtonStyle.secondary
            button = discord.ui.Button(label=label, style=style, custom_id=f"grid_{label}")
            button.callback = self.make_callback(label)
            self.add_item(button)

    def make_callback(self, label: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ **This minigame is not for you!**", ephemeral=True)
                return
            self.stop()
            for child in self.children:
                child.disabled = True
            await ensure_user(self.user_id)
            if label == self.target_label:
                reward = random.randint(1500, 3000)
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="🎉 VERIFICATION PASSED!",
                    description=f"You successfully located and pressed **{label}**! You have been awarded **${reward:,}** chips.",
                    color=0x22c55e
                )
            else:
                reward = 250
                USER_DATA[self.user_id]["balance"] += reward
                embed = discord.Embed(
                    title="❌ VERIFICATION FAILED",
                    description=f"You pressed the wrong grid button. You receive a reduced structural relief grant of **${reward:,}** chips.",
                    color=0xf43f5e
                )
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

@bot.command()
async def bailout(ctx):
    await ensure_user(ctx.author.id)
    # Save the status check initial state
    await save_user_data()
    
    if USER_DATA[ctx.author.id]["balance"] > 10:
        await ctx.send(f"❌ **You are not bankrupt! You still have ${USER_DATA[ctx.author.id]['balance']:,} chips.**")
        return
        
    game_type = random.choice(["math", "sequence", "grid"])
    
    if game_type == "math":
        view = AntiMacroMathView(ctx.author.id)
        embed = discord.Embed(
            title="🏦 Emergency Bailout Verification",
            description=f"Solve this verification equation to claim your bailout:\n\n➡️ **What is {view.correct_answer - 15} + 15?**",
            color=0x3b82f6
        )
        await ctx.send(embed=embed, view=view)
        
    elif game_type == "sequence":
        view = AntiMacroSequenceView(ctx.author.id)
        seq_str = " ➔ ".join(view.target_sequence)
        embed = discord.Embed(
            title="🏦 Emergency Bailout Verification",
            description=f"Anti-macro verification! Please click the buttons in this exact sequence from left to right:\n\n📋 **{seq_str}**",
            color=0x3b82f6
        )
        await ctx.send(embed=embed, view=view)
        
    elif game_type == "grid":
        view = AntiMacroGridView(ctx.author.id)
        embed = discord.Embed(
            title="🏦 Emergency Bailout Verification",
            description=f"Anti-macro verification! Locate the target label in the randomized matrix field below and press it:\n\n🎯 Target Button to click: **{view.target_label}**",
            color=0x3b82f6
        )
        await ctx.send(embed=embed, view=view)

@bot.command()
async def deposit(ctx, amount: str):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if "vault" not in USER_DATA[user_id]:
        USER_DATA[user_id]["vault"] = 0
        
    # Calculate Capacity: 50,000 base + (10,000 * bank_boost level)
    boost_lvl = USER_DATA[user_id].get("upgrades", {}).get("bank_boost", 0)
    max_capacity = 50000 + (10000 * boost_lvl)
    
    if amount.lower() == "max":
        amount = USER_DATA[user_id]["balance"]
    else:
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("❌ Please enter a valid number or `max`.")
            return

    if amount <= 0:
        await ctx.send("❌ You must deposit at least 1 chip.")
        return
        
    if USER_DATA[user_id]["balance"] < amount:
        await ctx.send("❌ You don't have that many chips in your wallet.")
        return
        
    if USER_DATA[user_id]["vault"] + amount > max_capacity:
        can_deposit = max_capacity - USER_DATA[user_id]["vault"]
        if can_deposit <= 0:
            await ctx.send(f"❌ Your vault is full! Max capacity: **{max_capacity:,}**.")
            return
        amount = can_deposit
        
    USER_DATA[user_id]["balance"] -= amount
    USER_DATA[user_id]["vault"] += amount
    await save_user_data()
    
    embed = discord.Embed(title="🔒 Vault Deposit", description=f"Deposited **${amount:,}** into your vault.\nVault Balance: **{USER_DATA[user_id]['vault']:,}** / **{max_capacity:,}**", color=0x3b82f6)
    await ctx.send(embed=embed)

@bot.command()
async def withdraw(ctx, amount: str):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if "vault" not in USER_DATA[user_id]:
        USER_DATA[user_id]["vault"] = 0
        
    if amount.lower() == "max":
        amount = USER_DATA[user_id]["vault"]
    else:
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("❌ Please enter a valid number or `max`.")
            return
            
    if amount <= 0:
        await ctx.send("❌ You must withdraw at least 1 chip.")
        return
        
    if USER_DATA[user_id]["vault"] < amount:
        await ctx.send("❌ You don't have that many chips in your vault.")
        return
        
    USER_DATA[user_id]["balance"] += amount
    USER_DATA[user_id]["vault"] -= amount
    await save_user_data()
    
    embed = discord.Embed(title="🔓 Vault Withdrawal", description=f"Withdrew **${amount:,}** to your wallet.\nVault Balance: **{USER_DATA[user_id]['vault']:,}**", color=0xf59e0b)
    await ctx.send(embed=embed)

@bot.command()
async def bank(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    boost_lvl = USER_DATA[user_id].get("upgrades", {}).get("bank_boost", 0)
    max_capacity = 50000 + (10000 * boost_lvl)
    vault_amt = USER_DATA[user_id].get("vault", 0)
    
    embed = discord.Embed(title="🏦 Personal Vault", color=0x10b981)
    embed.add_field(name="Vault Balance", value=f"**{vault_amt:,}** / **{max_capacity:,}** chips", inline=False)
    embed.add_field(name="Capacity Boost", value=f"Level **{boost_lvl}** (+{boost_lvl * 10000:,} storage)", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def race(ctx, selection: str, bet: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 10:
        remaining = int(10 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before racing again.")
    
    selection = selection.lower()
    valid_lanes = ["1", "2", "3", "4", "5"]
    if selection not in valid_lanes:
        await ctx.send("❌ **Invalid lane selection! Choose a lane from 1 to 5.**")
        return
        
    if bet < 10:
        await ctx.send("❌ **Minimum race wager is 10 chips!**")
        return
        
    if USER_DATA[user_id]["balance"] < bet:
        await ctx.send(f"❌ **Inadequate funds! Current balance: ${USER_DATA[user_id]['balance']:,}**")
        return

    USER_DATA[user_id]["balance"] -= bet
    USER_DATA[user_id]["net_earnings"] -= bet
    USER_DATA[user_id]["total_games"] += 1
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await add_xp(user_id, 1)
    await save_user_data() 

    racer_type = random.choice(["Duck", "Horse"])
    lane_positions = [150, 150, 150, 150, 150]
    finish_line = 1020
    
    msg = await ctx.send(f"🏁 **The Grand {racer_type} Derby is starting! Wager of ${bet:,} locked onto Lane {selection}.**")
    
    winner = None
    while not winner:
        for i in range(5):
            lane_positions[i] += random.randint(45, 115)
            if lane_positions[i] >= finish_line:
                lane_positions[i] = finish_line
                if winner is None:
                    winner = str(i + 1)
        
        img = Image.new("RGB", (1200, 720), "#1e293b")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (1200, 110)], fill="#0f172a")
        draw.text((50, 25), f"GRAND {racer_type.upper()} DERBY", fill="#eab308", font=font_large)
        draw.rectangle([(finish_line + 40, 110), (finish_line + 60, 680)], fill="#ef4444")
        
        for i in range(5):
            y_pos = 130 + (i * 110)
            draw.rectangle([(40, y_pos), (1160, y_pos + 90)], fill="#334155", outline="#475569", width=2)
            draw.text((60, y_pos + 22), f"LANE {i+1}", fill="#94a3b8", font=font_medium)
            racer_x = lane_positions[i]
            badge_color = "#eab308" if str(i+1) == selection else "#38bdf8"
            draw.ellipse([(racer_x, y_pos + 15), (racer_x + 60, y_pos + 75)], fill=badge_color, outline="#ffffff", width=2)
            draw.text((racer_x + 22, y_pos + 20), str(i+1), fill="#0f172a", font=font_medium)
            
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file = discord.File(buffer, filename="race.png")
        embed = discord.Embed(title=f"🏇 Derby Race Track Live Feed", color=0x3b82f6)
        embed.set_image(url="attachment://race.png")
        await msg.edit(content=None, embed=embed, attachments=[file])
        await asyncio.sleep(1.2)

    if selection == winner:
        payout = bet * 4
        USER_DATA[user_id]["balance"] += payout
        USER_DATA[user_id]["net_earnings"] += payout
        USER_DATA[user_id]["wins"] += 1
        result_desc = f"🎉 **Victory! Lane {winner} crossed the finish line first!**\nYou won **${payout:,}** chips!"
        embed_color = 0x22c55e
    else:
        result_desc = f"❌ **Lane {winner} won the race.**\nYour racer in Lane {selection} fell behind. You lost your bet of **${bet:,}** chips."
        embed_color = 0xf43f5e
    
    await save_user_data() 

    img = Image.new("RGB", (1200, 720), "#1e293b")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (1200, 110)], fill="#0f172a")
    draw.text((50, 25), "OFFICIAL DERBY RESULTS", fill="#eab308", font=font_large)
    draw.rectangle([(finish_line + 40, 110), (finish_line + 60, 680)], fill="#ef4444")
    
    for i in range(5):
        y_pos = 130 + (i * 110)
        is_winner = str(i+1) == winner
        fill_clr = "#1e293b" if is_winner else "#334155"
        out_clr = "#22c55e" if is_winner else "#475569"
        wdth = 4 if is_winner else 2
        draw.rectangle([(40, y_pos), (1160, y_pos + 90)], fill=fill_clr, outline=out_clr, width=wdth)
        label_text = f"LANE {i+1} (WINNER)" if is_winner else f"LANE {i+1}"
        draw.text((60, y_pos + 22), label_text, fill="#ffffff" if is_winner else "#94a3b8", font=font_medium)
        racer_x = lane_positions[i]
        badge_color = "#22c55e" if is_winner else ("#eab308" if str(i+1) == selection else "#38bdf8")
        draw.ellipse([(racer_x, y_pos + 15), (racer_x + 60, y_pos + 75)], fill=badge_color, outline="#ffffff", width=2)
        draw.text((racer_x + 22, y_pos + 20), str(i+1), fill="#0f172a", font=font_medium)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="results.png")

    final_embed = discord.Embed(title="🏁 Race Concluded!", description=result_desc, color=embed_color)
    final_embed.set_image(url="attachment://results.png")
    await ctx.send(embed=final_embed, file=file)

def generate_wheel_frame(winning_wedge, cost, reward):
    img = Image.new("RGB", (1200, 1200), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (1180, 1180)], outline="#334155", width=12)
    draw.ellipse([(200, 200), (1000, 1000)], fill="#1e293b", outline="#eab308", width=24)
    
    wedges = [
        ("JACKPOT", "#ef4444"), ("$500", "#3b82f6"), ("$2,500", "#10b981"),
        ("$0", "#64748b"), ("$10,000", "#a855f7"), ("$1,000", "#f97316")
    ]
    
    for i, (text, color) in enumerate(wedges):
        start_angle = i * (360 / len(wedges))
        end_angle = (i + 1) * (360 / len(wedges))
        draw.pieslice([(230, 230), (970, 970)], start=start_angle, end=end_angle, fill=color, outline="#0f172a", width=6)
        
        rad = math.radians(start_angle + 30)
        tx = int(600 + 260 * math.cos(rad))
        ty = int(600 + 260 * math.sin(rad))
        draw.text((tx - 40, ty - 20), text, fill="#ffffff", font=font_medium)
        
    draw.polygon([(600, 130), (560, 220), (640, 220)], fill="#eab308")
    draw.ellipse([(550, 550), (650, 650)], fill="#ffffff", outline="#eab308", width=10)
    
    draw.text((80, 1050), f"COST TO SPIN: ${cost:,}", fill="#94a3b8", font=font_medium)
    draw.text((700, 1050), f"WON: +${reward:,}", fill="#22c55e", font=font_medium)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="wheel.png")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = int(time.time())
    
    # Ensure structure exists
    if "daily_window_start" not in USER_DATA[user_id]:
        USER_DATA[user_id]["daily_window_start"] = 0
    if "daily_spin_count" not in USER_DATA[user_id]:
        USER_DATA[user_id]["daily_spin_count"] = 0
    if "daily_streak" not in USER_DATA[user_id]:
        USER_DATA[user_id]["daily_streak"] = 0
    if "last_streak_time" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_streak_time"] = 0

    # Reset daily window if 24 hours have passed
    if current_time - USER_DATA[user_id]["daily_window_start"] >= 86400:
        USER_DATA[user_id]["daily_window_start"] = current_time
        USER_DATA[user_id]["daily_spin_count"] = 0

    # Streak logic: Reset if 48 hours have passed (2 days)
    if current_time - USER_DATA[user_id]["last_streak_time"] > 172800:
        USER_DATA[user_id]["daily_streak"] = 0
    
    # Prevent double claiming within the same 24 hour window
    if current_time - USER_DATA[user_id]["last_streak_time"] < 86400:
        await ctx.send("❌ You already claimed your daily reward! Come back tomorrow.")
        return

    spin_cost = 1000 * (2 ** USER_DATA[user_id]["daily_spin_count"])

    if USER_DATA[user_id]["balance"] < spin_cost:
        embed = discord.Embed(
            title="❌ Insufficient Chips", 
            description=f"Spinning costs **{spin_cost:,}** chips.\nYour Current Balance: **{USER_DATA[user_id]['balance']:,}** chips.", 
            color=0xff0000
        )
        await ctx.send(embed=embed)
        return

    USER_DATA[user_id]["balance"] -= spin_cost
    USER_DATA[user_id]["daily_spin_count"] += 1
    USER_DATA[user_id]["daily_streak"] += 1
    USER_DATA[user_id]["last_streak_time"] = current_time

    daily_reward = random.randint(1000, 2500)
    
    # Add Streak Bonuses
    streak_bonus = 0
    if USER_DATA[user_id]["daily_streak"] % 7 == 0:
        streak_bonus = 5000
    elif USER_DATA[user_id]["daily_streak"] % 4 == 0:
        streak_bonus = 2000
    
    total_reward = daily_reward + streak_bonus
    await apply_gambling_winnings(user_id, total_reward)
    await save_user_data() 

    prize_pool = [1000, 1250, 1500, 1750, 2000, 2250, 2500, 1100, 1350, 1600, 1850, 2100]
    target_index = random.randint(0, len(prize_pool) - 1)
    prize_pool[target_index] = daily_reward

    slice_count = len(prize_pool)
    slice_arc = 360 / slice_count
    target_rotation = (270 - (target_index * slice_arc) - (slice_arc / 2)) % 360

    frames = []
    total_frames = 30
    extra_spins = 3 * 360 

    for f in range(total_frames):
        t = f / (total_frames - 1)
        factor = 1 - (1 - t) ** 3 
        animated_angle = (extra_spins + target_rotation) * factor

        img = Image.new("RGB", (300, 300), color=(15, 18, 24))
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        draw.ellipse([15, 15, 285, 285], fill=(40, 45, 55), outline=(230, 190, 60), width=5)

        for i, payout in enumerate(prize_pool):
            seg_start = animated_angle + (i * slice_arc)
            seg_end = seg_start + slice_arc
            
            color_wedge = (46, 139, 87) if i % 2 == 0 else (70, 130, 180)
            draw.pieslice([25, 25, 275, 275], start=seg_start, end=seg_end, fill=color_wedge, outline=(30, 35, 45), width=1)
            
            rad = math.radians(seg_start + (slice_arc / 2))
            text_x = 150 + int(90 * math.cos(rad))
            text_y = 150 + int(90 * math.sin(rad))
            draw.text((text_x, text_y), f"${payout}", fill=(255, 255, 255), font=font, anchor="mm")

        draw.ellipse([120, 120, 180, 180], fill=(220, 220, 220), outline=(100, 100, 100), width=2)
        draw.polygon([(150, 38), (142, 14), (158, 14)], fill=(255, 69, 0))

        frames.append(img)

    final_frame = frames[-1]
    for _ in range(20):
        frames.append(final_frame)

    final_buffer = io.BytesIO()
    frames[0].save(final_buffer, format="GIF", save_all=True, append_images=frames[1:], duration=70)
    final_buffer.seek(0)
    file = discord.File(fp=final_buffer, filename="daily.gif")

    next_spin_cost = 1000 * (2 ** USER_DATA[user_id]["daily_spin_count"])
    time_left = 86400 - (current_time - USER_DATA[user_id]["daily_window_start"])
    hours_left = max(0, time_left // 3600)
    mins_left = max(0, (time_left % 3600) // 60)

    embed = discord.Embed(
        title="🎁 Wheel Spin Complete 🎁", 
        description=f"Spent **{spin_cost:,}** chips to spin!\nLanded on and added **+${daily_reward:,}** chips.\nStreak Bonus: **+${streak_bonus:,}**", 
        color=0x00ff00
    )
    embed.add_field(name="🔥 Current Streak", value=f"**{USER_DATA[user_id]['daily_streak']}** days", inline=True)
    embed.add_field(name="💵 Current Funds", value=f"**{USER_DATA[user_id]['balance']:,}** chips", inline=True)
    embed.add_field(name="🔄 Next Spin Cost", value=f"**{next_spin_cost:,}** chips", inline=False)
    embed.add_field(name="⏱️ Price Reset In", value=f"**{hours_left}h {mins_left}m**", inline=False)
    embed.set_image(url="attachment://daily.gif")
    await ctx.send(file=file, embed=embed)

# ==============================================================================
# 2. INTERACTIVE SCRATCH CARD SYSTEM
# ==============================================================================

# Ensure you have a font that supports emojis loaded
# Example: font_large = ImageFont.truetype("seguiemj.ttf", 80)

# Ensure you load a font file that supports emojis, e.g., 'seguiemj.ttf'
font_emoji = ImageFont.truetype("seguisym.ttf", 80)

class ScratchCardView(discord.ui.View):
    def __init__(self, author_id, bet, matrix, vip_active):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.bet = bet
        self.matrix = matrix
        self.vip_active = vip_active
        self.revealed = [False] * 9
        self.clicks = 0

    async def update_scratch_canvas(self, interaction: discord.Interaction):
        img = Image.new("RGB", (900, 900), "#1e293b")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (880, 880)], outline="#a855f7", width=12)
        
        for i in range(9):
            row = i // 3
            col = i % 3
            x1, y1 = 60 + col * 270, 60 + row * 270
            
            if self.revealed[i]:
                draw.rectangle([(x1, y1), (x1 + 240, y1 + 240)], fill="#0f172a", outline="#a855f7", width=6)
                if self.matrix[i] == "⭐":
                    draw.ellipse([(x1 + 60, y1 + 60), (x1 + 180, y1 + 180)], fill="#eab308", outline="#854d0e", width=10)
                    draw.ellipse([(x1 + 75, y1 + 75), (x1 + 165, y1 + 165)], fill="#fbbf24", outline="#b45309", width=6)
                    draw.ellipse([(x1 + 85, y1 + 85), (x1 + 155, y1 + 155)], fill="#fde047", outline="#854d0e", width=4)
                    draw.text((x1 + 105, y1 + 90), "$", fill="#854d0e", font=font_large)
                else:
                    text_w = draw.textlength(self.matrix[i], font=font_emoji)
                    draw.text((x1 + 120 - (text_w / 2), y1 + 80), self.matrix[i], fill="#ffffff", font=font_emoji)
            else:
                draw.rectangle([(x1, y1), (x1 + 240, y1 + 240)], fill="#64748b", outline="#cbd5e1", width=6)
                text_w = draw.textlength("X", font=font_large)
                draw.text((x1 + 120 - (text_w / 2), y1 + 80), "X", fill="#ffffff", font=font_large)
                
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file_img = discord.File(buffer, filename="scratch.png")
        
        if self.clicks >= 3:
            self.stop()
            opened_items = [self.matrix[idx] for idx in range(9) if self.revealed[idx]]
            distinct = {item: opened_items.count(item) for item in set(opened_items)}
            
            winnings = 0
            if any(count == 3 for count in distinct.values()):
                match_symbol = [sym for sym, count in distinct.items() if count == 3][0]
                mult = {"🍒": 3, "💎": 10, "🍀": 5, "⭐": 2}.get(match_symbol, 2)
                if self.vip_active: mult *= 2
                winnings = self.bet * mult
                USER_DATA[self.author_id]["balance"] += winnings
                USER_DATA[self.author_id]["net_earnings"] += winnings
                res_str = f"🎉 **MATCH! 3/3 [{match_symbol}]! You won ${winnings:,} chips!**"
            elif any(count == 2 for count in distinct.values()):
                winnings = self.bet * 2
                USER_DATA[self.author_id]["balance"] += winnings
                USER_DATA[self.author_id]["net_earnings"] += winnings
                res_str = f"🎉 **MATCH! 2/3! You won ${winnings:,} chips!**"
            else:
                res_str = f"❌ **No Match! The items revealed were: {' '.join(opened_items)}.**"
                
            await interaction.message.edit(content=res_str, attachments=[file_img], view=None)
        else:
            await interaction.message.edit(attachments=[file_img], view=self)

    def register_click(self, idx):
        self.revealed[idx] = True
        self.clicks += 1
        for btn in self.children:
            if btn.custom_id == f"scratch_{idx}":
                btn.disabled = True
                btn.style = discord.ButtonStyle.secondary
                btn.label = self.matrix[idx]

    async def check_user(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ **This is not your scratch card profile session.**", ephemeral=True)
            return False
        await interaction.response.defer()
        return True

    @discord.ui.button(label="🗳️ 1", style=discord.ButtonStyle.primary, custom_id="scratch_0", row=0)
    async def b0(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(0); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 2", style=discord.ButtonStyle.primary, custom_id="scratch_1", row=0)
    async def b1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(1); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 3", style=discord.ButtonStyle.primary, custom_id="scratch_2", row=0)
    async def b2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(2); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 4", style=discord.ButtonStyle.primary, custom_id="scratch_3", row=1)
    async def b3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(3); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 5", style=discord.ButtonStyle.primary, custom_id="scratch_4", row=1)
    async def b4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(4); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 6", style=discord.ButtonStyle.primary, custom_id="scratch_5", row=1)
    async def b5(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(5); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 7", style=discord.ButtonStyle.primary, custom_id="scratch_6", row=2)
    async def b6(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(6); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 8", style=discord.ButtonStyle.primary, custom_id="scratch_7", row=2)
    async def b7(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(7); await self.update_scratch_canvas(interaction)
    @discord.ui.button(label="🗳️ 9", style=discord.ButtonStyle.primary, custom_id="scratch_8", row=2)
    async def b8(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_user(interaction): self.register_click(8); await self.update_scratch_canvas(interaction)

@bot.command()
async def scratch(ctx, bet: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 5:
        remaining = int(5 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before purchasing another ticket.")
    
    if bet < 100:
        await ctx.send("❌ **Minimum wager for a lottery scratch card ticket purchase is $100.**")
        return
    if USER_DATA[user_id]["balance"] < bet:
        await ctx.send("❌ **Insufficient funds available to purchase this scratch ticket card.**")
        return
        
    USER_DATA[user_id]["balance"] -= bet
    USER_DATA[user_id]["net_earnings"] -= bet
    USER_DATA[user_id]["scratch_history"] += 1
    USER_DATA[user_id]["total_games"] += 1
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await add_xp(user_id, 1)
    await save_user_data()
    
    pool = ["🍒", "💎", "🍀", "⭐"]
    matrix = [random.choice(pool) for _ in range(9)]
    
    if random.random() < 0.28:
        winning_sym = random.choice(pool)
        indices = random.sample(range(9), 3)
        for idx in indices:
            matrix[idx] = winning_sym
            
    img = Image.new("RGB", (900, 900), "#1e293b")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (880, 880)], outline="#a855f7", width=12)
    for i in range(9):
        row = i // 3
        col = i % 3
        x1, y1 = 60 + col * 270, 60 + row * 270
        draw.rectangle([(x1, y1), (x1 + 240, y1 + 240)], fill="#64748b", outline="#cbd5e1", width=6)
        text_w = draw.textlength("X", font=font_large)
        draw.text((x1 + 120 - (text_w / 2), y1 + 80), "X", fill="#ffffff", font=font_large)
        
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file_img = discord.File(buffer, filename="scratch.png")
    
    vip_active = USER_DATA[user_id].get("vip_status", False)
    view = ScratchCardView(user_id, bet, matrix, vip_active)
    await ctx.send(content="🎟️ **Scratch Card Purchased! Reveal exactly 3 panels. Match 3 symbols to win!**", file=file_img, view=view)


# ==============================================================================
# 3. CRASH MULTIPLIER RISKY ACCELERATION GAME
# ==============================================================================

class CrashGameView(discord.ui.View):
    def __init__(self, author_id, bet, crash_point, vip_active):
        super().__init__(timeout=45.0)
        self.author_id = author_id
        self.bet = bet
        self.crash_point = crash_point
        self.vip_active = vip_active
        self.current_mult = 1.0
        self.cashed_out = False

    @discord.ui.button(label="💥 CASH OUT", style=discord.ButtonStyle.danger, custom_id="crash_claim")
    async def crash_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ **This is not your flight vector module.**", ephemeral=True)
            return
        if self.current_mult >= self.crash_point or self.cashed_out:
            await interaction.response.send_message("❌ **Round has already concluded.**", ephemeral=True)
            return
            
        self.cashed_out = True
        self.stop()
        await interaction.response.defer()
        
        final_mult = self.current_mult
        if self.vip_active:
            final_mult *= 2
            
        winnings = int(self.bet * final_mult)
        USER_DATA[self.author_id]["balance"] += winnings
        USER_DATA[self.author_id]["net_earnings"] += winnings
        
        img = Image.new("RGB", (1000, 500), "#0f172a")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (980, 480)], outline="#22c55e", width=10)
        draw.text((100, 180), f"SUCCESSFUL ESCAPE: {self.current_mult:.2f}X", fill="#22c55e", font=font_xl)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file_img = discord.File(buffer, filename="crash.png")
        
        msg_str = f"✅ **Cashed out safely at {self.current_mult:.2f}x!** Received **${winnings:,}** chips!"
        if self.vip_active:
            msg_str += " **[VIP 2X PAYOUT APPLIED]**"
        await interaction.message.edit(content=msg_str, attachments=[file_img], view=None)

@bot.command()
async def crash(ctx, bet: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 20:
        remaining = int(20 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before initiating flight.")
    
    if bet < 10:
        await ctx.send("❌ **Wager minimum must be at least $10 chips.**")
        return
    if USER_DATA[user_id]["balance"] < bet:
        await ctx.send("❌ **You do not possess enough chips to initiate telemetry.**")
        return
        
    USER_DATA[user_id]["balance"] -= bet
    USER_DATA[user_id]["net_earnings"] -= bet
    USER_DATA[user_id]["crash_history"] += 1
    USER_DATA[user_id]["total_games"] += 1
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await add_xp(user_id, 1)
    await save_user_data()
    
    if random.random() < 0.12:
        crash_point = 1.0
    else:
        crash_point = round(random.uniform(1.05, 7.50), 2)
        
    vip_active = USER_DATA[user_id].get("vip_status", False)
    view = CrashGameView(user_id, bet, crash_point, vip_active)
    
    img = Image.new("RGB", (1000, 500), "#0f172a")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (980, 480)], outline="#ca8a04", width=10)
    draw.text((100, 180), "LAUNCHING MULTIPLIER... 1.00X", fill="#ca8a04", font=font_xl)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file_img = discord.File(buffer, filename="crash.png")
    
    game_msg = await ctx.send(content=f"🚀 **Crash rocket initiated by {ctx.author.mention}! Payout climbing...**", file=file_img, view=view)
    
    steps = [1.10, 1.30, 1.60, 2.00, 2.50, 3.20, 4.00, 5.00, 6.50, 7.50]
    for current_val in steps:
        await asyncio.sleep(1.8)
        if view.cashed_out:
            return
            
        if current_val >= crash_point:
            view.stop()
            img = Image.new("RGB", (1000, 500), "#0f172a")
            draw = ImageDraw.Draw(img)
            draw.rectangle([(20, 20), (980, 480)], outline="#ef4444", width=10)
            draw.text((100, 180), f"CRASHED AT {crash_point:.2f}X", fill="#ef4444", font=font_xl)
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            file_img = discord.File(buffer, filename="crash.png")
            
            await game_msg.edit(content=f"💥 **BOOM! The graph crashed at {crash_point:.2f}x!** {ctx.author.mention} lost their wager of **${bet:,}** chips.", attachments=[file_img], view=None)
            return
            
        view.current_mult = current_val
        img = Image.new("RGB", (1000, 500), "#0f172a")
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (980, 480)], outline="#ca8a04", width=10)
        draw.text((100, 180), f"CURRENT FLIGHT: {current_val:.2f}X", fill="#ca8a04", font=font_xl)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file_img = discord.File(buffer, filename="crash.png")
        
        await game_msg.edit(attachments=[file_img], view=view)

class PageJumpModal(discord.ui.Modal, title="Jump to Page"):
    page_input = discord.ui.TextInput(label="Page Number", placeholder="Enter a number...", min_length=1, max_length=3)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page = int(self.page_input.value)
            if 1 <= page <= self.view.total_pages:
                self.view.current_page = page
                await self.view.update_view(interaction)
            else:
                await interaction.response.send_message("Invalid page number.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid integer.", ephemeral=True)

class LeaderboardView(discord.ui.View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.bot = bot
        self.current_page = 1
        self.category = "balance"
        self.scope = "global"
        self.total_pages = self.calculate_total_pages()

    def calculate_total_pages(self):
        if self.scope == "server" and self.ctx.guild:
            member_ids = {str(m.id) for m in self.ctx.guild.members}
            filtered_data = {k: v for k, v in USER_DATA.items() if str(k) in member_ids}
            return max(1, (len(filtered_data) + 4) // 5)
        return max(1, (len(USER_DATA) + 4) // 5)

    @discord.ui.select(placeholder="Select Scope", options=[
        discord.SelectOption(label="Global Leaderboard", value="global", emoji="🌐"),
        discord.SelectOption(label="Server Leaderboard", value="server", emoji="🏠")
    ], row=0)
    async def select_scope(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.scope = select.values[0]
        self.current_page = 1
        self.total_pages = self.calculate_total_pages()
        await self.update_view(interaction)

    @discord.ui.select(placeholder="Select Category", options=[
        discord.SelectOption(label="Cash", value="balance", emoji="💵"),
        discord.SelectOption(label="Debt", value="loan_debt", emoji="💸"),
        discord.SelectOption(label="Wins", value="wins", emoji="🏆")
    ], row=1)
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.category = select.values[0]
        self.current_page = 1
        await self.update_view(interaction)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple, row=2)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages if self.current_page == 1 else self.current_page - 1
        await self.update_view(interaction)

    @discord.ui.button(label="Jump", style=discord.ButtonStyle.secondary, row=2)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PageJumpModal(self))

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple, row=2)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1 if self.current_page == self.total_pages else self.current_page + 1
        await self.update_view(interaction)

    async def update_view(self, interaction: discord.Interaction):
        file = generate_leaderboard_image(self.current_page, self.category, self.scope, self.ctx, self.bot)
        await interaction.response.edit_message(attachments=[file], view=self)

def format_number(num):
    suffixes = [
        (10**3, "K"), (10**6, "M"), (10**9, "B"), (10**12, "T"), 
        (10**15, "Qd"), (10**18, "Qt"), (10**21, "Sx"), (10**24, "Sp"), 
        (10**27, "Oc"), (10**30, "No"), (10**33, "Dc"), (10**36, "Ud"),
        (10**39, "Dd"), (10**42, "Td"), (10**45, "Qtd"), (10**48, "Qnd"),
        (10**51, "Sd"), (10**54, "St"), (10**57, "Od"), (10**60, "Nd"),
        (10**63, "Vg"), (10**66, "Uvg"), (10**69, "Dvg"), (10**72, "Tvg"),
        (10**75, "Qtvg"), (10**78, "Sxvg"), (10**81, "Spvg"), (10**84, "Ocvg"),
        (10**87, "Novg"), (10**90, "Tg"), (10**93, "Utg"), (10**96, "Dtg"),
        (10**99, "Ttg"), (10**102, "Qtg"), (10**105, "Sxtg"), (10**108, "Sptg"),
        (10**111, "Octg"), (10**114, "Notg"), (10**117, "Qag")
    ]
    if num >= 10**120:
        return "Infinite"
    for value, suffix in reversed(suffixes):
        if num >= value:
            return f"{num / value:.2f}{suffix}"
    return f"{num:,.0f}"

def generate_leaderboard_image(page, category, scope, ctx, bot):
    start = (page - 1) * 5
    
    source_data = USER_DATA
    if scope == "server" and ctx.guild:
        member_ids = {str(m.id) for m in ctx.guild.members}
        source_data = {k: v for k, v in USER_DATA.items() if str(k) in member_ids}
        
    sorted_players = sorted(source_data.items(), key=lambda x: x[1].get(category, 0), reverse=True)[start:start+5]
    
    img = Image.new("RGB", (1200, 800), "#0b0f19")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (1180, 780)], outline="#eab308", width=10)
    
    title_text = f"{scope.upper()} RANKINGS: {category.upper()}"
    draw.text((350, 50), title_text, fill="#ffffff", font=font_medium)
    
    y_offset = 180
    for rank_idx, (uid, records) in enumerate(sorted_players, start + 1):
        user_obj = bot.get_user(int(uid))
        username = user_obj.name if user_obj else f"User {uid}"
        val = records.get(category, 0)
        
        display_val = format_number(val) if category == "balance" else f"{val:,}"
        
        str_uid = str(uid)
        custom_tag = ""
        has_named_tag = False
        highlight_color = "#ffffff"

        current_xp = records.get("xp", 0)
        calc_level = int((current_xp / 4) ** 0.5) if current_xp > 0 else 1
        if calc_level < 1:
            calc_level = 1

        if str_uid == "978024161689608202":
            custom_tag = " [OWNER]"
            has_named_tag = True
            highlight_color = "#ef4444"
        elif str_uid == "962451361058930780":
            custom_tag = " [CO-OWNER]"
            has_named_tag = True
            highlight_color = "#3b82f6"
        elif str_uid in ["870849419065577503", "899343022565757059"]:
            custom_tag = " [DEV]"
            has_named_tag = True
            highlight_color = "#22c55e"
        elif str_uid == "1161762623382110208":
            custom_tag = " [POTATO]"
            has_named_tag = True
            highlight_color = "#eab308"
        elif str_uid == "941049240585662495":
            custom_tag = " [GOD]"
            has_named_tag = True
            highlight_color = "#eab308"
        elif str_uid == "921465683492106290":
            custom_tag = f" [ULTRA] [LVL {calc_level}]"
            has_named_tag = True
            highlight_color = "#a855f7"
        elif str_uid == "1229921852332441731":
            custom_tag = " [GRACIAS]"
            has_named_tag = True
            highlight_color = "#a855f7"
        elif records.get("vip_status", False) or records.get("upgrades", {}).get("vip_lounge", 0) > 0:
            custom_tag = " [VIP]"
            has_named_tag = True
            highlight_color = "#f97316"

        if not has_named_tag:
            custom_tag = f" [LVL {calc_level}]"

        local_font = font_medium
        font_size = local_font.size if hasattr(local_font, "size") else 32
        font_path = local_font.path if hasattr(local_font, "path") else None
        
        full_name_text = f"#{rank_idx} | {username.upper()}{custom_tag}"
        text_bbox = draw.textbbox((100, y_offset), full_name_text, font=local_font)
        text_right_edge = text_bbox[2]
        coin_left_edge = 750

        if text_right_edge >= coin_left_edge:
            if has_named_tag and f" [LVL {calc_level}]" in custom_tag:
                custom_tag = custom_tag.replace(f" [LVL {calc_level}]", "")
                full_name_text = f"#{rank_idx} | {username.upper()}{custom_tag}"
                text_bbox = draw.textbbox((100, y_offset), full_name_text, font=local_font)
                text_right_edge = text_bbox[2]

            while text_right_edge >= coin_left_edge and font_size > 8:
                font_size -= 1
                if font_path:
                    local_font = ImageFont.truetype(font_path, font_size)
                else:
                    break
                text_bbox = draw.textbbox((100, y_offset), full_name_text, font=local_font)
                text_right_edge = text_bbox[2]

        draw.text((100, y_offset), full_name_text, fill=highlight_color, font=local_font)
        draw.text((750, y_offset), f"{display_val} {'Chips' if category == 'balance' else ''}", fill="#22c55e", font=font_medium)
        y_offset += 110
        
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="leaderboard.png")

@bot.command()
async def leaderboard(ctx):
    if not USER_DATA:
        await ctx.send("❌ **No active player analytics registered inside database nodes.**")
        return
    view = LeaderboardView(ctx, bot)
    file = generate_leaderboard_image(1, "balance", "global", ctx, bot)
    await ctx.send(file=file, view=view)

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot_ref):
        self.bot_ref = bot_ref
        options = [
            discord.SelectOption(label="Home Menu", description="Main help overview screen", emoji="🏠"),
            discord.SelectOption(label="Commands", description="General utility and economy commands", emoji="🛠️"),
            discord.SelectOption(label="Gambling Commands", description="Risk chips and win big", emoji="🎰"),
            discord.SelectOption(label="Settings & Profile", description="Customize preferences and 2FA", emoji="⚙️"),
            discord.SelectOption(label="Relationship Commands", description="Manage your friends list", emoji="🧡")
        ]
        super().__init__(placeholder="Choose a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selection = self.values[0]
        self.view.current_category = selection
        self.view.current_page = 0
        
        embed = self.view.get_embed()
        self.view.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, author_id, bot_ref):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.bot_ref = bot_ref
        self.current_category = "Home Menu"
        self.current_page = 0
        
        self.add_item(HelpDropdown(self.bot_ref))
        
        self.commands_data = {
            "Commands": [
                {
                    "name": "📊 !leaderboard",
                    "value": "**What it Does:**\nGenerates a custom, high-resolution graphics card image displaying top-performing players across different economic indexes. It natively calculates ranks, account levels, and active prestige titles in real-time.\n\n**How to Use & Controls:**\nType `!leaderboard` to summon the graphical system dashboard. From there, you can interact with the menu controls:\n• **Select Scope Dropdown:** Toggle between `🌐 Global Leaderboard` (compares you against every single user across the entire bot network) and `🏠 Server Leaderboard` (filters ranks strictly to members inside your current Discord server).\n• **Select Category Dropdown:** Change what metric you are sorting by. You can look up `💵 Cash` (wallet balances), `💸 Debt` (outstanding loan balances), or `🏆 Wins` (total gaming victories count).\n• **Navigation Arrows (⬅️ / ➡️):** Flip through pages to view players ranked further down the ladder. The menu automatically loops back to the start if you click next on the final page.\n• **Jump Button:** Click this to open a text box where you can manually enter any specific page number to instantly teleport to that section of the rankings.\n\n**Player Tags to Look Out For:**\nWhile browsing, you will spot special colored brackets next to names representing user authority or milestones:\n• `[OWNER]` (Red)\n• `[CO-OWNER]` (Blue)\n• `[DEV]` (Green)\n• `[VIP]` (Orange)\n• `[POTATO]` or `[GOD]` (Yellow)\n• `[ULTRA]` or `[GRACIAS]` (Purple)\n• Standard users will display their calculated level based on active account XP progression: `[LVL X]`"
                },
                {
                    "name": "💰 !pay <@member> <amount>",
                    "value": "**What it Does:**\nAllows you to securely transfer currency directly from your wallet to another player's account.\n\n**How to Use:**\nType `!pay` followed by a user mention and the exact number of coins. Example: `!pay @User 500`.\n\n**Outcomes & Restrictions:**\n• **Success:** The money is immediately deducted from your profile and added to theirs.\n• **2FA Prompt:** If you have Transfer 2FA enabled, the transfer will pause until you verify a 6-digit code sent to your private DMs.\n• **Failure:** The transaction will fail if you don't have enough money, if the user has disabled incoming payments, or if they restrict payments to friends only and you are not on their friend list."
                },
                {
                    "name": "🥷 !rob <@member>",
                    "value": "**What it Does:**\nAn aggressive, high-stakes command where you attempt to sneak into another user's wallet to steal a random portion of their cash reserves.\n\n**How to Use:**\nType `!rob` followed by the mention of your target. Example: `!rob @User`.\n\n**Outcomes:**\n• **Success:** You successfully steal a fraction of their cash and add it to your balance.\n• **Failure:** You get caught by security systems and are forced to pay a steep financial penalty fine directly to the victim or security forces.\n• **Immunity:** Fails automatically if either you or your target has Passive Mode enabled."
                },
                {
                    "name": "📅 !daily",
                    "value": "**What it Does:**\nYour recurring login progression allowance. It features an integrated streak modifier that increases the rewards you get for every consecutive day you return to claim it.\n\n**How to Use:**\nSimply run `!daily` to claim your allowance.\n\n**Outcomes:**\nYou can run this command as many times as you want throughout the day; however, the base cost starts at $1,000 and doubles on every single attempt. The price scaling resets and your login streak timer updates exactly 24 hours after your very first claim of the day."
                }
            ],
            "Gambling Commands": [
                {
                    "name": "🃏 !bj",
                    "value": "**What it Does:**\nA classic casino game of Blackjack. You can choose to play completely solo against the dealer (the bot) or set up a multiplayer table so your friends can sit down and play alongside you.\n\n**How to Use:**\nRun `!bj` to launch the game creation lobby interface.\n\n**Outcomes:**\nYour goal is to get a hand total closer to 21 than the dealer without going over. Normal wins pay out 2x your wager, hitting a natural Blackjack pays out 2.5x your wager, and tying with the dealer returns your wager safely."
                },
                {
                    "name": "📈 !crash <amount>",
                    "value": "**What it Does:**\nA continuous multiplier multiplier game where a multiplier curve climbs higher and higher. You must decide exactly when to cash out before it completely collapses.\n\n**How to Use:**\nStart the game by risking a baseline stake. Example: `!crash 1000`.\n\n**Outcomes:**\n• **Cash Out:** If you click cash out before the crash, your wager is multiplied by the exact number shown on screen.\n• **Crash:** The multiplier can crash at any point, including right at 1.0x. If it crashes before you click cash out, you lose 100% of your wager."
                },
                {
                    "name": "🪙 !coinflip <amount> <heads or tails>",
                    "value": "**What it Does:**\nA pure 50/50 double-or-nothing game based on a virtual coin toss.\n\n**How to Use:**\nEnter your wager along with your choice of heads or tails. Example: `!coinflip 500 heads`.\n\n**Outcomes:**\n• **Win:** The coin lands on your selection, granting you a 2x payout of your total wager.\n• **Loss:** The coin lands on the opposite face, and your wager is permanently lost."
                },
                {
                    "name": "🎫 !scratch <amount>",
                    "value": "**What it Does:**\nPurchases an instant scratch card ticket where you uncover concealed panels to try and line up identical prize symbols.\n\n**How to Use:**\nSpecify the cost tier of the scratch card you want to buy. Example: `!scratch 300`.\n\n**Outcomes:**\n• **3/3 Matches:** Ultimate match jackpot! You win 3x your card purchase price.\n• **2/3 Matches:** Minor combination match! You win 2x your card purchase price.\n• **1/3 Matches:** Loss penalty! The house takes your wager and fines you an extra 2x your card price.\n• **0/3 Matches:** Complete bust! The house takes your wager and fines you an extra 3x your card price."
                },
                {
                    "name": "🎲 !diceduel <amount>",
                    "value": "**What it Does:**\nA quick head-to-head single die rolling contest pitching your luck directly against the bot.\n\n**How to Use:**\nSet your entry stake. Example: `!diceduel 400`.\n\n**Outcomes:**\n• **Win:** You roll a higher numerical value than the bot, yielding a 2x payout of your bet.\n• **Loss:** You roll a lower numerical value than the bot, losing your entire bet.\n• **Tie:** Both you and the bot roll the exact same number. The match is declared a draw, and your funds are refunded."
                },
                {
                    "name": "↕️ !highlow <amount>",
                    "value": "**What it Does:**\nA prediction game where you are shown a random base number between 1 and 999 and must guess whether the next hidden number will be higher or lower.\n\n**How to Use:**\nEnter your starting bet. Example: `!highlow 500`.\n\n**Outcomes:**\n• **Correct Guess:** If your prediction is correct, you win a premium high-tier payout of 6x your wager.\n• **Incorrect Guess:** If your prediction is wrong, you fail the challenge and are penalized a loss equal to 3x your wager."
                },
                {
                    "name": "🎱 !keno <amount>",
                    "value": "**What it Does:**\nA standard casino lotto drawing game where you select a pool of numbers and check how many match the house results.\n\n**How to Use:**\nEnter your entry fee and choose up to 20 unique numbers ranging from 1 to 80. Example: `!keno 1000`.\n\n**Outcomes:**\nThe bot draws 20 random winning numbers. Your financial payout scales incrementally based on how many numbers you successfully matched. If you manage to achieve zero matches across your entire selection, you lose your bet."
                },
                {
                    "name": "💣 !mines <amount> <mine amount>",
                    "value": "**What it Does:**\nA strategic mining game played on a hidden 5x5 grid (spaces 0 to 24). You must uncover safe tiles while completely avoiding hidden explosive mines.\n\n**How to Use:**\nProvide your wager along with the total number of bombs you want hidden on the board. Example: `!mines 500 5`.\n\n**Outcomes:**\nEach safe tile you uncover dramatically raises your current cash-out multiplier. You can click to cash out and claim your earnings at any time. If you click a tile that contains a mine, your board explodes, instantly ending the game and losing your entire bet."
                },
                {
                    "name": "🪵 !plinko <amount>",
                    "value": "**What it Does:**\nDrops a physics-based ball down a triangular peg board where it deflects randomly into various multiplier slots at the bottom.\n\n**How to Use:**\nInput your stake per ball drop. Example: `!plinko 300`.\n\n**Outcomes:**\nThe pegs bounce the ball away from the center. Slots in the exact middle have lower values, while slots on the far outer edges have massive multipliers. You can unlock and purchase permanent board upgrades inside the `!shop` command to raise the value of outer edge multipliers."
                },
                {
                    "name": "🎰 !slots <amount>",
                    "value": "**What it Does:**\nSpins a high-volatility 3-reel slot machine looking for matching slot item configurations.\n\n**How to Use:**\nInput your cost per spin. Example: `!slots 200`.\n\n**Outcomes:**\n• **3/3 Matching Symbols:** Hits the ultimate slot machine grand jackpot, paying out a massive 170x your spin cost.\n• **2/3 Matching Symbols:** Hits a partial combination line, paying out a strong 17x your spin cost.\n• **0/3 Matching Symbols:** No symbols align correctly, resulting in a total loss of your spin cost."
                },
                {
                    "name": "🎡 !roulette <amount> <color/number/high/low/odd/even>",
                    "value": "**What it Does:**\nAllows you to place bets on a standard roulette wheel utilizing a wide range of different betting categories.\n\n**How to Use:**\nInput your wager followed by your market prediction. Examples: `!roulette 500 red`, `!roulette 1000 14`, or `!roulette 300 even`.\n\n**Outcomes:**\nThe wheel spins and lands on a pocket. If the winning pocket matches your specific color, exact number, range, or numerical parity, you win 2x your bet. If it misses, your wager is collected by the house."
                },
                {
                    "name": "🏎️ !race <lane 1-5> <amount>",
                    "value": "**What it Does:**\nA high-chaos racing simulator where five separate lanes compete to cross the finish line first.\n\n**How to Use:**\nPick your lane choice (numbers 1 through 5) and set your backing stake. Example: `!race 3 1000`.\n\n**Outcomes:**\nFive racers dash across the screen in real-time. Because the simulation variables are completely chaotic, winning is incredibly rare and difficult. If your chosen lane manages to place first, you win a premium high-tier payout. If any other lane wins, your stake is lost."
                },
                {
                    "name": "🎲 !dice <amount> <guess>",
                    "value": "**What it Does:**\nA direct intuition challenge where you predict the exact single outcome of a rolled six-sided die.\n\n**How to Use:**\nEnter your wager and your guess from 1 to 6. Example: `!dice 500 4`.\n\n**Outcomes:**\n• **Correct Guess:** Successfully predicting the precise face pays out an optimized 5x your bet.\n• **Incorrect Guess:** Missing the number results in a harsh penalty, losing 2x your wagered amount to the house."
                }
            ],
            "Settings & Profile": [
                {
                    "name": "🔔 Toggle DM Notifications",
                    "value": "**What it Does:**\nControls whether the bot has permission to directly message your personal inbox with gameplay and profile notifications.\n\n**How to Use:**\nManaged directly inside your interactive `!settings` configurations panel.\n\n**Outcomes:**\n• **ON:** The bot will automatically send transaction logs, security updates, and automated event alerts straight to your DMs.\n• **OFF:** Silences the bot, completely blocking it from sending you direct messages."
                },
                {
                    "name": "👁️ Toggle Profile Visibility",
                    "value": "**What it Does:**\nControls the global privacy setting of your account statistics, net worth, and milestones.\n\n**How to Use:**\nToggle this option inside your main account settings dashboard.\n\n**Outcomes:**\n• **PUBLIC:** Any member in the server can look up your level, wallet balances, and leaderboard records.\n• **PRIVATE:** Restricts visibility, completely masking your profile metrics from other players."
                },
                {
                    "name": "🔒 Toggle Transfer 2FA",
                    "value": "**What it Does:**\nAdds a secure confirmation layer to your wallet to prevent unauthorized, accidental, or fraudulent coin transfers.\n\n**How to Use:**\nEnable the security flag inside your settings menu panel.\n\n**Outcomes:**\nWhen enabled, running `!pay` will temporarily halt your transfer. The bot will instantly generate a random 6-digit confirmation code and send it to your private DMs. You must reply and verify that code before the coins are officially moved."
                },
                {
                    "name": "🛡️ Toggle Passive Mode",
                    "value": "**What it Does:**\nOpt completely out of player-versus-player economy combat to protect your wallet balance from thieves.\n\n**How to Use:**\nSwitch the protection flag inside your settings menu.\n\n**Outcomes:**\n• **ON:** You are granted complete immunity from all incoming `!rob` attempts. However, this safety barrier also blocks you from using `!rob` on anyone else.\n• **OFF:** You enter the active economy ecosystem, meaning you can rob other non-passive players, but you can also be targeted by thieves."
                },
                {
                    "name": "💸 Cycle Pay Permissions",
                    "value": "**What it Does:**\nSets filtering rules to determine exactly who is allowed to send you money or initiate transfers to your wallet.\n\n**How to Use:**\nClick this option inside your settings panel to cycle through three distinct states.\n\n**Outcomes:**\n• **EVERYONE:** Any user across the server can transfer coins to you without restriction.\n• **FRIENDS ONLY:** Restricts incoming payments strictly to users verified on your personal friends list.\n• **DISABLED:** Completely blocks incoming coin transfers from all players."
                }
            ],
            "Relationship Commands": [
                {
                    "name": "🧡 !friend <@member>",
                    "value": "**What it Does:**\nEstablishes an official social link between your profile and another player on the bot network.\n\n**How to Use:**\nMention the specific user you want to connect with. Example: `!friend @User`.\n\n**Outcomes:**\nSends an outbound friend request. If they accept, you become verified friends. Being official friends allows you to join cooperative multiplayer blackjack tables and bypass strict 'Friends Only' payment filters."
                }
            ]
        }
        self.update_buttons()

    def get_embed(self):
        if self.current_category == "Home Menu":
            embed = discord.Embed(
                title="📚 Bot Command Documentation",
                description="Welcome to the help dashboard. Select a module category using the dropdown menu selection box down below to explore all available engine tools.",
                color=0x3b82f6
            )
            embed.add_field(name="Modules Available", value="• 🛠️ **Commands**\n• 🎰 **Gambling Commands**\n• ⚙️ **Settings & Profile**\n• 🧡 **Relationship Commands**", inline=False)
            return embed

        cmds = self.commands_data[self.current_category]
        total_cmds = len(cmds)
        max_pages = max(1, (total_cmds + 4) // 5)
        
        if self.current_page >= max_pages:
            self.current_page = max_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        colors = {"Commands": 0x3b82f6, "Gambling Commands": 0xeab308, "Settings & Profile": 0x4b5563, "Relationship Commands": 0xec4899}
        titles = {"Commands": "🛠️ General Utility & Economy Commands", "Gambling Commands": "🎰 Gambling & Economy Commands", "Settings & Profile": "⚙️ Settings & Customization Guide", "Relationship Commands": "🧡 Relationship & Social Commands"}
        descriptions = {
            "Commands": "A list of all primary economy and system commands. Use these to track rankings, pay peers, claim daily bonuses, or interact with other members.",
            "Gambling Commands": "A list of all available gambling and economy commands for the bot. Use these to risk chips, earn rewards, and manage your finances.",
            "Settings & Profile": "Manage your account settings by using `!settings`.",
            "Relationship Commands": "Make friends, play together, have a good time"
        }

        embed = discord.Embed(
            title=titles[self.current_category],
            description=descriptions[self.current_category],
            color=colors.get(self.current_category, 0x3b82f6)
        )

        start_idx = self.current_page * 5
        end_idx = start_idx + 5
        page_commands = cmds[start_idx:end_idx]

        for cmd in page_commands:
            embed.add_field(name=cmd["name"], value=cmd["value"], inline=False)

        embed.set_footer(text=f"Page {self.current_page + 1} of {max_pages}")
        return embed

    def update_buttons(self):
        if self.current_category == "Home Menu":
            self.prev_page.disabled = True
            self.next_page.disabled = True
            return

        cmds = self.commands_data[self.current_category]
        total_cmds = len(cmds)
        max_pages = max(1, (total_cmds + 4) // 5)

        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= max_pages - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⬅️", row=1)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        embed = self.get_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, emoji="➡️", row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        embed = self.get_embed()
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This interaction menu belongs to someone else.", ephemeral=True)
            return False
        return True

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📚 Bot Command Documentation",
        description="Welcome to the help dashboard. Select a module category using the dropdown menu selection box down below to explore all available engine tools.",
        color=0x3b82f6
    )
    embed.add_field(name="Modules Available", value="• 🛠️ **Commands**\n• 🎰 **Gambling Commands**\n• ⚙️ **Settings & Profile**\n• 🧡 **Relationship Commands**", inline=False)
    
    view = HelpView(ctx.author.id, bot)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def dice(ctx, bet: int = None, guess: int = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    # Custom Cooldown Check (3 seconds)
    now = time.time()
    last_use = USER_DATA[user_id].get("last_dice_time", 0)
    cooldown_duration = 3.0
    
    if now - last_use < cooldown_duration:
        remaining = round(cooldown_duration - (now - last_use), 1)
        await ctx.send(f"⏳ **Hold on!** You can use this command again in **{remaining}s**.")
        return

    if bet is None or guess is None:
        await ctx.send("❌ **Usage:** `!dice <bet> <guess (1-6)>`")
        return

    if bet <= 0:
        await ctx.send("❌ **Bet amount must be greater than 0!**")
        return

    if guess < 1 or guess > 6:
        await ctx.send("❌ **Your guess must be a number between 1 and 6!**")
        return

    current_balance = USER_DATA[user_id]["balance"]
    
    # Calculate potential maximum loss (2x the bet)
    max_loss = bet * 2
    if current_balance < max_loss:
        await ctx.send(f"❌ **You don't have enough chips to cover the risk!** You need at least **${max_loss:,}** (2x your bet) on hand to cover a loss, but your balance is **${current_balance:,}**.")
        return

    # Update cooldown timestamp now that validation has passed
    USER_DATA[user_id]["last_dice_time"] = now

    # Roll the 6-sided dice
    roll = random.randint(1, 6)
    
    # Custom dice emojis for aesthetic display
    dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    roll_emoji = dice_emojis.get(roll, "🎲")

    if guess == roll:
        winnings = bet * 5
        await apply_gambling_winnings(user_id, winnings)
        
        embed_win = discord.Embed(
            title="🎯 PERFECT GUESS! - YOU WIN",
            description=f"The dice rolled a **{roll}** {roll_emoji}!\n"
                        f"Your guess was **{guess}**.\n\n"
                        f"💰 **Payout:** +${winnings:,} chips (5x your bet)",
            color=0x22c55e
        )
        await ctx.send(embed=embed_win)
    else:
        loss = bet * 2
        USER_DATA[user_id]["balance"] -= loss
        await save_user_data()
        
        embed_lose = discord.Embed(
            title="❌ WRONG GUESS - YOU LOSE",
            description=f"The dice rolled a **{roll}** {roll_emoji}!\n"
                        f"Your guess was **{guess}**.\n\n"
                        f"📉 **Loss:** -${loss:,} chips (2x your bet)",
            color=0xef4444
        )
        await ctx.send(embed=embed_lose)

@bot.command()
async def dbg_set_vip(ctx, user: discord.Member, status: bool):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
        
    await ensure_user(user.id)
    USER_DATA[user.id]["vip_status"] = status
    await save_user_data()
    
    txt_status = "ENABLED" if status else "REVOKED"
    
    await ctx.send(f"⚙️ **VIP tier settings updated: Set {user.mention}'s 2x payout override profile flag to {txt_status}!**")
    await log_moderation_action("VIP_FLAG_TOGGLE", user.id, f"Admin updated VIP modifier status configuration settings flag matrix to **{txt_status}**.")

@bot.command()
async def animate(ctx):

    frames = []
    
    # Generate 10 frames with shifting colors
    for i in range(10):
        # Create a solid color image (R, G, B) shifting from dark to bright red
        img = Image.new("RGB", (200, 200), color=(i * 25, 0, 50))
        frames.append(img)
    
    # Save the sequence of frames into a bytes buffer as an animated GIF
    final_buffer = io.BytesIO()
    frames[0].save(
        final_buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,  # Duration of each frame in milliseconds     # 0 means the GIF loops infinitely
    )
    
    # Reset the buffer pointer to the beginning so discord can read it
    final_buffer.seek(0)
    
    # Send the animated GIF to the Discord channel
    await ctx.send(file=discord.File(fp=final_buffer, filename="animated.gif"))

@bot.command()
async def dbg_reset_daily(ctx, user: discord.Member):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
        
    await ensure_user(user.id)
    USER_DATA[user.id]["daily_cost"] = 1000
    await save_user_data()
    await ctx.send(f"⚙️ **Progressive tracking system refreshed: Reset {user.mention}'s next `!daily` spin purchase cost configuration threshold to base $1,000 chips.**")
    await log_moderation_action("DAILY_COST_RESET", user.id, "Admin reset individual progressive operational spinning cost baseline threshold matrix configuration back to $1,000 values directly.")

@bot.command()
async def dbg_money(ctx, action: str, member: discord.Member, amount: int = 0):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    await ensure_user(member.id)
    action_lower = action.lower()
    
    if action_lower == "add":
        if amount <= 0:
            await ctx.send("❌ **Please specify a positive amount to add.**")
            return
        USER_DATA[member.id]["balance"] += amount
        await save_user_data()
        await ctx.send(f"⚙️ **Added ${amount:,} chips to {member.mention}'s balance. New balance: ${USER_DATA[member.id]['balance']:,}**")
    
    elif action_lower == "remove":
        if amount <= 0:
            await ctx.send("❌ **Please specify a positive amount to remove.**")
            return
        USER_DATA[member.id]["balance"] = max(0, USER_DATA[member.id]["balance"] - amount)
        await save_user_data()
        await ctx.send(f"⚙️ **Removed ${amount:,} chips from {member.mention}'s balance. New balance: ${USER_DATA[member.id]['balance']:,}**")
    
    elif action_lower == "reset":
        USER_DATA[member.id]["balance"] = 5000
        await save_user_data()
        await ctx.send(f"⚙️ **Reset {member.mention}'s balance to the starting $5,000 chips.**")
    
    else:
        await ctx.send("❌ **Invalid action! Use `add`, `remove`, or `reset`.**")

RIGGED_ROULETTE = {}

@bot.command()
async def rig_roulette(ctx, target: str):
    target = target.lower()
    if target == "none":
        if ctx.author.id in RIGGED_ROULETTE:
            del RIGGED_ROULETTE[ctx.author.id]
        await ctx.send("✅ Roulette rigging has been disabled.")
    else:
        RIGGED_ROULETTE[ctx.author.id] = target
        await ctx.send(f"✅ Roulette rigged for: **{target.upper()}**")

@bot.command()
async def roulette(ctx, bet: str = None, space: str = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    await save_user_data() 

    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 15:
        remaining = int(15 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before playing roulette again.")

    if USER_DATA[user_id].get("trespassed", False):
        embed = discord.Embed(title="❌ Access Denied", description="You are **Trespassed** from this establishment. Security will not allow you to play.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    if bet is None or space is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You must specify both your bet amount and the space you are betting on.", color=0xff0000)
        embed.add_field(name="Correct Usage", value="`!roulette <bet_amount> <space>`\n`!roulette all <space>`", inline=False)
        embed.add_field(name="Valid Spaces", value="🔴 **red**\n⚫ **black**\n🟢 **green**\n🔢 Specific number: **0-36**\n⚖️ **even** / **odd**\n📦 **high** (19-36) / **low** (1-18)", inline=False)
        embed.add_field(name="Examples", value="`!roulette 500 red`\n`!roulette all 17`\n`!roulette 100 even`", inline=False)
        await ctx.send(embed=embed)
        return
    
    if bet.lower() == "all":
        bet_amount = USER_DATA[user_id]["balance"]
    else:
        try:
            bet_amount = int(bet)
        except ValueError:
            embed = discord.Embed(title="❌ Invalid Bet Amount", description="Please enter a valid whole number for your wager, or type `all`.", color=0xff0000)
            await ctx.send(embed=embed)
            return

    if bet_amount <= 0:
        embed = discord.Embed(title="❌ Invalid Bet Amount", description="Your bet must be greater than 0 chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    if USER_DATA[user_id]["balance"] < bet_amount:
        embed = discord.Embed(title="❌ Insufficient Funds", description=f"You do not have enough chips. Current Balance: **{USER_DATA[user_id]['balance']}** chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return
        
    space = space.lower().strip()
    valid_options = ["red", "black", "green", "even", "odd", "high", "low"]
    is_number = False
    target_number = -1
    try:
        target_number = int(space)
        if 0 <= target_number <= 36:
            is_number = True
        else:
            embed = discord.Embed(title="❌ Invalid Betting Number", description="If betting on a specific number, it must be between 0 and 36.", color=0xff0000)
            await ctx.send(embed=embed)
            return
    except ValueError:
        if space not in valid_options:
            embed = discord.Embed(title="❌ Invalid Betting Option", description="That is not a valid space on a roulette table.", color=0xff0000)
            embed.add_field(name="Valid Spaces", value="`red`, `black`, `green`, `even`, `odd`, `high`, `low`, or a number from `0-36`.", inline=False)
            await ctx.send(embed=embed)
            return
            
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    if user_id in RIGGED_ROULETTE:
        rig_val = RIGGED_ROULETTE.pop(user_id)
        if rig_val.isdigit():
            winning_num = int(rig_val)
        elif rig_val == "red": winning_num = random.choice(red_numbers)
        elif rig_val == "black": winning_num = random.choice([n for n in range(1, 37) if n not in red_numbers and n != 0])
        elif rig_val == "green": winning_num = 0
        else: winning_num = random.randint(0, 36)
    else:
        if "upgrades" not in USER_DATA[user_id]:
            USER_DATA[user_id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "slots_winboost": 0, "roulette_boost": 0, "xp_booster": 0}
        boost_lvl = USER_DATA[user_id]["upgrades"].get("roulette_boost", 0)
        if random.random() < (0.05 + (boost_lvl * 0.01)):
            winning_num = target_number if is_number else random.randint(0, 36)
        else:
            winning_num = random.randint(0, 36)
            
    USER_DATA[user_id]["total_games"] += 1
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await add_xp(user_id, 1)
    
    if winning_num == 0:
        winning_color = "green"
    elif winning_num in red_numbers:
        winning_color = "red"
    else:
        winning_color = "black"
    color_emoji = "🟢" if winning_color == "green" else "🔴" if winning_color == "red" else "⚫"
    
    won = False
    payout_multiplier = 0
    if is_number:
        if winning_num == target_number:
            won = True
            payout_multiplier = 35
    elif space == "red" and winning_color == "red":
        won = True
        payout_multiplier = 1
    elif space == "black" and winning_color == "black":
        won = True
        payout_multiplier = 1
    elif space == "green" and winning_color == "green":
        won = True
        payout_multiplier = 17
    elif space == "even" and winning_num != 0 and winning_num % 2 == 0:
        won = True
        payout_multiplier = 1
    elif space == "odd" and winning_num != 0 and winning_num % 2 != 0:
        won = True
        payout_multiplier = 1
    elif space == "high" and 19 <= winning_num <= 36:
        won = True
        payout_multiplier = 1
    elif space == "low" and 1 <= winning_num <= 18:
        won = True
        payout_multiplier = 1

    wheel_order = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
    winning_index = wheel_order.index(winning_num)
    slice_angle = 360 / 37
    target_rotation = (270 - (winning_index * slice_angle) - (slice_angle / 2)) % 360

    frames = []
    total_frames = 20
    high_velocity_spins = 2 * 360 

    for f in range(total_frames):
        t = f / (total_frames - 1)
        factor = 1 - (1 - t) ** 3  
        animated_angle = (high_velocity_spins + target_rotation) * factor

        img = Image.new("RGB", (300, 300), color=(20, 24, 30))
        draw = ImageDraw.Draw(img)
        draw.ellipse([10, 10, 290, 290], fill=(54, 33, 19), outline=(212, 175, 55), width=4)
        
        for i, num in enumerate(wheel_order):
            seg_start = animated_angle + (i * slice_angle)
            seg_end = seg_start + slice_angle
            color_theme = (34, 139, 34) if num == 0 else (178, 34, 34) if num in red_numbers else (20, 20, 20)
            draw.pieslice([25, 25, 275, 275], start=seg_start, end=seg_end, fill=color_theme, outline=(50, 50, 50), width=1)
            rad = math.radians(seg_start + (slice_angle / 2))
            text_x = 150 + int(105 * math.cos(rad))
            text_y = 150 + int(105 * math.sin(rad))
            draw.text((text_x, text_y), str(num), fill=(255, 255, 255), anchor="mm")

        draw.ellipse([110, 110, 190, 190], fill=(120, 120, 120), outline=(212, 175, 55), width=2)
        draw.polygon([(150, 35), (143, 10), (157, 10)], fill=(255, 215, 0))
        frames.append(img)

    final_buffer = io.BytesIO()
    frames[0].save(final_buffer, format="GIF", save_all=True, append_images=frames[1:], duration=100)
    final_buffer.seek(0)
    file = discord.File(fp=final_buffer, filename="roulette.gif")

    if won:
        net_gain = bet_amount * payout_multiplier
        USER_DATA[user_id]["balance"] += net_gain
        USER_DATA[user_id]["net_earnings"] += net_gain
        USER_DATA[user_id]["wins"] += 1
        result_color = 0x00ff00
        payout_text = f"{payout_multiplier}:1 payout" if payout_multiplier > 1 else "Even payout"
        outcome_statement = f"🎉 **WINNER WINNER!** 🎉\n\nYour bet on **{space.upper()}** hit!\nYou won **${net_gain:,}** ({payout_text})"
    else:
        USER_DATA[user_id]["balance"] -= bet_amount
        USER_DATA[user_id]["net_earnings"] -= bet_amount
        result_color = 0xff0000
        outcome_statement = f"😭 **House Wins!** 😭\n\nYour bet on **{space.upper()}** missed.\nYou lost **${bet_amount:,}**"
        
    await save_user_data()
        
    updated_embed = discord.Embed(title="🎡 Roulette Results 🎡", color=result_color)
    updated_embed.add_field(name="🎯 The Winning Pocket", value=f"{color_emoji} **{winning_num} {winning_color.upper()}**", inline=False)
    updated_embed.add_field(name="💰 Your Wager", value=f"Placed **{bet_amount:,}** chips on **{space.upper()}**", inline=False)
    updated_embed.add_field(name="📊 Result", value=outcome_statement, inline=False)
    updated_embed.add_field(name="💵 Updated Balance", value=f"**{USER_DATA[user_id]['balance']:,}** chips", inline=False)
    updated_embed.set_image(url="attachment://roulette.gif")
    await ctx.send(file=file, embed=updated_embed)
@bot.command()
async def keno(ctx, bet: str = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    await save_user_data()

    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    cooldown = 30
    if current_time - last_use < cooldown:
        remaining = int(cooldown - (current_time - last_use))
        await ctx.send(f"❌ Please wait {remaining}s before using this command again.")
        return

    if bet is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You must specify your bet amount.", color=0xff0000)
        embed.add_field(name="Correct Usage", value="`!keno <bet_amount>` or `!keno all`", inline=False)
        await ctx.send(embed=embed)
        return

    if bet.lower() == "all":
        bet_amount = USER_DATA[user_id]["balance"]
    else:
        try:
            bet_amount = int(bet)
        except ValueError:
            await ctx.send("Please enter a valid bet amount or `all`.")
            return

    if bet_amount > USER_DATA[user_id]["balance"]:
        await ctx.send("You do not have enough balance for this bet.")
        return

    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await save_user_data()

    class KenoModal(discord.ui.Modal, title='Enter your Keno numbers'):
        numbers_input = discord.ui.TextInput(
            label='Numbers (1-80)',
            style=discord.TextStyle.paragraph,
            placeholder='e.g. 1, 5, 12, 45, 77',
            required=True,
        )

        async def on_submit(self, interaction: discord.Interaction):
            try:
                numbers = [int(n.strip()) for n in self.numbers_input.value.split(',')]
            except ValueError:
                await interaction.response.send_message("Please enter numbers separated by commas.", ephemeral=True)
                return

            if not all(1 <= n <= 80 for n in numbers) or len(set(numbers)) != len(numbers) or not (1 <= len(numbers) <= 10):
                await interaction.response.send_message("❌ Please pick 1-10 unique numbers between 1 and 80.", ephemeral=True)
                return

            drawn_numbers = random.sample(range(1, 81), 20)
            matches = [n for n in numbers if n in drawn_numbers]
            match_count = len(matches)
            
            payout_table = {
                1: {1: 3},
                2: {2: 6},
                3: {3: 15},
                4: {4: 40},
                5: {5: 120},
                6: {6: 400},
                7: {7: 1500},
                8: {8: 5000},
                9: {9: 15000},
                10: {10: 50000}
            }
            
            multiplier = payout_table.get(len(numbers), {}).get(match_count, 0)
            winnings = bet_amount * multiplier

            USER_DATA[user_id]["balance"] -= bet_amount
            USER_DATA[user_id]["balance"] += winnings
            await save_user_data()

            result_embed = discord.Embed(title="Keno Results", color=0x00ff00)
            result_embed.add_field(name="Your Numbers", value=str(numbers), inline=False)
            result_embed.add_field(name="Drawn Numbers", value=str(drawn_numbers), inline=False)
            result_embed.add_field(name="Matches", value=f"{match_count} ({', '.join(map(str, matches))})", inline=False)
            result_embed.add_field(name="Winnings", value=f"{winnings}", inline=False)
            
            await interaction.response.send_message(embed=result_embed)

    class KenoView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.button(label="Click to enter numbers", style=discord.ButtonStyle.primary)
        async def enter_numbers(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                return await interaction.response.send_message("This is not your game.", ephemeral=True)
            await interaction.response.send_modal(KenoModal())

    await ctx.send(f"Bet set to {bet_amount}. Click the button below to pick your numbers.", view=KenoView())
class BetModal(discord.ui.Modal):
    def __init__(self, ctx):
        super().__init__(title="Adjust Stakes")
        self.ctx = ctx
        self.bet_input = discord.ui.TextInput(
            label="Enter New Bet Amount",
            placeholder="e.g. 500 or 'all'",
            required=True,
            max_length=15
        )
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        print(f"[DEBUG] [Modal] User submitted new bet string: '{self.bet_input.value}'")
        await interaction.response.defer(ephemeral=True)
        bot_command = bot.get_command("cups")
        await self.ctx.invoke(bot_command, bet=self.bet_input.value)


class PlayAgainView(discord.ui.View):
    def __init__(self, ctx, current_bet):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.bet = current_bet

    @discord.ui.button(label="Play Again (Same Bet)", style=discord.ButtonStyle.success)
    async def same_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"[DEBUG] [PlayAgain] User chose to replay with same bet: {self.bet}")
        await interaction.response.defer()
        bot_command = bot.get_command("cups")
        await self.ctx.invoke(bot_command, bet=str(self.bet))

    @discord.ui.button(label="Change Bet & Play", style=discord.ButtonStyle.secondary)
    async def change_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("[DEBUG] [PlayAgain] User requested to change stakes. Sending modal...")
        modal = BetModal(self.ctx)
        await interaction.response.send_modal(modal)


class RealCupsView(discord.ui.View):
    def __init__(self, ctx, bet_amount):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet = bet_amount
        self.round = 1
        self.score = 0
        self.ball_pos = 1  
        self.cups_pos = [0, 1, 2]  
        self.base_delay = [40, 25, 12]

    def render_scene(self, width, height, c_positions, lift_offset=0, show_ball=False, ball_x_override=None, arc_data=None):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = (35, 45, 60)  
        cv2.line(frame, (50, 320), (750, 320), (55, 65, 80), 3)

        if show_ball:
            b_x = ball_x_override if ball_x_override is not None else (200 + (c_positions[self.ball_pos] * 200))
            cv2.circle(frame, (b_x, 280), 14, (50, 50, 220), -1)
            cv2.circle(frame, (b_x, 280), 14, (100, 100, 255), 2)
            cv2.circle(frame, (b_x - 4, 280 - 4), 3, (255, 255, 255), -1)

        for idx, pos in enumerate(c_positions):
            x_center = 200 + (pos * 200)
            y_base = 300

            if arc_data and idx in arc_data:
                x_center, y_base = arc_data[idx]
            elif idx == self.ball_pos:
                y_base -= lift_offset

            pts = np.array([
                [x_center - 45, y_base - 100],
                [x_center + 45, y_base - 100],
                [x_center + 32, y_base],
                [x_center - 32, y_base]
            ], np.int32)

            cv2.fillPoly(frame, [pts], (40, 90, 160))
            cv2.polylines(frame, [pts], True, (70, 140, 220), 2)
            cv2.circle(frame, (x_center, y_base - 100), 45, (60, 110, 180), -1)
        return frame

    def generate_round_animation(self):
        width, height = 800, 400
        frames_list = []

        print(f"[DEBUG] [Engine] Initializing Frame Generation Loop for Round {self.round}")
        print(f"[DEBUG] [Engine] Current Mapping Layout State: Cups positional track={self.cups_pos} | Target Ball index={self.ball_pos}")

        # Step 1: Reveal - Lift cup to show ball (20 Frames)
        for f in range(20):
            lift = int(60 * math.sin((f / 20) * (math.pi / 2)))
            img = self.render_scene(width, height, self.cups_pos, lift_offset=lift, show_ball=True)
            frames_list.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Step 2: Staredown - Pause to let player inspect screen (30 Frames)
        for _ in range(30):
            img = self.render_scene(width, height, self.cups_pos, lift_offset=60, show_ball=True)
            frames_list.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Step 3: Close - Drop the shell cup back down (15 Frames)
        for f in range(15):
            lift = int(60 * math.cos((f / 15) * (math.pi / 2)))
            img = self.render_scene(width, height, self.cups_pos, lift_offset=lift, show_ball=True)
            frames_list.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Step 4: The Shuffle - Perform randomized arc shuffles
        swap_count = 4 if self.round == 1 else (6 if self.round == 2 else 9)
        print(f"[DEBUG] [Engine] Selected Shuffle Swap Steps Count for Round {self.round}: {swap_count} shuffles")
        
        for swap_idx in range(swap_count):
            idx1, idx2 = random.sample(range(3), 2)
            start_pos1, start_pos2 = self.cups_pos[idx1], self.cups_pos[idx2]
            
            steps = 12
            for s in range(steps):
                t = s / (steps - 1)
                curr_pos1 = start_pos1 + (start_pos2 - start_pos1) * t
                curr_pos2 = start_pos2 + (start_pos1 - start_pos2) * t
                
                x1 = int(200 + (curr_pos1 * 200))
                x2 = int(200 + (curr_pos2 * 200))
                
                arc_y = int(35 * math.sin(t * math.pi))
                y1 = 300 + arc_y
                y2 = 300 - arc_y

                arc_dictionary = {idx1: (x1, y1), idx2: (x2, y2)}
                img = self.render_scene(width, height, self.cups_pos, arc_data=arc_dictionary)
                frames_list.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
            
            self.cups_pos[idx1], self.cups_pos[idx2] = start_pos2, start_pos1
            print(f"[DEBUG] [Engine] Swap #{swap_idx+1} Complete. Pos state tracker: {self.cups_pos}")

        print(f"[DEBUG] [Engine] Total Frames Compiled: {len(frames_list)}. Saving bytes...")
        buffer = io.BytesIO()
        frames_list[0].save(
            buffer, format='GIF', save_all=True, 
            append_images=frames_list[1:], 
            duration=self.base_delay[self.round - 1],
            optimize=False
        )
        buffer.seek(0)
        return buffer

    async def start_shuffle_tier(self, msg_target):
        self.clear_items()
        
        estimated_time = 5 if self.round == 1 else (4 if self.round == 2 else 3)
        print(f"[DEBUG] [Bot] Estimated compilation overhead: {estimated_time}s")
        
        await msg_target.edit(
            content=f"⚙️ **Loading, Please wait {estimated_time}s** — Compiling physics timeline frames matrix in background core threads...",
            attachments=[], view=None
        )
        
        buffer = await asyncio.to_thread(self.generate_round_animation)
        file_payload = discord.File(fp=buffer, filename=f"round_{self.round}_shuffle.gif")
        
        print(f"[DEBUG] [Bot] Pushing Round {self.round} GIF...")
        await msg_target.edit(
            content=f"🔮 **Round {self.round}/3** — Shuffling! Watch the cups closely...",
            attachments=[file_payload], view=None
        )

        await asyncio.sleep(float(estimated_time))
        
        self.add_item(discord.ui.Button(label="Cup 1", style=discord.ButtonStyle.primary, custom_id="0"))
        self.add_item(discord.ui.Button(label="Cup 2", style=discord.ButtonStyle.primary, custom_id="1"))
        self.add_item(discord.ui.Button(label="Cup 3", style=discord.ButtonStyle.primary, custom_id="2"))
        
        for item in self.children:
            item.callback = self.process_guess
            
        print(f"[DEBUG] [Bot] Spawning selection buttons wrapper. Ball location index: Cup #{self.cups_pos[self.ball_pos] + 1}")
        await msg_target.edit(content=f"🔴 **Round {self.round}/3** — Where is the ball? Make your choice!", view=self)

    async def process_guess(self, interaction: discord.Interaction):
        await interaction.response.defer()
        choice = int(interaction.data["custom_id"])
        
        chosen_cup_actual_pos = self.cups_pos[choice]
        ball_cup_actual_pos = self.cups_pos[self.ball_pos]
        
        print(f"[DEBUG] [User Action] User picked Button Index [{choice}] (Screen Column position: {chosen_cup_actual_pos})")

        if chosen_cup_actual_pos == ball_cup_actual_pos:
            self.score += 1
            feedback = "✨ **CORRECT!** You tracked it perfectly."
            print(f"[DEBUG] [User Action] Result: SUCCESS. Current tally score: {self.score}/3")
        else:
            feedback = "❌ **WRONG!** The cup was empty."
            print(f"[DEBUG] [User Action] Result: FAILURE. Current tally score: {self.score}/3")

        width, height = 800, 400
        reveal_frames = []
        for f in range(15):
            lift = int(60 * math.sin((f / 15) * (math.pi / 2)))
            img = self.render_scene(width, height, self.cups_pos, lift_offset=lift, show_ball=True)
            reveal_frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        rev_buffer = io.BytesIO()
        reveal_frames[0].save(
            rev_buffer, format='GIF', save_all=True, 
            append_images=reveal_frames[1:], 
            duration=30,
            optimize=False
        )
        rev_buffer.seek(0)

        await interaction.message.edit(
            content=f"{feedback} Revealing ball...",
            attachments=[discord.File(fp=rev_buffer, filename="reveal.gif")], view=None
        )
        await asyncio.sleep(2.5)

        self.round += 1
        if self.round <= 3:
            print(f"[DEBUG] [Bot] Advancing game state timeline forward to Round {self.round}")
            self.cups_pos = [0, 1, 2]
            self.ball_pos = 1
        if self.round <= 3:
            print(f"[DEBUG] [Bot] Advancing game state timeline forward to Round {self.round}")
            self.cups_pos = [0, 1, 2]
            self.ball_pos = 1
            await self.start_shuffle_tier(interaction.message)
        else:
            print("[DEBUG] [Bot] All rounds exhausted. Advancing context to settlement tiers...")
            await self.conclude_game_session(interaction.message)

    async def conclude_game_session(self, final_msg_hook):
        user_id = self.ctx.author.id
        multiplier = {3: 3, 2: 1.5, 1: -1, 0: -2}.get(self.score, 0)
        payout = int(self.bet * multiplier)
        
        print(f"[DEBUG] [Accounting] Final Tally: {self.score}/3. Base Stake: ${self.bet:,} | Shift Payout: ${payout:,}")
        
        USER_DATA[user_id]["balance"] += payout
        await save_user_data()

        width, height = 800, 400
        end_img = self.render_scene(width, height, self.cups_pos, lift_offset=60, show_ball=True)
        res_buffer = io.BytesIO()
        Image.fromarray(cv2.cvtColor(end_img, cv2.COLOR_BGR2RGB)).save(res_buffer, format="PNG")
        res_buffer.seek(0)

        outcome_text = "🎉 **PROFIT!**" if payout > 0 else "📉 **HOUSE WINS!**"
        await final_msg_hook.edit(
            content=f"🏆 **Game Over!** You got **{self.score}/3** correct.\n{outcome_text} Payout: **${payout:,}**",
            attachments=[discord.File(fp=res_buffer, filename="final_results.png")],
            view=PlayAgainView(self.ctx, self.bet)
        )

@bot.command()
async def cups(ctx, bet: str):
    user_id = ctx.author.id
    print(f"\n[DEBUG] [Command Trigger] !cups invoked by User {ctx.author} (ID: {user_id}) with stake value: '{bet}'")
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 4:
        print("[DEBUG] [Command Trigger] Aborted invocation: Cooldown timeframe active.")
        return await ctx.send(f"❌ Cool down active. Please wait a moment.")
    
    bet_amount = USER_DATA[user_id]["balance"] if bet.lower() == "all" else int(bet)
    if bet_amount <= 0 or bet_amount > USER_DATA[user_id]["balance"]:
        print(f"[DEBUG] [Command Trigger] Aborted invocation: Invalid funding thresholds.")
        return await ctx.send("❌ Invalid stake or insufficient funds.")
        
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await save_user_data()
    
    initial_pending_msg = await ctx.send("🃏 **Initializing high-stakes card room simulation tables...**")
    
    game_instance = RealCupsView(ctx, bet_amount)
    await game_instance.start_shuffle_tier(initial_pending_msg)



    async def conclude_game_session(self, final_msg_hook):
        user_id = self.ctx.author.id
        multiplier = {3: 3, 2: 1.5, 1: -1, 0: -2}.get(self.score, 0)
        payout = int(self.bet * multiplier)
        
        print(f"[DEBUG] [Accounting] Final Tally: {self.score}/3 correct. Multiplier Selected: {multiplier}x")
        print(f"[DEBUG] [Accounting] Base Stake: ${self.bet:,} | Total Calculated Shift Payout: ${payout:,}")
        
        USER_DATA[user_id]["balance"] += payout
        await save_user_data()
        print(f"[DEBUG] [Accounting] Database updated successfully. Balance committed to system state record fields.")

        width, height = 800, 400
        end_img = self.render_scene(width, height, self.cups_pos, lift_offset=60, show_ball=True)
        res_buffer = io.BytesIO()
        Image.fromarray(cv2.cvtColor(end_img, cv2.COLOR_BGR2RGB)).save(res_buffer, format="PNG")
        res_buffer.seek(0)

        outcome_text = "🎉 **PROFIT!**" if payout > 0 else "📉 **HOUSE WINS!**"
        await final_msg_hook.edit(
            content=f"🏆 **Game Over!** You got **{self.score}/3** correct.\n{outcome_text} Payout: **${payout:,}**",
            attachments=[discord.File(fp=res_buffer, filename="final_results.png")],
            view=PlayAgainView(self.ctx, self.bet)
        )





def get_safe_username(username):
    return "".join(c if ord(c) < 128 else "?" for c in username)

def generate_profile_image(target_id, username, stats, rank, avatar_img, badges, achievements, calc_level):
    width, height = 2400, 1300
    img = Image.new("RGB", (width, height), "#0b0f19")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(40, 40), (2360, 1260)], outline="#3b82f6", width=16)
    
    avatar_img_resized = avatar_img.resize((400, 400))
    img.paste(avatar_img_resized, (140, 140), avatar_img_resized)
    
    draw.rectangle([(136, 136), (544, 544)], outline="#ffffff", width=8)
    
    str_uid = str(target_id)
    custom_tag = ""
    highlight_color = "#ffffff"

    if str_uid == "978024161689608202":
        custom_tag = " [OWNER]"
        highlight_color = "#ef4444"
    elif str_uid == "962451361058930780":
        custom_tag = " [CO-OWNER]"
        highlight_color = "#3b82f6"
    elif str_uid in ["870849419065577503", "899343022565757059"]:
        custom_tag = " [DEV]"
        highlight_color = "#22c55e"
    elif str_uid == "1161762623382110208":
        custom_tag = " [POTATO]"
        highlight_color = "#eab308"
    elif str_uid == "941049240585662495":
        custom_tag = " [GOD]"
        highlight_color = "#eab308"
    elif str_uid == "921465683492106290":
        custom_tag = f" [ULTRA] [LVL {calc_level}]"
        highlight_color = "#a855f7"
    elif str_uid == "1229921852332441731":
        custom_tag = " [GRACIAS]"
        highlight_color = "#a855f7"
    elif stats.get("vip_status", False) or stats.get("upgrades", {}).get("vip_lounge", 0) > 0:
        custom_tag = " [VIP]"
        highlight_color = "#f97316"

    safe_name = get_safe_username(username)
    draw.text((620, 160), f"PLAYER PROFILE: {safe_name.upper()}{custom_tag}", fill=highlight_color, font=font_large)
    
    rank_color = "#94a3b8"
    if rank == "Intermediate":
        rank_color = "#3b82f6"
    elif rank == "Advanced":
        rank_color = "#eab308"
    draw.text((620, 280), f"PLAYER RANK: {rank.upper()}", fill=rank_color, font=font_large)
    
    current_xp = stats.get("xp", 0)
    current_level = calc_level
    next_level = current_level + 1
    current_lvl_base_xp = 4 * ((current_level - 1) ** 2) if current_level > 1 else 0
    next_lvl_req_xp = 4 * ((next_level - 1) ** 2)
    xp_in_level = current_xp - current_lvl_base_xp
    xp_needed_for_level = next_lvl_req_xp - current_lvl_base_xp
    progress_str = f"Level {current_level} ({current_xp} Total XP) — {xp_in_level}/{xp_needed_for_level} XP to Level {next_level}"
        
    draw.text((620, 400), f"EXPERIENCE PROGRESS: {progress_str}", fill="#a855f7", font=font_medium)

    def draw_badge_shape(draw, shape_name, cx, cy):
        if shape_name == "owner":
            draw.rectangle([cx-20, cy+10, cx+20, cy+18], fill=(220, 20, 60))
            draw.polygon([(cx-20, cy+10), (cx-20, cy-15), (cx-10, cy), (cx, cy-22), (cx+10, cy), (cx+20, cy-15), (cx+20, cy+10)], fill=(212, 175, 55))
        elif shape_name == "staff":
            draw.polygon([(cx-20, cy-20), (cx+20, cy-20), (cx+20, cy), (cx, cy+25), (cx-20, cy)], fill=(65, 105, 225), outline=(255,255,255), width=2)
        elif shape_name == "vip":
            draw.polygon([(cx, cy-25), (cx+22, cy), (cx, cy+25), (cx-22, cy)], fill=(0, 238, 238), outline=(255, 255, 255), width=2)
        elif shape_name == "verified":
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = 25 if i % 2 == 0 else 10
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            draw.polygon(points, fill=(255, 215, 0))
        elif shape_name == "jackpot":
            draw.rectangle([cx-15, cy-10, cx+15, cy+15], fill=(212, 175, 55))
            draw.ellipse([cx-25, cy-25, cx+25, cy-5], fill=(212, 175, 55))

    draw.text((620, 470), "BADGES & ACHIEVEMENTS", fill="#94a3b8", font=font_medium)
    for i, badge in enumerate(badges):
        draw_badge_shape(draw, badge.lower(), 660 + (i * 80), 550)

    draw.line([(140, 600), (2260, 600)], fill="#1e293b", width=10)
    draw.text((140, 680), "CASH RESERVES", fill="#94a3b8", font=font_medium)
    draw.text((140, 780), f"${format_number(stats['balance'])}", fill="#22c55e", font=font_large)
    draw.text((1200, 680), "TOTAL PROFIT / LOSS", fill="#94a3b8", font=font_medium)
    
    earnings_color = "#22c55e" if stats['net_earnings'] >= 0 else "#ef4444"
    sign = "+" if stats['net_earnings'] >= 0 else ""
    draw.text((1200, 780), f"{sign}${format_number(abs(stats['net_earnings']))}", fill=earnings_color, font=font_large)
    
    draw.text((140, 960), "TOTAL GAMES PLAYED", fill="#94a3b8", font=font_medium)
    draw.text((140, 1060), f"{stats['total_games']} MATCHES", fill="#ffffff", font=font_large)
    draw.text((1200, 960), "GAME WIN RATE", fill="#94a3b8", font=font_medium)
    
    win_rate = (stats['wins'] / stats['total_games'] * 100) if stats['total_games'] > 0 else 0.0
    draw.text((1200, 1060), f"{win_rate:.2f}% WIN RATE", fill="#eab308", font=font_large)

    img = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="profile.png")


@bot.command()
async def profile(ctx, user: discord.Member = None):
    target = user or ctx.author
    await ensure_user(target.id)
    
    mutated = False
    if "upgrades" not in USER_DATA[target.id]:
        USER_DATA[target.id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "xp_booster": 0, "vip_lounge": 0, "loan_bribe": 0, "bank_boost": 0}
        mutated = True
    if "loan_debt" not in USER_DATA[target.id]:
        USER_DATA[target.id]["loan_debt"] = 0
        mutated = True
    if "vault" not in USER_DATA[target.id]:
        USER_DATA[target.id]["vault"] = 0
        mutated = True
    if "badges" not in USER_DATA[target.id]:
        USER_DATA[target.id]["badges"] = []
        mutated = True
    if "achievements" not in USER_DATA[target.id]:
        USER_DATA[target.id]["achievements"] = []
        mutated = True
    if "xp" not in USER_DATA[target.id]:
        USER_DATA[target.id]["xp"] = 0
        mutated = True
    if "streak" not in USER_DATA[target.id]:
        USER_DATA[target.id]["streak"] = 0
        mutated = True
    if "rep" not in USER_DATA[target.id]:
        USER_DATA[target.id]["rep"] = 0
        mutated = True
    
    if mutated:
        await save_user_data()

    if ctx.guild and ctx.guild.id == 1520275208592687275:
        role_to_xp_map = {
            1520602478410731712: 40000,
            1520602473801191574: 22500,
            1520602455698837615: 10000,
            1520602484379353118: 25000,
            1520277331472814120: 16000,
            1520277657458053261: 900,
            1520277335092236388: 400,
            1520277338439549240: 100,
            1520277650243846288: 0
        }
        for role_id, implied_xp in role_to_xp_map.items():
            if any(r.id == role_id for r in target.roles):
                if USER_DATA[target.id]["xp"] < implied_xp:
                    USER_DATA[target.id]["xp"] = implied_xp
                    await save_user_data()
                break

    upgrades = USER_DATA[target.id]["upgrades"]
    plinko_lvl = upgrades.get("plinko_boost", 0)
    slots_lvl = upgrades.get("slots_boost", 0)
    xp_lvl = upgrades.get("xp_booster", 0)
    vip_lvl = upgrades.get("vip_lounge", 0)
    bribe_lvl = upgrades.get("loan_bribe", 0)
    bank_lvl = upgrades.get("bank_boost", 0)
    debt = USER_DATA[target.id].get("loan_debt", 0)
    bal = USER_DATA[target.id]["balance"]
    vault = USER_DATA[target.id]["vault"]
    badges = USER_DATA[target.id].get("badges", [])
    achievements = USER_DATA[target.id].get("achievements", [])
    current_xp = USER_DATA[target.id].get("xp", 0)
    streak = USER_DATA[target.id].get("streak", 0)
    rep = USER_DATA[target.id].get("rep", 0)
    
    calc_level = int((current_xp / 4) ** 0.5) if current_xp > 0 else 1
    if calc_level < 1:
        calc_level = 1
        
    is_vip = vip_lvl > 0 or USER_DATA[target.id].get("vip_status", False)
    vip_badge = "💎 **VIP Platinum Member**" if is_vip else "🎟️ **Standard Guest Tier**"

    if USER_DATA[target.id].get("trespassed", False):
        embed = discord.Embed(title="❌ Access Denied", description=f"{target.mention} is currently **Trespassed** from the facility floors.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    avatar = await fetch_avatar_image(target)
    
    rank_label = "Novice"
    if calc_level >= 20:
        rank_label = "Advanced"
    elif calc_level >= 5:
        rank_label = "Intermediate"
        
    file = generate_profile_image(target.id, target.display_name, USER_DATA[target.id], rank_label, avatar, badges, achievements, calc_level)
    
    max_vault_capacity = 50000 + (bank_lvl * 10000)
    vault_ratio = min(1.0, max(0.0, vault / max_vault_capacity)) if max_vault_capacity > 0 else 0.0
    bar_blocks = int(vault_ratio * 12)
    progress_bar_str = "🟩" * bar_blocks + "⬛" * (12 - bar_blocks)
    vault_percentage_str = f"{vault_ratio * 100:.1f}%"
    
    sorted_leaderboard = sorted(USER_DATA.items(), key=lambda x: x[1].get("balance", 0), reverse=True)
    leaderboard_position = "Unranked"
    for rank_idx, (uid, _) in enumerate(sorted_leaderboard, 1):
        if uid == target.id:
            leaderboard_position = f"#{rank_idx:,} of {len(USER_DATA):,}"
            break

    embed_color = 0xd4af37 if is_vip else 0x1e1f22
    embed = discord.Embed(color=embed_color)
    
    avatar_url_fallback = target.avatar.url if target.avatar else target.default_avatar.url
    embed.set_author(name=f"{target.display_name} — Account Dashboard", icon_url=avatar_url_fallback)
    
    overview_field = (
        f"• **Standing:** {vip_badge}\n"
        f"• **Account Level:** Level **{calc_level}**\n"
        f"• **Total Progression Score:** `{current_xp:,}` XP"
    )
    embed.add_field(name="✨ Account Overview", value=overview_field, inline=False)
    
    metrics_field = (
        f"🔥 **Daily Streak:** `{streak:,}` days\n"
        f"👍 **Reputation Score:** `{rep:+,}` REP\n"
        f"🏆 **Leaderboard Rank:** `{leaderboard_position}`"
    )
    embed.add_field(name="📊 Social Matrix & Engagement", value=metrics_field, inline=False)
    
    financials_field = (
        f"💵 Wallet Chips: **{bal:,}**\n"
        f"🏛️ Vault Storage: **{vault:,}** / **{max_vault_capacity:,}**\n"
        f"📊 `{progress_bar_str}` (**{vault_percentage_str}** Full)"
    )
    embed.add_field(name="💰 Liquid & Stored Assets", value=financials_field, inline=False)
    
    debt_text = f"🚨 **{debt:,}** chips outstanding" if debt > 0 else "✅ Clear (No Debts)"
    security_field = (
        f"• **Loan Liabilities:** {debt_text}\n"
        f"• **Security Bribes Logs:** Level **{bribe_lvl}** purchased"
    )
    embed.add_field(name="🛡️ Security & Risks Balance", value=security_field, inline=False)
    
    upgrades_display = (
        f"🎲 **Plinko Booster:** Lvl `{plinko_lvl}/10`\n"
        f"🎰 **Slots Multiplier:** Lvl `{slots_lvl}/150`\n"
        f"⚡ **XP Overdrive Module:** Lvl `{xp_lvl}/4`\n"
        f"📈 **Vault Infrastructure:** Lvl `{bank_lvl}/100`"
    )
    embed.add_field(name="🛍️ Core Upgrades Matrix", value=upgrades_display, inline=True)
    
    badge_names = [BADGE_ITEMS[b]["name"] if b in BADGE_ITEMS else b for b in badges]
    badge_text = " ".join(badge_names) if badges else "*No Badges Unlocked Yet.*"
    
    achievement_text = "\n".join([f"• {ach}" for ach in achievements]) if achievements else "*No Achievements Unlocked Yet.*"
    
    embed.add_field(name="🎖️ Achievements & Badges", value=f"**Badges:** {badge_text}\n\n**Achievements:**\n{achievement_text}", inline=False)
    
    embed.set_image(url="attachment://profile.png")
    embed.set_footer(text="Casino Operating System • Use !cmds to explore parameters")
    await ctx.send(file=file, embed=embed)

@bot.command()
async def balance(ctx, user: discord.Member = None):
    target = user or ctx.author
    await ensure_user(target.id)
    await save_user_data()
    
    if "vault" not in USER_DATA[target.id]:
        USER_DATA[target.id]["vault"] = 0
    
    if USER_DATA[target.id].get("trespassed", False):
        embed = discord.Embed(title="❌ Trespassed", description=f"{target.mention} is currently **Trespassed** from the casino.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    bal = USER_DATA[target.id]["balance"]
    vault = USER_DATA[target.id]["vault"]
    file = generate_balance_image(target.display_name, bal)
    
    embed = discord.Embed(title="🏦 BANK LEDGER ACCOUNT VIEW", description=f"**Official financial records for {target.mention}:**", color=0xd4af37)
    embed.add_field(name="💼 Wallet Balance", value=f"**`{format_number(bal)} chips`**", inline=True)
    embed.add_field(name="🔒 Vault Balance", value=f"**`{format_number(vault)} chips`**", inline=True)
    embed.add_field(name="💰 Total Net Worth", value=f"**`{format_number(bal + vault)} chips`**", inline=False)
    embed.set_image(url="attachment://balance.png")
    await ctx.send(file=file, embed=embed)

class InventoryPaginator(discord.ui.View):
    def __init__(self, pages, member):
        super().__init__(timeout=60)
        self.pages = pages
        self.member = member
        self.current_page = 0

    def create_embed(self):
        embed = discord.Embed(
            title=f"🎒 {self.member.display_name}'s Inventory",
            description=self.pages[self.current_page],
            color=0x3b82f6
        )
        embed.set_author(name=self.member.name, icon_url=self.member.display_avatar.url)
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} • Total unique items: {len(self.pages)}")
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("You cannot control this inventory menu.", ephemeral=True)
            return
            
        if self.current_page > 0:
            self.current_page -= 1
            
        self.next_button.disabled = False
        if self.current_page == 0:
            button.disabled = True
            
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("You cannot control this inventory menu.", ephemeral=True)
            return
            
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            
        self.previous_button.disabled = False
        if self.current_page == len(self.pages) - 1:
            button.disabled = True
            
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

@bot.command()
async def inv(ctx, member: discord.Member = None):
    target_member = member or ctx.author
    user_id = target_member.id
    
    await ensure_user(user_id)
    
    # Check inventory privacy settings if viewing someone else's inventory
    if ctx.author.id != user_id:
        privacy_setting = USER_DATA[user_id].get("private_inventory", "everyone")
        
        if privacy_setting == "no one":
            await ctx.send(f"❌ **{target_member.display_name}** has set their inventory privacy to private.")
            return
            
        elif privacy_setting == "friends only":
            author_friends = USER_DATA[ctx.author.id].get("friends", [])
            target_friends = USER_DATA[user_id].get("friends", [])
            
            if ctx.author.id not in target_friends and user_id not in author_friends:
                await ctx.send(f"❌ You must be friends with **{target_member.display_name}** to view their inventory.")
                return

    user_inventory = USER_DATA[user_id].get("inventory", {})
    
    # Filter out items that the user owns but has 0 quantity of
    active_items = {item_id: qty for item_id, qty in user_inventory.items() if qty > 0}
    
    if not active_items:
        embed = discord.Embed(
            title=f"🎒 {target_member.display_name}'s Inventory",
            description="*This inventory is currently empty.*",
            color=0x3b82f6
        )
        embed.set_author(name=target_member.name, icon_url=target_member.display_avatar.url)
        embed.set_footer(text="Use shop commands to acquire items!")
        await ctx.send(embed=embed)
        return

    # Advanced metrics for features extension
    total_item_count = sum(active_items.values())
    net_worth = 0
    
    pages = []
    for item_id, quantity in active_items.items():
        item_info = ITEMS_DATABASE.get(item_id, {
            "name": f"Unknown Item ({item_id})",
            "description": "No description available.",
            "rarity": "Common",
            "usable": False,
            "cost": 0
        })
        
        item_cost = item_info.get("cost", 0)
        total_item_value = item_cost * quantity
        net_worth += total_item_value
        
        rarity_colors = {
            "Common": "⚪ Common",
            "Uncommon": "🟢 Uncommon",
            "Rare": "🔵 Rare",
            "Epic": "🟣 Epic",
            "Legendary": "🟡 Legendary",
            "Unique": "🟠 Unique",
            "Mythic": "🔴 Mythical"
        }
        rarity_display = rarity_colors.get(item_info["rarity"], "⚪ Common")
        usable_display = "✅ Consumable/Usable" if item_info["usable"] else "Passive / Auto-use"
        
        cost_display = f"{item_cost:,} coins" if item_cost > 0 else "Unpriced / Special"
        total_value_display = f"{total_item_value:,} coins" if total_item_value > 0 else "0 coins"
        
        page_text = (
            f"**Item:** {item_info['name']}\n"
            f"**Quantity Owned:** `{quantity}`\n"
            f"**Rarity:** {rarity_display}\n"
            f"**Type:** {usable_display}\n"
            f"**ID Key:** `{item_id}`\n"
            f"**Value (Per Unit):** `{cost_display}`\n"
            f"**Total Value:** `{total_value_display}`\n\n"
            f"**Description:**\n*{item_info['description']}*\n\n"
            f"📈 *Inventory Stats: Total Items: {total_item_count} | Estimated Net Worth: {net_worth:,} coins*"
        )
        pages.append(page_text)

    if len(pages) == 1:
        embed = discord.Embed(
            title=f"🎒 {target_member.display_name}'s Inventory",
            description=pages[0],
            color=0x3b82f6
        )
        embed.set_author(name=target_member.name, icon_url=target_member.display_avatar.url)
        embed.set_footer(text=f"Page 1/1 • Total unique items: 1")
        await ctx.send(embed=embed)
    else:
        view = InventoryPaginator(pages, target_member)
        embed = view.create_embed()
        await ctx.send(embed=embed, view=view)

class AuctionHousePaginator(discord.ui.View):
    def __init__(self, listings, ctx_author, current_filter="all"):
        super().__init__(timeout=60)
        self.listings = listings
        self.ctx_author = ctx_author
        self.current_filter = current_filter
        self.current_page = 0
        self.items_per_page = 5
        self.pages = self.chunk_listings()
        self.update_button_states()

    def chunk_listings(self):
        filtered = []
        now = time.time()
        for aid, data in AUCTION_HOUSE.items():
            if data["expires_at"] <= now:
                continue
            if self.current_filter == "buy_now" and data["type"] != "buy_now":
                continue
            if self.current_filter == "bid" and data["type"] != "bid":
                continue
            filtered.append((aid, data))
            
        return [filtered[i:i + self.items_per_page] for i in range(0, len(filtered), self.items_per_page)]

    def update_button_states(self):
        total_pages = len(self.pages)
        self.prev_btn.disabled = self.current_page <= 0
        self.next_btn.disabled = self.current_page >= total_pages - 1 or total_pages == 0

    def generate_embed(self):
        embed = discord.Embed(
            title="🏛️ Global Economy Auction House",
            description="Welcome to the marketplace! Use the buttons or options below to navigate active listings.",
            color=0xf59e0b
        )
        embed.add_field(name="⚙️ Active Filter", value=f"`{self.current_filter.upper()}`", inline=True)
        embed.add_field(name="📦 Total Listings", value=f"`{len(AUCTION_HOUSE)}` items listed", inline=True)
        
        if not self.pages or len(self.pages[self.current_page]) == 0:
            embed.add_field(name="Empty Market", value="*There are no current active listings matching this criteria.*", inline=False)
            return embed

        for aid, data in self.pages[self.current_page]:
            item_info = ITEMS_DATABASE.get(data["item_id"], {
                "name": f"Unknown ({data['item_id']})", "rarity": "Common", "description": "N/A"
            })
            time_left = max(0, int(data["expires_at"] - time.time()))
            minutes, seconds = divmod(time_left, 60)
            hours, minutes = divmod(minutes, 60)
            time_str = f"{hours}h {minutes}m {seconds}s" if time_left > 0 else "Expired"
            
            seller = f"<@{data['seller_id']}>"
            if data["type"] == "buy_now":
                pricing_block = f"💰 **Buy It Now Price:** `{data['price']:,}` coins"
            else:
                top_bidder = f"<@{data['highest_bidder']}>" if data["highest_bidder"] else "*None*"
                pricing_block = (
                    f"📢 **Auction Format: Bidding**\n"
                    f"💵 **Starting Price:** `{data['price']:,}` coins\n"
                    f"🔺 **Current High Bid:** `{data['highest_bid']:,}` coins\n"
                    f"👤 **Top Bidder:** {top_bidder}"
                )

            embed.add_field(
                name=f"🆔 `{aid}` | {item_info['name']} (x{data['quantity']})",
                value=(
                    f"✨ **Rarity:** `{item_info['rarity']}`\n"
                    f"👤 **Seller:** {seller}\n"
                    f"{pricing_block}\n"
                    f"⏳ **Time Remaining:** `{time_str}`\n"
                    f"↳ *To buy/bid: Use `!ah buy {aid}` or `!ah bid {aid} <amount>`*"
                ),
                inline=False
            )
            
        embed.set_footer(text=f"Page {self.current_page + 1}/{max(1, len(self.pages))} • Navigation windows expire in 60s.")
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, custom_id="ah_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx_author.id:
            await interaction.response.send_message("This menu is controlled by someone else.", ephemeral=True)
            return
        if self.current_page > 0:
            self.current_page -= 1
            self.update_button_states()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Filter: All", style=discord.ButtonStyle.success, custom_id="ah_filter_all")
    async def filter_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx_author.id:
            await interaction.response.send_message("This menu is controlled by someone else.", ephemeral=True)
            return
        self.current_filter = "all"
        self.current_page = 0
        self.pages = self.chunk_listings()
        self.update_button_states()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Filter: Buy Now", style=discord.ButtonStyle.primary, custom_id="ah_filter_buy")
    async def filter_buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx_author.id:
            await interaction.response.send_message("This menu is controlled by someone else.", ephemeral=True)
            return
        self.current_filter = "buy_now"
        self.current_page = 0
        self.pages = self.chunk_listings()
        self.update_button_states()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Filter: Bids", style=discord.ButtonStyle.primary, custom_id="ah_filter_bid")
    async def filter_bid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx_author.id:
            await interaction.response.send_message("This menu is controlled by someone else.", ephemeral=True)
            return
        self.current_filter = "bid"
        self.current_page = 0
        self.pages = self.chunk_listings()
        self.update_button_states()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="ah_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx_author.id:
            await interaction.response.send_message("This menu is controlled by someone else.", ephemeral=True)
            return
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_button_states()
            await interaction.response.edit_message(embed=self.generate_embed(), view=self)

@bot.event
async def on_ready():
    while True:
        now = time.time()
        expired_ids = [aid for aid, data in AUCTION_HOUSE.items() if data["expires_at"] <= now]
        
        for aid in expired_ids:
            data = AUCTION_HOUSE.pop(aid, None)
            if not data:
                continue
                
            seller_id = data["seller_id"]
            item_id = data["item_id"]
            qty = data["quantity"]
            
            await ensure_user(seller_id)
            
            if data["type"] == "bid" and data["highest_bidder"] is not None:
                buyer_id = data["highest_bidder"]
                payout = data["highest_bid"]
                
                await ensure_user(buyer_id)
                
                USER_DATA[seller_id]["balance"] += payout
                buyer_inv = USER_DATA[buyer_id].setdefault("inventory", {})
                buyer_inv[item_id] = buyer_inv.get(item_id, 0) + qty
                
                USER_DATA[seller_id].setdefault("history_actions", []).append(f"Auction {aid} sold item {item_id} x{qty} for {payout} coins.")
                USER_DATA[buyer_id].setdefault("history_actions", []).append(f"Won auction {aid} for item {item_id} x{qty} spending {payout} coins.")
            else:
                seller_inv = USER_DATA[seller_id].setdefault("inventory", {})
                seller_inv[item_id] = seller_inv.get(item_id, 0) + qty
                USER_DATA[seller_id].setdefault("history_actions", []).append(f"Auction {aid} expired unsold. {item_id} x{qty} returned.")
                
        await save_user_data()
        await asyncio.sleep(15)

@bot.group(invoke_without_command=True)
async def ah(ctx):
    if ctx.author.id in AUCTION_BLACKLIST:
        await ctx.send("❌ You are blacklisted from using the Auction House system.")
        return
        
    await ensure_user(ctx.author.id)
    view = AuctionHousePaginator(AUCTION_HOUSE, ctx.author, "all")
    await ctx.send(embed=view.generate_embed(), view=view)

@ah.command(name="sell")
async def ah_sell(ctx, item_id: str, quantity: int, mode: str, price: int):
    if ctx.author.id in AUCTION_BLACKLIST:
        await ctx.send("❌ You are blacklisted from using the Auction House system.")
        return
        
    await ensure_user(ctx.author.id)
    
    if quantity <= 0:
        await ctx.send("❌ Quantity must be a positive number greater than 0.")
        return
        
    if price < 0:
        await ctx.send("❌ Price cannot be negative.")
        return
        
    mode = mode.lower()
    if mode not in ["buy_now", "bid"]:
        await ctx.send("❌ Invalid mode. Choose either `buy_now` or `bid`.")
        return
        
    user_inv = USER_DATA[ctx.author.id].get("inventory", {})
    if item_id not in user_inv or user_inv[item_id] < quantity:
        await ctx.send("❌ You do not have enough of that item in your inventory to sell.")
        return
        
    if item_id not in ITEMS_DATABASE:
        await ctx.send("❌ That item ID does not exist in the catalog systems.")
        return

    item_info = ITEMS_DATABASE[item_id]
    
    user_inv[item_id] -= quantity
    if user_inv[item_id] == 0:
        del user_inv[item_id]
        
    listing_id = str(uuid.uuid4().hex[:6].upper())
    while listing_id in AUCTION_HOUSE:
        listing_id = str(uuid.uuid4().hex[:6].upper())
        
    expiry_duration = 7200 
    
    AUCTION_HOUSE[listing_id] = {
        "seller_id": ctx.author.id,
        "item_id": item_id,
        "quantity": quantity,
        "type": mode,
        "price": price,
        "highest_bid": price if mode == "bid" else 0,
        "highest_bidder": None,
        "expires_at": time.time() + expiry_duration
    }
    
    await save_user_data()
    
    embed = discord.Embed(title="📝 Listing Created Successfully", color=0x10b981)
    embed.add_field(name="Item Details", value=f"{item_info['name']} x{quantity}", inline=True)
    embed.add_field(name="Listing ID", value=f"`{listing_id}`", inline=True)
    embed.add_field(name="Sale System Format", value=f"`{mode.upper()}`", inline=True)
    embed.add_field(name="Base/Buy Price", value=f"`{price:,}` coins", inline=True)
    await ctx.send(embed=embed)

@ah.command(name="buy")
async def ah_buy(ctx, listing_id: str):
    if ctx.author.id in AUCTION_BLACKLIST:
        await ctx.send("❌ You are blacklisted from using the Auction House system.")
        return
        
    listing_id = listing_id.upper()
    if listing_id not in AUCTION_HOUSE:
        await ctx.send("❌ Listing ID not found or already closed.")
        return
        
    data = AUCTION_HOUSE[listing_id]
    if data["type"] != "buy_now":
        await ctx.send("❌ This listing is configured for bidding. Use `!ah bid <id> <amount>` instead.")
        return
        
    if data["seller_id"] == ctx.author.id:
        await ctx.send("❌ You cannot purchase your own auction item.")
        return
        
    await ensure_user(ctx.author.id)
    await ensure_user(data["seller_id"])
    
    cost = data["price"]
    if USER_DATA[ctx.author.id]["balance"] < cost:
        await ctx.send(f"❌ You do not have enough coins. Required: `{cost:,}` coins.")
        return
        
    AUCTION_HOUSE.pop(listing_id)
    USER_DATA[ctx.author.id]["balance"] -= cost
    USER_DATA[data["seller_id"]]["balance"] += cost
    
    buyer_inv = USER_DATA[ctx.author.id].setdefault("inventory", {})
    buyer_inv[data["item_id"]] = buyer_inv.get(data["item_id"], 0) + data["quantity"]
    
    await save_user_data()
    await ctx.send(f"✅ Purchase complete! You bought **{data['quantity']}x {ITEMS_DATABASE.get(data['item_id'], {}).get('name', data['item_id'])}** for `{cost:,}` coins.")

@ah.command(name="bid")
async def ah_bid(ctx, listing_id: str, bid_amount: int):
    if ctx.author.id in AUCTION_BLACKLIST:
        await ctx.send("❌ You are blacklisted from using the Auction House system.")
        return
        
    listing_id = listing_id.upper()
    if listing_id not in AUCTION_HOUSE:
        await ctx.send("❌ Listing ID not found or already closed.")
        return
        
    data = AUCTION_HOUSE[listing_id]
    if data["type"] != "bid":
        await ctx.send("❌ This listing is configured as an instant 'Buy It Now' item. Use `!ah buy <id>` instead.")
        return
        
    if data["seller_id"] == ctx.author.id:
        await ctx.send("❌ You cannot place bids on your own listings.")
        return
        
    if bid_amount <= data["highest_bid"]:
        await ctx.send(f"❌ Your bid must exceed the current highest valuation of `{data['highest_bid']:,}` coins.")
        return
        
    await ensure_user(ctx.author.id)
    if USER_DATA[ctx.author.id]["balance"] < bid_amount:
        await ctx.send(f"❌ You lack the liquid wallet balances required to back this bid.")
        return
        
    if data["highest_bidder"] is not None:
        old_bidder = data["highest_bidder"]
        await ensure_user(old_bidder)
        USER_DATA[old_bidder]["balance"] += data["highest_bid"]
        
    USER_DATA[ctx.author.id]["balance"] -= bid_amount
    
    data["highest_bid"] = bid_amount
    data["highest_bidder"] = ctx.author.id
    
    await save_user_data()
    await ctx.send(f"🪙 Bid registered! High bid on listing `{listing_id}` updated to `{bid_amount:,}` coins by {ctx.author.mention}.")

@ah.command(name="cancel")
async def ah_cancel(ctx, listing_id: str):
    listing_id = listing_id.upper()
    if listing_id not in AUCTION_HOUSE:
        await ctx.send("❌ Listing ID not found.")
        return
        
    data = AUCTION_HOUSE[listing_id]
    is_staff = ctx.author.id in ADMIN_IDS
    
    if data["seller_id"] != ctx.author.id and not is_staff:
        await ctx.send("❌ You do not own this listing, nor do you hold administrative privileges.")
        return
        
    AUCTION_HOUSE.pop(listing_id)
    
    await ensure_user(data["seller_id"])
    seller_inv = USER_DATA[data["seller_id"]].setdefault("inventory", {})
    seller_inv[data["item_id"]] = seller_inv.get(data["item_id"], 0) + data["quantity"]
    
    if data["type"] == "bid" and data["highest_bidder"] is not None:
        await ensure_user(data["highest_bidder"])
        USER_DATA[data["highest_bidder"]]["balance"] += data["highest_bid"]
        
    await save_user_data()
    msg = f"🛑 Listing `{listing_id}` canceled by Owner/Admin. Items returned to inventory."
    if data["highest_bidder"]:
        msg += " Active high-bid currency funds refunded back to the bidder."
    await ctx.send(msg)

@ah.command(name="blacklist")
async def ah_blacklist(ctx, member: discord.Member):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ System administration command. Access Denied.")
        return
        
    AUCTION_BLACKLIST.add(member.id)
    await ctx.send(f"⛔ **{member.display_name}** has been blacklisted from interacting with the auction house market.")

@ah.command(name="unblacklist")
async def ah_unblacklist(ctx, member: discord.Member):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ System administration command. Access Denied.")
        return
        
    AUCTION_BLACKLIST.discard(member.id)
    await ctx.send(f"✅ **{member.display_name}** has been unblacklisted from the auction house market.")

@bot.command()
async def rewards(ctx):
    embed = discord.Embed(title="🎖️ All Available Badges & Achievements", color=0x3b82f6)
    
    badge_list = "\n".join([f"{v['name']} - *{v['description']}*" for k, v in BADGE_ITEMS.items()])
    embed.add_field(name="🎖️ Badges", value=badge_list, inline=False)
    
    achievement_list = "\n".join([f"{v['name']} - *{v['description']}*" for k, v in ACHIEVEMENT_ITEMS.items()])
    embed.add_field(name="📜 Achievements", value=achievement_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def dbg_give(ctx, item_type: str, item_name: str, target: discord.Member, amount: int = 1):
    if ctx.author.id not in ADMIN_IDS:
        return
    
    target_id = target.id
    await ensure_user(target_id)
    
    if item_type.lower() == "badge":
        if item_name not in USER_DATA[target_id]["badges"]:
            USER_DATA[target_id]["badges"].append(item_name)
    elif item_type.lower() == "achievement":
        if item_name not in USER_DATA[target_id]["achievements"]:
            USER_DATA[target_id]["achievements"].append(item_name)
    elif item_type.lower() == "shop":
        if item_name in USER_DATA[target_id]["upgrades"]:
            USER_DATA[target_id]["upgrades"][item_name] += amount
        else:
            USER_DATA[target_id]["upgrades"][item_name] = amount
    elif item_type.lower() == "inventory":
        if item_name in USER_DATA[target_id]["inventory"]:
            USER_DATA[target_id]["inventory"][item_name] += amount
        else:
            USER_DATA[target_id]["inventory"][item_name] = amount
            
    await save_user_data()
    await ctx.send(f"✅ Successfully granted {item_name} to {target.display_name}.")

class FriendRequestButtons(discord.ui.View):
    def __init__(self, requester_id):
        super().__init__(timeout=180)
        self.requester_id = requester_id
    @discord.ui.button(label="Accept Friend Request", style=discord.ButtonStyle.success, emoji="🧡")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_id = interaction.user.id
        req_id = self.requester_id
        await ensure_user(target_id)
        await ensure_user(req_id)
        
        if target_id not in FRIENDS: FRIENDS[target_id] = {"friends": [], "requests_out": {}, "requests_in": {}}
        if req_id not in FRIENDS: FRIENDS[req_id] = {"friends": [], "requests_out": {}, "requests_in": {}}
        
        if "friends" not in FRIENDS[target_id]: FRIENDS[target_id]["friends"] = []
        if "friends" not in FRIENDS[req_id]: FRIENDS[req_id]["friends"] = []

        if req_id not in FRIENDS[target_id]["requests_in"]:
            await interaction.response.send_message("**This friend request expired or is no longer valid.**", ephemeral=True)
            self.stop(); return
            
        if req_id not in FRIENDS[target_id]["friends"]:
            FRIENDS[target_id]["friends"].append(req_id)
        if target_id not in FRIENDS[req_id]["friends"]:
            FRIENDS[req_id]["friends"].append(target_id)
            
        USER_DATA[target_id]["friends_list"] = FRIENDS[target_id]["friends"]
        USER_DATA[req_id]["friends_list"] = FRIENDS[req_id]["friends"]
        
        del FRIENDS[target_id]["requests_in"][req_id]
        del FRIENDS[req_id]["requests_out"][target_id]
        
        await save_friends_data()
        await save_user_data()
        
        await interaction.response.send_message("**Friend request accepted! You are now friends.**", ephemeral=True)
        requester = bot.get_user(req_id)
        if requester:
            embed = discord.Embed(title="✅ FRIEND REQUEST ACCEPTED", description=f"**{interaction.user.name} accepted your friend request!**", color=0x00cc00)
            await requester.send(embed=embed)
        self.stop()
    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_id = interaction.user.id
        req_id = self.requester_id
        
        if target_id not in FRIENDS: FRIENDS[target_id] = {"friends": [], "requests_out": {}, "requests_in": {}}
        if req_id not in FRIENDS: FRIENDS[req_id] = {"friends": [], "requests_out": {}, "requests_in": {}}
        
        if req_id in FRIENDS[target_id]["requests_in"]:
            del FRIENDS[target_id]["requests_in"][req_id]
            del FRIENDS[req_id]["requests_out"][target_id]
        await save_friends_data()
        await interaction.response.send_message("**Friend request declined.**", ephemeral=True)
        self.stop()

# Helper to save friends data
# First, ensure your save_friends_data is defined like this:
async def save_friends_data():
    async with file_lock:
        try:
            export_data = {str(k): v for k, v in FRIENDS.items()}
            temp_file = FRIENDS_FILE + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(export_data, f, indent=4)
            os.replace(temp_file, FRIENDS_FILE)
        except Exception as e:
            print(f"Error saving FRIENDS: {e}")

@bot.command()
async def friend(ctx, target: discord.Member = None):
    if not target or target == ctx.author: 
        return
        
    rid = ctx.author.id
    tid = target.id
    
    await ensure_user(rid)
    await ensure_user(tid)
    
    # Ensure friendship structures exist for these users
    if rid not in FRIENDS: FRIENDS[rid] = {"friends": [], "requests_out": {}, "requests_in": {}}
    if tid not in FRIENDS: FRIENDS[tid] = {"friends": [], "requests_out": {}, "requests_in": {}}

    if tid in FRIENDS[rid].get("friends", []):
        await ctx.send("**You are already friends with this person!**")
        return
    if tid in FRIENDS[rid]["requests_out"]:
        await ctx.send("**You already have a pending friend request sent to them.**")
        return
        
    FRIENDS[rid]["requests_out"][tid] = True
    FRIENDS[tid]["requests_in"][rid] = True
    
    # Save the pending request state to file
    await save_friends_data()
    
    embed_in = discord.Embed(title="🧡 NEW FRIEND REQUEST", description=f"**{ctx.author.name}** has sent you a friend request!", color=0xeab308)
    try:
        await target.send(embed=embed_in, view=FriendRequestButtons(rid))
        await ctx.send(f"**Friend request has been sent to {target.mention}!**")
    except:
        await ctx.send("**We couldn't send the request. That user might have their direct messages closed.**")
        # Revert changes and save if sending fails
        del FRIENDS[rid]["requests_out"][tid]
        del FRIENDS[tid]["requests_in"][rid]
        await save_friends_data()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    user_id = message.author.id
    if user_id in USER_DATA:
        current_time = time.time()
        last_interest = USER_DATA[user_id].get("last_interest_time", current_time)
        
        if current_time - last_interest >= 600:
            debt = USER_DATA[user_id].get("loan_debt", 0)
            if debt >= 5000:
                current_rate = USER_DATA[user_id].get("interest_rate", 1.0)
                
                # Check if the float multiplication or size will exceed system limits to prevent OverflowError
                try:
                    # Perform math using integer operations where possible, or catch the float overflow early
                    new_debt = int(debt * current_rate)
                    # Handle safety check if integer conversion explodes or hits infinity limits
                    if new_debt > 10**300: 
                        new_debt = 10**300
                    USER_DATA[user_id]["loan_debt"] = new_debt
                except (OverflowError, ValueError):
                    USER_DATA[user_id]["loan_debt"] = 10**300

                # Cap interest rate growth to prevent it from reaching infinity
                next_rate = current_rate + 0.1
                if next_rate > 1000.0:
                    next_rate = 1000.0
                USER_DATA[user_id]["interest_rate"] = next_rate
                
                USER_DATA[user_id]["last_interest_time"] = current_time
                await save_user_data()
    
    await bot.process_commands(message)

async def apply_gambling_winnings(user_id, amount):
    global DOUBLE_PROFIT_END, DEBT_PAYOFF_END
    await ensure_user(user_id)
    
    if time.time() < DOUBLE_PROFIT_END:
        amount *= 2
        
    if time.time() < DEBT_PAYOFF_END:
        debt = USER_DATA[user_id].get("loan_debt", 0)
        paid = min(debt, amount)
        USER_DATA[user_id]["loan_debt"] -= paid
        amount -= paid
    
    debt = USER_DATA[user_id].get("loan_debt", 0)
    if debt > 0:
        paid = min(debt, amount)
        USER_DATA[user_id]["loan_debt"] -= paid
        amount -= paid
    
    USER_DATA[user_id]["balance"] += amount
    await save_user_data()

@bot.command()
async def debt(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if "loan_debt" not in USER_DATA[user_id]:
        USER_DATA[user_id]["loan_debt"] = 0
    if "interest_rate" not in USER_DATA[user_id]:
        USER_DATA[user_id]["interest_rate"] = 1.0
    if "last_payment_deadline" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_payment_deadline"] = time.time()
        
    debt_val = USER_DATA[user_id].get("loan_debt", 0)
    rate = USER_DATA[user_id].get("interest_rate", 1.0)
    
    if debt_val > 0:
        now = time.time()
        time_since_deadline = now - USER_DATA[user_id]["last_payment_deadline"]
        if time_since_deadline >= 600:
            missed_intervals = int(time_since_deadline // 600)
            interest_increase = missed_intervals * 0.2
            USER_DATA[user_id]["interest_rate"] += interest_increase
            USER_DATA[user_id]["last_payment_deadline"] += missed_intervals * 600
            rate = USER_DATA[user_id]["interest_rate"]
            
    embed = discord.Embed(title="💳 Loan Status", color=0x3b82f6)
    embed.add_field(name="Current Debt", value=f"**${debt_val:,}**", inline=True)
    embed.add_field(name="Current Interest Rate", value=f"**{rate:.1f}x**", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def bribe(ctx, amount_str: str = "1"):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if "upgrades" not in USER_DATA[user_id]:
        USER_DATA[user_id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "xp_booster": 0, "vip_lounge": 0, "loan_bribe": 0}
        
    bribe_count = USER_DATA[user_id]["upgrades"].get("loan_bribe", 0)
    if bribe_count <= 0:
        await ctx.send("❌ You don't have any clean ledgers or fake IDs purchased! Buy a `loan_bribe` upgrade in the `!shop` first.")
        return

    amount_str = amount_str.strip().lower()
    if amount_str == "max":
        target_amount = bribe_count
    else:
        try:
            target_amount = max(1, int(amount_str))
        except ValueError:
            target_amount = 1

    target_amount = min(target_amount, bribe_count)

    bribes_used = 0
    debt_cleared = 0
    trespass_cleared = False

    for _ in range(target_amount):
        has_cleared_something = False

        if USER_DATA[user_id].get("trespassed", False):
            USER_DATA[user_id]["trespassed"] = False
            trespass_cleared = True
            has_cleared_something = True

        current_debt = USER_DATA[user_id].get("loan_debt", 0)
        if current_debt > 0:
            USER_DATA[user_id]["loan_debt"] = max(0, current_debt - 5000)
            debt_cleared += 5000
            has_cleared_something = True

        if has_cleared_something:
            bribes_used += 1
            USER_DATA[user_id]["upgrades"]["loan_bribe"] -= 1
        else:
            break

    if bribes_used > 0:
        log_output = ""
        if trespass_cleared:
            log_output += "• Your **Trespass** flag has been entirely expunged from casino records.\n"
        if debt_cleared > 0:
            log_output += f"• Subtracted **${debt_cleared:,}** from your active Loan Shark liabilities.\n"

        embed = discord.Embed(
            title="📜 Papers Exchanged", 
            description=f"You successfully burned **{bribes_used}** fake ID / clean ledger item(s):\n\n{log_output}\nRemaining Bribes in Stock: **{USER_DATA[user_id]['upgrades']['loan_bribe']}**", 
            color=0x10b981
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ You have no active debts and are not trespassed. Save your upgrade items for when you are in trouble!")

@bot.command()
async def borrow(ctx, amount: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if USER_DATA[user_id].get("trespassed", False):
        await ctx.send("❌ Security won't let you talk to the Loan Shark while trespassed.")
        return
        
    if "loan_debt" not in USER_DATA[user_id]:
        USER_DATA[user_id]["loan_debt"] = 0
    if "interest_rate" not in USER_DATA[user_id]:
        USER_DATA[user_id]["interest_rate"] = 1.0
    if "reputation" not in USER_DATA[user_id]:
        USER_DATA[user_id]["reputation"] = 0
    if "last_loan_timestamp" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_loan_timestamp"] = 0
    if "last_payment_deadline" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_payment_deadline"] = 0
        
    if amount <= 0:
        await ctx.send("❌ Invalid borrowing amount.")
        return

    now = time.time()
    time_elapsed = now - USER_DATA[user_id]["last_loan_timestamp"]
    if time_elapsed < 86400:
        remaining_time = int(86400 - time_elapsed)
        await ctx.send(f"❌ **The Loan Shark turns you away!** You can only borrow once every 24 hours. Try again in **{remaining_time // 3600}h {(remaining_time % 3600) // 60}m**.")
        return

    user_level = USER_DATA[user_id].get("level", 1)
    
    if user_level >= 100:
        base_cap = 100000
    elif user_level >= 75:
        base_cap = 75000
    elif user_level >= 50:
        base_cap = 50000
    elif user_level >= 20:
        base_cap = 25000
    elif user_level >= 15:
        base_cap = 20000
    elif user_level >= 10:
        base_cap = 15000
    elif user_level >= 5:
        base_cap = 10000
    elif user_level >= 1:
        base_cap = 5000
    else:
        base_cap = 0

    user_rep = USER_DATA[user_id]["reputation"]
    
    if user_rep < 0:
        final_cap = base_cap // 2
        rep_status = "📉 **Bad Reputation (Cap Halved)**"
    elif user_rep > 50:
        final_cap = base_cap + 5000
        rep_status = "📈 **Good Reputation (+$5,000 Bonus)**"
    else:
        final_cap = base_cap
        rep_status = "😐 **Neutral Reputation**"

    if amount > final_cap:
        await ctx.send(f"❌ **The Loan Shark scoffs!** Based on your level ({user_level}) and reputation, your absolute maximum borrow limit is **${final_cap:,} chips**.\nStatus: {rep_status}")
        return

    USER_DATA[user_id]["balance"] += amount
    USER_DATA[user_id]["loan_debt"] += amount
    USER_DATA[user_id]["debt"] = USER_DATA[user_id].get("debt", 0) + amount
    USER_DATA[user_id]["last_loan_timestamp"] = now
    USER_DATA[user_id]["last_payment_deadline"] = now

    embed = discord.Embed(title="🤝 Deal Sealed", description=f"The Loan Shark handed you **{amount:,}** chips under the table.\n\nStatus: {rep_status}\nYour total outstanding debt is now **${USER_DATA[user_id]['loan_debt']:,}** chips.", color=0x7c3aed)
    await ctx.send(embed=embed)

@bot.command()
async def pay_loan(ctx, amount: int):
    user_id = ctx.author.id
    await ensure_user(user_id)

    if "loan_debt" not in USER_DATA[user_id] or USER_DATA[user_id]["loan_debt"] <= 0:
        await ctx.send("❌ You do not have any active loans to pay off.")
        return

    if amount <= 0:
        await ctx.send("❌ Please provide a valid amount to pay.")
        return

    if USER_DATA[user_id]["balance"] < amount:
        await ctx.send("❌ You do not have enough chips in your balance to make this payment.")
        return

    if "reputation" not in USER_DATA[user_id]:
        USER_DATA[user_id]["reputation"] = 0
    if "interest_rate" not in USER_DATA[user_id]:
        USER_DATA[user_id]["interest_rate"] = 1.0
    if "last_payment_deadline" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_payment_deadline"] = time.time()

    now = time.time()
    time_since_deadline = now - USER_DATA[user_id]["last_payment_deadline"]
    
    if time_since_deadline >= 600:
        missed_intervals = int(time_since_deadline // 600)
        interest_increase = missed_intervals * 0.2
        USER_DATA[user_id]["interest_rate"] += interest_increase
        USER_DATA[user_id]["last_payment_deadline"] += missed_intervals * 600
        await ctx.send(f"⚠️ **Interest Increased!** You missed paying your $5,000 baseline every 10 minutes. Your interest rate went up by **{interest_increase:.1f}x**!")

    debt_owed = USER_DATA[user_id]["loan_debt"]
    
    if amount >= debt_owed:
        payment = debt_owed
        USER_DATA[user_id]["balance"] -= payment
        USER_DATA[user_id]["loan_debt"] = 0
        USER_DATA[user_id]["reputation"] += 10
        USER_DATA[user_id]["interest_rate"] = 1.0
        msg = f"🎉 **You have completely paid off your loan!** Your interest rate has reset to 1.0x and your reputation increased by **10** (Current Rep: {USER_DATA[user_id]['reputation']})."
    else:
        USER_DATA[user_id]["balance"] -= amount
        USER_DATA[user_id]["loan_debt"] -= amount
        USER_DATA[user_id]["reputation"] += 2
        
        if amount >= 5000:
            USER_DATA[user_id]["last_payment_deadline"] = now
            
        msg = f"💰 You paid **${amount:,}** chips toward your debt. Remaining Debt: **${USER_DATA[user_id]['loan_debt']:,}** chips.\nYour reputation increased by **2** (Current Rep: {USER_DATA[user_id]['reputation']})."

    await ctx.send(msg)
    await save_user_data()

@bot.command()
async def rob(ctx, target: discord.Member = None):
    user_id = ctx.author.id
    now = time.time()
    
    await ensure_user(user_id)

    if target is None:
        if now < USER_DATA[user_id].get("trespassed", 0):
            remaining_trespass = int(USER_DATA[user_id]["trespassed"] - now)
            await ctx.send(f"🚨 **Security Barred!** You are arrested and can not go back to the casino for another **{remaining_trespass} seconds**.")
            return

        if "reputation" not in USER_DATA[user_id]:
            USER_DATA[user_id]["reputation"] = 0

        embed_confirm = discord.Embed(
            title="⚠️ Dangerous Move...",
            description="Are you absolutely sure you want to rob the loan sharks? There is a real chance you could die or end up arrested in the process.",
            color=0xeab308
        )

        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.value = None

            @discord.ui.button(label="Yes, let's do this", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                    return
                self.value = True
                self.stop()

            @discord.ui.button(label="No, back out", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                    return
                self.value = False
                self.stop()

        view = ConfirmView()
        msg = await ctx.send(embed=embed_confirm, view=view)
        await view.wait()

        if view.value is None:
            await msg.edit(content="⏱️ **Decision timed out.** You decided to stay away from trouble.", embed=None, view=None)
            return
        elif view.value is False:
            await msg.edit(content="❌ **Operation called off.** Wise choice.", embed=None, view=None)
            return

        USER_DATA[user_id]["reputation"] -= 15
        roll = random.random()

        if roll < 0.25:
            USER_DATA[user_id]["balance"] = 0
            if "debt" in USER_DATA[user_id]:
                USER_DATA[user_id]["debt"] += 10000
            embed_dead = discord.Embed(
                title="💀 WASTED",
                description=f"The loan sharks didn't hesitate. They pulled weapons and took you out immediately.\n\n"
                            f"💸 **Losses:** All pocket balance cleared.\n"
                            f"📉 **Reputation Lost:** 15 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                color=0x000000
            )
            await msg.edit(embed=embed_dead, view=None)
            await save_user_data()
            return

        elif roll < 0.50:
            stolen_cash = random.randint(5000, 25000)
            user_debt = USER_DATA[user_id].get("debt", 0)
            
            allocation_msg = ""
            if user_debt > 0:
                if stolen_cash <= user_debt:
                    USER_DATA[user_id]["debt"] -= stolen_cash
                    allocation_msg = f"💰 You stole **${stolen_cash:,} chips**! The entire amount has been automatically paid toward your debt."
                else:
                    remainder = stolen_cash - user_debt
                    USER_DATA[user_id]["debt"] = 0
                    await apply_gambling_winnings(user_id, remainder)
                    allocation_msg = f"💰 You stole **${stolen_cash:,} chips**! Your total debt of **${user_debt:,} chips** has been fully paid off, and the remaining **${remainder:,} chips** went to your balance."
            else:
                await apply_gambling_winnings(user_id, stolen_cash)
                allocation_msg = f"💰 You stole **${stolen_cash:,} chips**! Since you have no active debt, everything has been added directly to your balance."

            embed_loot = discord.Embed(
                title="💰 Successful Loan Shark Heist!",
                description=f"{allocation_msg}\n📉 Your high-profile crime dropped your reputation by **15** points (Current Rep: {USER_DATA[user_id]['reputation']}).",
                color=0x22c55e
            )
            await msg.edit(embed=embed_loot, view=None)
            await save_user_data()
            return

        else:
            stolen_from_you = min(10000, USER_DATA[user_id]["balance"])
            USER_DATA[user_id]["balance"] -= stolen_from_you
            
            sentence_duration = 1200
            USER_DATA[user_id]["trespassed"] = now + sentence_duration

            embed_caught = discord.Embed(
                title="🚓 Caught Mid-Act!",
                description=f"The loan sharks caught you sneaking around. Instead of wasting you, they roughed you up, took your money, and threw you to the cops!\n\n"
                            f"💸 **Looted by Sharks:** ${stolen_from_you:,} chips\n"
                            f"⏳ **Prison Sentence:** You are arrested and can not go back to the casino for **{sentence_duration} seconds**.\n"
                            f"📉 **Reputation Lost:** 15 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                color=0xef4444
            )
            await msg.edit(embed=embed_caught, view=None)
            await save_user_data()
            return

    await ensure_user(target.id)

    if target.id == user_id:
        await ctx.send("❌ **You cannot pickpocket your own pockets!**")
        return

    if USER_DATA[user_id]["settings"].get("passive_mode", False):
        await ctx.send("🛡️ **You are in Passive Mode!** Turn it off in your configuration panel via `!settings` if you wish to orchestrate heists.")
        return

    if USER_DATA[target.id]["settings"].get("passive_mode", False):
        await ctx.send(f"🛡️ **Heist failed!** {target.mention} is currently shielded by Passive Mode preferences.")
        return

    if now < USER_DATA[user_id].get("trespassed", 0):
        remaining_trespass = int(USER_DATA[user_id]["trespassed"] - now)
        await ctx.send(f"🚨 **Security Barred!** You are arrested and can not go back to the casino for another **{remaining_trespass} seconds**.")
        return

    cooldown = 7200 if USER_DATA[user_id].get("last_rob_cooldown_increase", False) else 3600
    if now - USER_DATA[user_id].get("last_rob", 0) < cooldown:
        remaining_cd = int(cooldown - (now - USER_DATA[user_id].get("last_rob", 0)))
        await ctx.send(f"❌ **You are on a cooldown!** Try again in **{remaining_cd // 60}m {remaining_cd % 60}s**.")
        return

    target_balance = USER_DATA[target.id]["balance"]
    if target_balance < 1000:
        await ctx.send(f"💸 **{target.display_name} is too broke to target right now!** They need at least $1,000 chips on hand.")
        return

    USER_DATA[user_id]["last_rob"] = now
    
    if "reputation" not in USER_DATA[user_id]:
        USER_DATA[user_id]["reputation"] = 0

    if random.random() < 0.4:
        max_steal = min(5000, target_balance)
        if max_steal <= 1000:
            steal_amt = max_steal
        else:
            steal_amt = random.randint(1000, max_steal)
            
        USER_DATA[target.id]["balance"] -= steal_amt
        await apply_gambling_winnings(user_id, steal_amt)
        USER_DATA[user_id]["last_rob_cooldown_increase"] = False
        USER_DATA[user_id]["reputation"] -= 5
        
        embed_success = discord.Embed(
            title="⚔️ Successful Pickpocket!",
            description=f"You successfully snuck into {target.mention}'s pockets and made off with **${steal_amt:,} chips**!\n📉 Your criminal behavior dropped your reputation by **5** points (Current Rep: {USER_DATA[user_id]['reputation']}).",
            color=0x22c55e
        )
        await ctx.send(embed=embed_success)
    else:
        USER_DATA[user_id]["reputation"] -= 8
        if random.random() < 0.5:
            USER_DATA[user_id]["trespassed"] = now + 600
            USER_DATA[user_id]["last_rob_cooldown_increase"] = True
            
            penalty_amt = min(2000, USER_DATA[user_id]["balance"])
            if penalty_amt > 0:
                USER_DATA[user_id]["balance"] -= penalty_amt
            
            embed_busted = discord.Embed(
                title="👮 BUSTED BY SECURITY!",
                description=f"Local authorities caught you red-handed! \n\n"
                            f"🛑 **Fine Paid:** ${penalty_amt:,} chips\n"
                            f"⏳ **Arrest Penalty:** 10 Minutes lock\n"
                            f"🕒 **Cooldown Increase:** 2 Hours\n"
                            f"📉 **Reputation Lost:** 8 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                color=0xef4444
            )
            await ctx.send(embed=embed_busted)
        else:
            USER_DATA[user_id]["last_rob_cooldown_increase"] = False
            await ctx.send(f"💨 **You couldn't find a clean opening.** You failed to rob {target.display_name}, but managed to slip away unnoticed.\n📉 Your reputation dropped by **8** points for being spotted sneaking around (Current Rep: {USER_DATA[user_id]['reputation']}).")

    await save_user_data()

@bot.command()
async def prison(ctx):
    user_id = ctx.author.id
    now = time.time()
    await ensure_user(user_id)

    if now >= USER_DATA[user_id].get("trespassed", 0):
        await ctx.send("❔ **You are not currently incarcerated or arrested.**")
        return

    remaining = int(USER_DATA[user_id]["trespassed"] - now)

    embed_prison = discord.Embed(
        title="🏢 Main Prison Hub",
        description=f"You are locked within the facility walls. Time Remaining: **{remaining} seconds**.\nSelect an administrative or tactical action below:",
        color=0x1f2937
    )

    class PrisonHubView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="Start a Riot", style=discord.ButtonStyle.danger)
        async def riot(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            USER_DATA[user_id]["reputation"] -= 20
            riot_roll = random.random()
            
            if riot_roll < 0.35:
                USER_DATA[user_id]["balance"] = 0
                if "debt" in USER_DATA[user_id]:
                    USER_DATA[user_id]["debt"] += 20000
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="💀 Riot Suppressed Lethally",
                    description=f"The guards deployed extreme tactical countermeasures. You did not survive the containment effort.\n\n"
                                f"💸 **Losses:** All pocket balance cleared.\n"
                                f"📉 **Reputation Lost:** 20 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x000000
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            elif riot_roll < 0.80:
                added_time = 1800
                USER_DATA[user_id]["trespassed"] += added_time
                new_remaining = int(USER_DATA[user_id]["trespassed"] - time.time())
                embed_res = discord.Embed(
                    title="👮 Riot Failed & Solitary Imposed",
                    description=f"The guard forces put down the insurrection. You were isolated and thrown into deep solitary refinement.\n\n"
                                f"⏳ **Added Sentence:** +30 Minutes\n"
                                f"🕒 **Total Remaining Time:** {new_remaining} seconds\n"
                                f"📉 **Reputation Lost:** 20 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0xef4444
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            else:
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="🔓 Riot Overruns Gates!",
                    description=f"The absolute chaos completely overwhelmed structural defenses! You ran right out the front doors undetected.\n\n"
                                f"📉 **Reputation Lost:** 20 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x22c55e
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
                
            await save_user_data()

        @discord.ui.button(label="Prison Break (Call Friend)", style=discord.ButtonStyle.primary)
        async def prison_break_opt(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            await interaction.response.send_message(f"📢 {interaction.user.mention} is requesting extraction from jail! A friend must run `!prison_break @{interaction.user.name}` to bust them out.", ephemeral=False)

        @discord.ui.button(label="Attempt Escape Yourself", style=discord.ButtonStyle.danger)
        async def escape(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            USER_DATA[user_id]["reputation"] -= 10
            escape_roll = random.random()
            
            if escape_roll < 0.30:
                USER_DATA[user_id]["balance"] = 0
                if "debt" in USER_DATA[user_id]:
                    USER_DATA[user_id]["debt"] += 15000
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="💀 Lethal Force Authorized",
                    description=f"The guards caught you scaling the fence and opened fire. You died during the escape attempt.\n\n"
                                f"💸 **Losses:** All pocket balance cleared.\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x000000
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            elif escape_roll < 0.75:
                added_time = 1200
                USER_DATA[user_id]["trespassed"] += added_time
                new_remaining = int(USER_DATA[user_id]["trespassed"] - time.time())
                embed_res = discord.Embed(
                    title="🚨 Escape Failed!",
                    description=f"Guards tackled you before you reached the perimeter. Extra charges have been tacked on.\n\n"
                                f"⏳ **Added Sentence:** +20 Minutes\n"
                                f"🕒 **Total Remaining Time:** {new_remaining} seconds\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0xef4444
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            else:
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="🏃 Into the Shadows!",
                    description=f"You successfully slipped past the guards and broke out of prison! You are now free to enter the casino.\n\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x22c55e
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
                
            await save_user_data()

        @discord.ui.button(label="Pay Bail (Self-Bail Alternative)", style=discord.ButtonStyle.success)
        async def pay_bail_opt(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            bail_cost = 10000
            if USER_DATA[user_id]["balance"] < bail_cost:
                await interaction.response.send_message(f"💸 **Insolvent!** Direct personal emergency bail costs **${bail_cost:,} chips**. Ask a friend to run `!bail @{interaction.user.name}` for the regular rate.", ephemeral=True)
                return
                
            USER_DATA[user_id]["balance"] -= bail_cost
            USER_DATA[user_id]["trespassed"] = 0
            USER_DATA[user_id]["reputation"] -= 5
            
            embed_res = discord.Embed(
                title="🕊️ Self Bail Processed",
                description=f"You handled your legal fees directly and processed an emergency cash bail for **${bail_cost:,} chips**.\n\n"
                            f"🔓 You are immediately discharged from custody.\n"
                            f"📉 **Reputation Lost:** 5 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                color=0x3b82f6
            )
            self.stop()
            await interaction.response.edit_message(embed=embed_res, view=None)
            await save_user_data()

        @discord.ui.button(label="Wait Out Your Time", style=discord.ButtonStyle.secondary)
        async def wait_time(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            self.stop()
            await interaction.response.edit_message(content="⏳ You chose to keep your head down and serve your sentence peacefully.", embed=None, view=None)

    await ctx.send(embed=embed_prison, view=PrisonHubView())

@bot.command()
async def prison_options(ctx):
    user_id = ctx.author.id
    now = time.time()
    await ensure_user(user_id)

    if now >= USER_DATA[user_id].get("trespassed", 0):
        await ctx.send("❔ **You are not currently incarcerated or arrested.**")
        return

    remaining = int(USER_DATA[user_id]["trespassed"] - now)

    embed_prison = discord.Embed(
        title="🏢 Local Jail Facility",
        description=f"You are currently locked down for another **{remaining} seconds**.\nChoose your course of action below:",
        color=0x374151
    )

    class PrisonView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=40)
            self.ctx = ctx

        @discord.ui.button(label="Attempt Escape", style=discord.ButtonStyle.danger)
        async def escape(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            USER_DATA[user_id]["reputation"] -= 10
            escape_roll = random.random()
            
            if escape_roll < 0.30:
                USER_DATA[user_id]["balance"] = 0
                if "debt" in USER_DATA[user_id]:
                    USER_DATA[user_id]["debt"] += 15000
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="💀 Lethal Force Authorized",
                    description=f"The guards caught you scaling the fence and opened fire. You died during the escape attempt.\n\n"
                                f"💸 **Losses:** All pocket balance cleared.\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x000000
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            elif escape_roll < 0.75:
                added_time = 1200
                USER_DATA[user_id]["trespassed"] += added_time
                new_remaining = int(USER_DATA[user_id]["trespassed"] - time.time())
                embed_res = discord.Embed(
                    title="🚨 Escape Failed!",
                    description=f"Guards tackled you before you reached the perimeter. Extra charges have been tacked on.\n\n"
                                f"⏳ **Added Sentence:** +20 Minutes\n"
                                f"🕒 **Total Remaining Time:** {new_remaining} seconds\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0xef4444
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
            else:
                USER_DATA[user_id]["trespassed"] = 0
                embed_res = discord.Embed(
                    title="🏃 Into the Shadows!",
                    description=f"You successfully slipped past the guards and broke out of prison! You are now free to enter the casino.\n\n"
                                f"📉 **Reputation Lost:** 10 points (Current Rep: {USER_DATA[user_id]['reputation']})",
                    color=0x22c55e
                )
                self.stop()
                await interaction.response.edit_message(embed=embed_res, view=None)
                
            await save_user_data()

        @discord.ui.button(label="Wait Your Time", style=discord.ButtonStyle.secondary)
        async def wait_time(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("This menu is not for you.", ephemeral=True)
                return
            
            await interaction.response.edit_message(content="⏳ You chose to keep your head down and serve your sentence peacefully.", embed=None, view=None)
            self.stop()

    await ctx.send(embed=embed_prison, view=PrisonView())

@bot.command()
async def bail(ctx, target: discord.Member):
    user_id = ctx.author.id
    target_id = target.id
    now = time.time()

    await ensure_user(user_id)
    await ensure_user(target_id)

    if target_id == user_id:
        await ctx.send("❌ **You cannot pay your own bail this way!**")
        return

    if now >= USER_DATA[target_id].get("trespassed", 0):
        await ctx.send(f"❔ **{target.display_name} is not currently arrested.**")
        return

    bail_cost = 5000
    if USER_DATA[user_id]["balance"] < bail_cost:
        await ctx.send(f"💸 **You don't have enough money!** Paying bail for a friend costs **${bail_cost:,} chips**.")
        return

    USER_DATA[user_id]["balance"] -= bail_cost
    USER_DATA[target_id]["trespassed"] = 0
    USER_DATA[target_id]["reputation"] -= 5

    embed_bail = discord.Embed(
        title="🕊️ Posted Bail!",
        description=f"{ctx.author.mention} paid **${bail_cost:,} chips** to post bail for {target.mention}!\n\n"
                    f"🔓 {target.display_name} is now immediately released from prison.\n"
                    f"📉 {target.display_name}'s reputation dropped by **5** points (Current Rep: {USER_DATA[target_id]['reputation']}).",
        color=0x3b82f6
    )
    await ctx.send(embed=embed_bail)
    await save_user_data()

@bot.command()
async def prison_break(ctx, target: discord.Member):
    user_id = ctx.author.id
    target_id = target.id
    now = time.time()

    await ensure_user(user_id)
    await ensure_user(target_id)

    if target_id == user_id:
        await ctx.send("❌ **You cannot bust yourself out of prison!** Get a friend to use this command on you.")
        return

    if now >= USER_DATA[target_id].get("trespassed", 0):
        await ctx.send(f"❔ **{target.display_name} is not currently arrested.**")
        return

    if "reputation" not in USER_DATA[user_id]:
        USER_DATA[user_id]["reputation"] = 0
    if "reputation" not in USER_DATA[target_id]:
        USER_DATA[target_id]["reputation"] = 0

    USER_DATA[user_id]["reputation"] -= 15
    USER_DATA[target_id]["reputation"] -= 10

    break_roll = random.random()

    if break_roll < 0.40:
        USER_DATA[user_id]["balance"] = 0
        if "debt" in USER_DATA[user_id]:
            USER_DATA[user_id]["debt"] += 10000
        
        embed_fail = discord.Embed(
            title="💀 Prison Break Disaster!",
            description=f"{ctx.author.mention} attempted a tactical prison break to free {target.mention}, but the operation went completely sideways!\n\n"
                        f"❌ **Result:** {ctx.author.mention} was shot down by tower snipers during the attempt and lost all pocket money.\n"
                        f"⏳ {target.display_name} remains locked up.\n"
                        f"📉 **Reputation Lost:** -15 to your crew, -10 to the prisoner.",
            color=0x000000
        )
        await ctx.send(embed=embed_fail)
    elif break_roll < 0.70:
        added_sentence = 1800
        USER_DATA[target_id]["trespassed"] += added_sentence
        
        embed_caught = discord.Embed(
            title="👮 Tactical Intervention Failed!",
            description=f"The prison break was thwarted! SWAT teams intercepting the breach managed to scatter your operation.\n\n"
                        f"🚨 {ctx.author.mention} escaped into hiding, but security locked down the facility tighter.\n"
                        f"⏳ **Sentence Increased:** +30 Minutes added to {target.mention}'s time.\n"
                        f"📉 **Reputation Lost:** -15 to your crew, -10 to the prisoner.",
            color=0xef4444
        )
        await ctx.send(embed=embed_caught)
    else:
        USER_DATA[target_id]["trespassed"] = 0
        embed_success = discord.Embed(
            title="💥 SUCCESSFUL PRISON BREAK!",
            description=f"{ctx.author.mention} blew open the cell blocks and successfully extracted {target.mention} from maximum security!\n\n"
                        f"🔓 {target.mention} is now free and has left prison walls behind.\n"
                        f"📉 **Reputation Lost:** Both parties lost standing due to the extreme breakout stunt.",
            color=0x22c55e
        )
        await ctx.send(embed=embed_success)

    await save_user_data()

@bot.command()
async def reputation(ctx, target: discord.Member = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if target is None:
        target = ctx.author
    else:
        await ensure_user(target.id)
        
    if "reputation" not in USER_DATA[target.id]:
        USER_DATA[target.id]["reputation"] = 0
        
    rep_val = USER_DATA[target.id]["reputation"]
    
    if rep_val < 0:
        status = "📉 **Bad Reputation**\n↳ *Loan Shark limits are halved!*"
        embed_color = 0xef4444
    elif rep_val > 50:
        status = "📈 **Good Reputation**\n↳ *Eligible for an extra $5,000 on loans!*"
        embed_color = 0x22c55e
    else:
        status = "😐 **Neutral Reputation**\n↳ *Standard level limits apply.*"
        embed_color = 0x3b82f6
        
    embed = discord.Embed(
        title=f"👤 {target.display_name}'s Reputation Profile",
        description=f"Current Reputation Score: **{rep_val:,}**\n\n### Standing Status\n{status}",
        color=embed_color
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command()
async def rep(ctx, operation: str, target: discord.Member):
    user_id = ctx.author.id
    await ensure_user(user_id)
    await ensure_user(target.id)

    if target.id == user_id:
        await ctx.send("❌ You cannot modify your own reputation!")
        return

    if operation not in ["+", "-"]:
        await ctx.send("❌ Invalid operation! Use `+` to give reputation or `-` to subtract reputation.")
        return

    now = time.time()
    if "last_rep_given" not in USER_DATA[user_id]:
        USER_DATA[user_id]["last_rep_given"] = 0

    time_elapsed = now - USER_DATA[user_id]["last_rep_given"]
    if time_elapsed < 86400:
        remaining_time = int(86400 - time_elapsed)
        await ctx.send(f"❌ You have already handed out reputation recently! You can give or subtract 1 reputation point every 24 hours. Try again in **{remaining_time // 3600}h {(remaining_time % 3600) // 60}m**.")
        return

    if "reputation" not in USER_DATA[target.id]:
        USER_DATA[target.id]["reputation"] = 0

    if operation == "+":
        USER_DATA[target.id]["reputation"] += 1
        change_text = "increased"
    else:
        USER_DATA[target.id]["reputation"] -= 1
        change_text = "decreased"

    USER_DATA[user_id]["last_rep_given"] = now
    await save_user_data()

    await ctx.send(f"👥 You have {change_text} {target.display_name}'s reputation by **1** point! (Their Total Rep: {USER_DATA[target.id]['reputation']})")

@bot.command()
async def dbg_rep(ctx, action: str, target: discord.Member, amount: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    await ensure_user(target.id)

    if user_id not in ADMIN_IDS:
        await ctx.send("❌ You do not have permission to execute developer/admin override tools.")
        return

    if action not in ["add", "remove"]:
        await ctx.send("❌ Invalid action! Use `add` or `remove` followed by the user and the exact amount.")
        return

    if amount <= 0:
        await ctx.send("❌ Please specify a positive integer value for the modification amount.")
        return

    if "reputation" not in USER_DATA[target.id]:
        USER_DATA[target.id]["reputation"] = 0

    if action == "add":
        USER_DATA[target.id]["reputation"] += amount
        mod_text = f"Added **{amount}** reputation points to"
    else:
        USER_DATA[target.id]["reputation"] -= amount
        mod_text = f"Removed **{amount}** reputation points from"

    await save_user_data()
    await ctx.send(f"🛠️ **[ADMIN OVERRIDE]** {mod_text} {target.mention}. (New Total Rep: {USER_DATA[target.id]['reputation']})")

@bot.command()
async def beg(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 10:
        remaining = int(10 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before begging again.")
    
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await save_user_data()

    outcomes = [
        (True, "You begged a passerby and they gave you", 100, 1500),
        (True, "A generous gambler felt bad and tossed you", 500, 3000),
        (True, "You found a stray ticket on the floor worth", 50, 1000),
        (True, "You cleaned up some trash and found", 200, 2000),
        (True, "An old man decided to share his winnings of", 1000, 5000),
        (True, "You sang a song and a crowd tipped you", 300, 2500),
        (False, "You begged, but everyone ignored you.", 0, 0),
        (False, "Someone told you to get a job and walked away.", 0, 0),
        (False, "The security guard saw you begging and shooed you off.", 0, 0),
        (False, "You tried to beg but tripped and embarrassed yourself.", 0, 0),
        (False, "Everyone you approached was already broke.", 0, 0),
        (False, "A tourist mistook you for a statue and took a photo instead.", 0, 0)
    ]
    
    success, message, min_amt, max_amt = random.choice(outcomes)
    
    if success:
        amount = random.randint(min_amt, max_amt)
        await apply_gambling_winnings(user_id, amount)
        
        embed = discord.Embed(title="💰 Begging Success", description=f"{message} **${amount:,}** chips!", color=0xfacc15)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="😔 Begging Failed", description=message, color=0xef4444)
        await ctx.send(embed=embed)

class AccountSettingsButtons(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
    @discord.ui.button(label="Toggle DM Notifications", style=discord.ButtonStyle.primary, emoji="🔔")
    async def toggle_dms(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await ensure_user(self.user_id)
        current = USER_DATA[self.user_id]["settings"].get("dm_notifications", True)
        USER_DATA[self.user_id]["settings"]["dm_notifications"] = not current
        status_text = "ENABLED" if not current else "DISABLED"
        await interaction.response.send_message(f"⚙️ **Direct Message hand alerts are now {status_text}!**", ephemeral=True)
    @discord.ui.button(label="Toggle Profile Visibility", style=discord.ButtonStyle.secondary, emoji="👁️")
    async def toggle_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await ensure_user(self.user_id)
        current = USER_DATA[self.user_id]["settings"].get("public_profile", True)
        USER_DATA[self.user_id]["settings"]["public_profile"] = not current
        status_text = "PUBLIC" if not current else "PRIVATE"
        await interaction.response.send_message(f"⚙️ **Your profile layout state is now set to {status_text}!**", ephemeral=True)
    @discord.ui.button(label="Toggle Transfer 2FA", style=discord.ButtonStyle.danger, emoji="🔒")
    async def toggle_2fa(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await ensure_user(self.user_id)
        current = USER_DATA[self.user_id]["settings"].get("transfer_2fa", False)
        USER_DATA[self.user_id]["settings"]["transfer_2fa"] = not current
        await save_user_data()
        status_text = "ENABLED" if not current else "DISABLED"
        await interaction.response.send_message(f"⚙️ **One-time payment code verification is now {status_text}!**", ephemeral=True)
    @discord.ui.button(label="Toggle Passive Mode", style=discord.ButtonStyle.success, emoji="🛡️")
    async def toggle_passive(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await ensure_user(self.user_id)
        current = USER_DATA[self.user_id]["settings"].get("passive_mode", False)
        USER_DATA[self.user_id]["settings"]["passive_mode"] = not current
        await save_user_data()
        status_text = "ENABLED" if not current else "DISABLED"
        await interaction.response.send_message(f"🛡️ **Passive Mode is now {status_text}!** You cannot rob or be robbed by anyone.", ephemeral=True)
    @discord.ui.button(label="Cycle Pay Permissions", style=discord.ButtonStyle.primary, emoji="💸")
    async def cycle_pay_permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await ensure_user(self.user_id)
        current = USER_DATA[self.user_id]["settings"].get("pay_permissions", "everyone")
        
        if current == "everyone":
            new_perm = "friends"
            status_text = "FRIENDS ONLY"
        elif current == "friends":
            new_perm = "no_one"
            status_text = "DISABLED (NO ONE)"
        else:
            new_perm = "everyone"
            status_text = "EVERYONE"
            
        USER_DATA[self.user_id]["settings"]["pay_permissions"] = new_perm
        await save_user_data()
        await interaction.response.send_message(f"💸 **Inbound payment allowance rule updated to: {status_text}!**", ephemeral=True)

@bot.command()
async def settings(ctx):
    await ensure_user(ctx.author.id)
    
    # Save the current state in case ensure_user created a new profile for the user
    await save_user_data()
    
    embed = discord.Embed(
        title="⚙️ Personal Account Customization Settings", 
        description="**Click on the layout option buttons below to switch your public alerts and private gameplay preferences:**", 
        color=0x4b5563
    )
    # The view will handle the button clicks; make sure the callback logic 
    # inside AccountSettingsButtons also calls await save_user_data()
    await ctx.send(embed=embed, view=AccountSettingsButtons(ctx.author.id))

class PayConfirmationView(discord.ui.View):
    def __init__(self, author_id, member, amount):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.member = member
        self.amount = amount
        self.confirmed = None

    @discord.ui.button(label="Confirm Transfer", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This confirmation menu is not for you.", ephemeral=True)
            return
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel Transfer", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This confirmation menu is not for you.", ephemeral=True)
            return
        self.confirmed = False
        self.stop()
        await interaction.response.defer()

class PayConfirmationView(discord.ui.View):
    def __init__(self, author_id, member, amount):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.member = member
        self.amount = amount
        self.confirmed = None

    @discord.ui.button(label="Confirm Transfer", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This confirmation menu is not for you.", ephemeral=True)
            return
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel Transfer", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This confirmation menu is not for you.", ephemeral=True)
            return
        self.confirmed = False
        self.stop()
        await interaction.response.defer()

class RulesPaginationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.game_data = {
            "bj": {"name": "♣️ Blackjack", "rules": "**Get closer to 21 than the dealer without going over!**\n\n• Cards: Number cards face value, J/Q/K 10, A 1 or 11.\n• Hit to draw, stand to hold.\n• Dealer hits on 16, stands on 17+.\n• Blackjack: 150% payout, Win: 100%, Bust/Lose: Loss."},
            "coinflip": {"name": "⏣ Coinflip", "rules": "**Classic 50/50 odds!**\n\n• Type `!coinflip <bet> <heads/tails>`.\n• If it lands on your pick, you win double your bet.\n• Otherwise, the house takes your chips."},
            "crash": {"name": "📈 Crash", "rules": "**Watch the multiplier climb and cash out before it crashes!**\n\n• Type `!crash <bet>`.\n• Multiplier increases over time.\n• Click cashout before the random crash to multiply your bet."},
            "daily": {"name": "📅 Daily", "rules": "**Claim your free daily allowance!**\n\n• Type `!daily` once every 24 hours.\n• Rewards increase based on your current streak!"},
            "diceduel": {"name": "🎲 Dice Duel", "rules": "**Higher roll wins!**\n\n• Type `!diceduel <bet>`.\n• You and the bot each roll a 6-sided die.\n• Highest roll takes the pot."},
            "highlow": {"name": "🔼 High-Low", "rules": "**Guess if the next card is higher or lower!**\n\n• Type `!highlow <bet>`.\n• Guess if the next card drawn from the deck is higher or lower than the current card."},
            "keno": {"name": "🎯 Keno", "rules": "**Pick your numbers and hit the jackpot!**\n\n• Type `!keno <bet>` and select 1-10 numbers (1-80).\n• 20 numbers are drawn.\n• Payout depends on how many numbers you match."},
            "mines": {"name": "💣 Mines", "rules": "**Avoid the bombs!**\n\n• Type `!mines <bet> <mine_count>`.\n• Dig squares on a 5x5 grid.\n• Each safe square increases your multiplier; hit a mine and lose everything."},
            "plinko": {"name": "🔻 Plinko", "rules": "**Drop the ball and see where it lands!**\n\n• Type `!plinko <bet>`.\n• Ball bounces down pins into slots with different multipliers.\n• Further from center = higher payout."},
            "race": {"name": "🏎️ Race", "rules": "**Bet on your favorite racer!**\n\n• Type `!race <bet> <racer_index>`.\n• Watch the race unfold to see if your chosen racer takes 1st place."},
            "roulette": {"name": "🎡 Roulette", "rules": "**Predict where the ball lands!**\n\n• Bet on colors (1:1), even/odd (1:1), or specific numbers (35:1).\n• Type `!roulette <bet> <space>`."},
            "scratch": {"name": "🎫 Scratch", "rules": "**Scratch and match!**\n\n• Type `!scratch <bet>`.\n• Reveal hidden symbols on the card.\n• Match 3 symbols to win the prize shown."},
            "slots": {"name": "🎰 Slots", "rules": "**Spin the reels!**\n\n• Type `!slots <bet>`.\n• Match 3 symbols in a row for massive payouts, or 2 for small returns."}
        }
        
        options = [discord.SelectOption(label=data["name"], value=key) for key, data in self.game_data.items()]
        self.add_item(discord.ui.Select(placeholder="Select a game to view rules...", options=options, custom_id="rules_select"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "rules_select":
            game_key = interaction.data["values"][0]
            game = self.game_data[game_key]
            embed = discord.Embed(title=f"📖 {game['name']} Rules", description=game['rules'], color=0x00cc00)
            await interaction.response.edit_message(embed=embed)
            return False
        return True

class RulesActionButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="View Gambling Rules", style=discord.ButtonStyle.success, emoji="🎲")
    async def view_gambling(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎰 Game Rules Manual", description="Select a game from the menu below to view its specific rules.", color=0x00cc00)
        await interaction.response.send_message(embed=embed, view=RulesPaginationView(), ephemeral=True)
    
    @discord.ui.button(label="View Bot Guidelines", style=discord.ButtonStyle.primary, emoji="📜")
    async def view_bot_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📜 Bot Code of Conduct", description="**1. Play Fairly**\n• No cheating or exploiting.\n\n**2. Respect Others**\n• Be friendly and sportsmanlike.\n\n**3. Responsible Gambling**\n• Never gamble real money.\n\n**4. Account Security**\n• Keep your account safe.\n\n**5. Violations**\n• Admins have final say.", color=0x3b82f6)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command()
async def rules(ctx):
    embed = discord.Embed(title="🏛️ Information Desk & Rules Guide", description="Welcome! Click below to view game rules or community guidelines.", color=0xd4af37)
    await ctx.send(embed=embed, view=RulesActionButtons())

@bot.command()
async def flag(ctx, member: discord.Member = None, *, reason: str = None):
    if not ctx.author.id in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    
    if member is None or reason is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You forgot to specify a user or a reason for the flag.", color=0xFF0000)
        embed.add_field(name="Correct Format:", value="`!flag <@user/ID> <reason>`")
        await ctx.send(embed=embed)
        return

    user_id = member.id
    await ensure_user(user_id)
    
    if reason in USER_DATA[user_id]["flags"]:
        await ctx.send(f"**{member.name}** is already flagged for this exact reason.")
        return

    # Log to moderation history array
    USER_DATA[user_id]["moderation_history"].append({
        "who": f"{ctx.author.name} (ID: {ctx.author.id})",
        "what": "FLAG",
        "when": str(datetime.datetime.now(datetime.UTC)),
        "why": str(reason)
    })

    USER_DATA[user_id]["flags"].append(str(reason))
    await save_user_data()
    
    embed = discord.Embed(title="🚩 User Flagged", description=f"{member.mention} has been flagged.", color=0xFFFF00)
    embed.add_field(name="Reason", value=reason)
    await ctx.send(embed=embed)
    
    try:
        staff_member = await bot.fetch_user(DM_ID)
        dm_embed = discord.Embed(title="🚩 Flag Alert", color=0xFFFF00)
        dm_embed.add_field(name="Who", value=f"{member.name} (ID: {user_id})", inline=False)
        dm_embed.add_field(name="What", value="User was flagged", inline=False)
        dm_embed.add_field(name="When", value=f"<t:{int(ctx.message.created_at.timestamp())}:F>", inline=False)
        dm_embed.add_field(name="Where", value=ctx.channel.mention, inline=False)
        dm_embed.add_field(name="Why", value=reason, inline=False)
        await staff_member.send(embed=dm_embed)
    except:
        pass


# --- STRIKE COMMAND ---
@bot.command()
async def strike(ctx, member: discord.Member = None, *, reason: str = None):
    if not ctx.author.id in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    if member is None or reason is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You forgot to specify a user or a reason for the strike.", color=0xFF0000)
        embed.add_field(name="Correct Format:", value="`!strike <@user/ID> <reason>`")
        await ctx.send(embed=embed)
        return
    
    user_id = member.id
    await ensure_user(user_id)
    
    if USER_DATA[user_id]["trespassed"]:
        embed = discord.Embed(title="Already Trespassed", description=f"{member.mention} is already permanently trespassed from the casino.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    
    USER_DATA[user_id]["strikes"] += 1
    current_strikes = USER_DATA[user_id]["strikes"]
    
    if current_strikes >= 3:
        USER_DATA[user_id]["trespassed"] = True
        
        USER_DATA[user_id]["moderation_history"].append({
            "who": f"{ctx.author.name} (ID: {ctx.author.id})",
            "what": f"STRIKE {current_strikes} (AUTO-TRESPASS)",
            "when": str(datetime.datetime.now(datetime.UTC)),
            "why": str(reason)
        })
        
        await save_user_data() 
        
        embed = discord.Embed(title="🚨 TRES-PASSED 🚨", description=f"{member.mention} has accumulated {current_strikes} strikes and has been formally **Trespassed** from the casino.\n\n**Reason for final strike:** {reason}\n\nThey can no longer interact with any casino features.", color=0xff0000)
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(title="🚨 You've Been Trespassed", description=f"You have been **permanently trespassed** from the gambling casino after receiving {current_strikes} strikes.\n\n**Final Reason:** {reason}\n\nYou can no longer use any casino commands or play any games.", color=0xff0000)
            await member.send(embed=dm_embed)
        except:
            pass
        
        await log_moderation_action("TRESPASS", user_id, f"**Reason:** {reason}\n**Strikes:** {current_strikes}/3\n**Admin:** {ctx.author.mention}")
    else:
        USER_DATA[user_id]["moderation_history"].append({
            "who": f"{ctx.author.name} (ID: {ctx.author.id})",
            "what": f"STRIKE {current_strikes}",
            "when": str(datetime.datetime.now(datetime.UTC)),
            "why": str(reason)
        })
        
        await save_user_data() 
        
        embed = discord.Embed(title="Strike Issued", description=f"{member.mention} has been given a strike.\n\n**Reason:** {reason}\n**Current Strikes:** {current_strikes}/3", color=0xffa500)
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(title="⚠️ You've Received a Strike", description=f"You have received a **strike** in the casino.\n\n**Reason:** {reason}\n**Current Strikes:** {current_strikes}/3\n\n⚠️ At 3 strikes, you will be permanently trespassed!", color=0xffa500)
            await member.send(embed=dm_embed)
        except:
            pass
        
        await log_moderation_action("STRIKE", user_id, f"**Reason:** {reason}\n**Strikes:** {current_strikes}/3\n**Admin:** {ctx.author.mention}")

@bot.command()
async def untrespass(ctx, member: discord.Member = None):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    if member is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You must mention a user to remove a strike from.", color=0xFF0000)
        embed.add_field(name="Correct Format:", value="`!untrespass <@user/ID>`")
        await ctx.send(embed=embed)
        return
    
    user_id = member.id
    await ensure_user(user_id)
    
    was_trespassed = USER_DATA[user_id]["trespassed"]
    USER_DATA[user_id]["strikes"] = 0
    USER_DATA[user_id]["trespassed"] = False
    
    # Save the updated status to the file
    await save_user_data()
    
    embed = discord.Embed(title="Trespass Lifted", description=f"{member.mention} has been pardoned. Their strikes have been reset to 0 and they may play in the casino again.", color=0x00ff00)
    await ctx.send(embed=embed)
    
    # DM the user
    try:
        dm_embed = discord.Embed(title="✅ Trespass Lifted", description=f"Your strikes have been cleared and you have been **unbanned** from the casino. You can now play games again!", color=0x00ff00)
        await member.send(embed=dm_embed)
    except:
        pass
    
    # Log moderation action
    await log_moderation_action("UNTRESPASS", user_id, f"**Previous Status:** {'Trespassed' if was_trespassed else 'Warned'}\n**Admin:** {ctx.author.mention}")

@bot.command()
async def events(ctx):
    embed = discord.Embed(title="📅 Event Overview", color=0x8b5cf6)
    
    possible_info = ""
    for eid, cfg in EVENTS_CONFIG.items():
        possible_info += f"**{cfg['name']}** - {cfg['description']}\n"
    embed.add_field(name="Possible Events", value=possible_info, inline=False)
    
    active_info = ""
    current_time = time.time()
    
    if ACTIVE_EVENT_STATES["race"]["end_time"] > current_time:
        remaining = int(ACTIVE_EVENT_STATES["race"]["end_time"] - current_time)
        active_info += f"🏁 **{EVENTS_CONFIG['race']['name']}** (Ends in {remaining}s)\n"
    
    if LOTTERY_POOL > 0:
        active_info += f"🎟️ **{EVENTS_CONFIG['lottery']['name']}** (Current Pot: ${LOTTERY_POOL:,})\n"
        
    if not active_info:
        active_info = "No events are currently running."
        
    embed.add_field(name="Currently Active", value=active_info, inline=False)
    await ctx.send(embed=embed)
@bot.command()
async def dbg_info(ctx):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**", ephemeral=True)
        return
    embed = discord.Embed(title="⚙️ Developer Diagnostic Panel", description="Checking systems logs...", color=0xffaa00)
    embed.add_field(name="Connection Speed Latency", value=f"{round(bot.latency * 1000)}ms")
    embed.add_field(name="Progression Tracking System", value=f"**Status:** {'ACTIVE' if GLOBAL_SETTINGS['xp_enabled'] else 'DISABLED'}")
    embed.add_field(name="Active Database Status", value=f"Tracking {len(USER_DATA)} active user wallets.")
    await ctx.send(embed=embed)

@bot.command()
async def dbg_reset_user(ctx, user: discord.Member):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    await ensure_user(user.id)
    USER_DATA[user.id] = {
        "balance": 5000, "total_games": 0, "wins": 0, "net_earnings": 0, "xp": 0, "rank_override": None, "strikes": 0, "trespassed": False,
        "settings": {"dm_notifications": True, "public_profile": True},
        "daily_cost": 1000, "vip_status": False, "scratch_history": 0, "crash_history": 0, 
        "last_command_timestamp": 0.0, "loan_debt": 0, 
        "upgrades": {"plinko_boost": 0, "slots_boost": 0, "xp_booster": 0, "vip_lounge": 0}
    }
    await save_user_data()
    await ctx.send(f"**Successfully wiped tracking history and reset wallet files for {user.name}.**")

class DbgTriggerView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        for event in EVENTS_CONFIG.keys():
            self.add_item(DbgButton(event))

class DbgButton(discord.ui.Button):
    def __init__(self, event):
        super().__init__(label=event.capitalize(), style=discord.ButtonStyle.primary, custom_id=event)
        self.event = event
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await run_event_logic(self.ctx, self.event, "no")
        await interaction.followup.send(f"✅ **Triggered {self.event}.**", ephemeral=True)

async def run_event_logic(ctx, event, silent):
    global LOTTERY_POOL, RACE_END_TIME, RACE_PARTICIPANTS
    target_channels = ["general", "chat", "public", "english"]
    async def broadcast_event(embed):
        if silent.lower() == "yes":
            await ctx.send(embed=embed)
        else:
            for guild in bot.guilds:
                for channel in guild.text_channels:
                    if channel.name.lower() in target_channels:
                        try:
                            await channel.send(embed=embed)
                            break
                        except:
                            continue
    if event == "race":
        RACE_END_TIME = time.time() + EVENTS_CONFIG["race"]["duration"]
        RACE_PARTICIPANTS = {}
        race_embed = discord.Embed(title=f"🏁 {EVENTS_CONFIG['race']['name']}", description=EVENTS_CONFIG['race']['description'], color=0x3b82f6)
        race_embed.add_field(name="Status", value="Event triggered by administrator.")
        await broadcast_event(race_embed)
    elif event == "lottery":
        if LOTTERY_POOL > 0:
            lottery_embed = discord.Embed(title=f"🎟️ {EVENTS_CONFIG['lottery']['name']}", description=f"The pot of **${LOTTERY_POOL:,}** goes to the system!", color=0xf59e0b)
            await broadcast_event(lottery_embed)
            LOTTERY_POOL = 0
    elif event == "interest":
        user_id = ctx.author.id
        await ensure_user(user_id)
        debt = USER_DATA[user_id].get("loan_debt", 0)
        if debt >= 5000:
            current_rate = USER_DATA[user_id].get("interest_rate", 1.0)
            USER_DATA[user_id]["loan_debt"] = int(debt * current_rate)
            USER_DATA[user_id]["interest_rate"] = current_rate + 0.1
            USER_DATA[user_id]["last_interest_time"] = time.time()
            await save_user_data()
            int_embed = discord.Embed(title=f"📈 {EVENTS_CONFIG['interest']['name']}", description=EVENTS_CONFIG['interest']['description'], color=0xef4444)
            int_embed.add_field(name="New Debt", value=f"${USER_DATA[user_id]['loan_debt']:,}")
            await broadcast_event(int_embed)
        else:
            await ctx.send("❌ **Debt too low for interest trigger.**")

@bot.command()
async def dbg_trigger(ctx, event: str = None, silent: str = "no"):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ **Access Denied.**")
    if not event:
        await ctx.send("⚙️ **Select an event to trigger:**", view=DbgTriggerView(ctx))
    elif event.lower() in EVENTS_CONFIG:
        await run_event_logic(ctx, event.lower(), silent)
    else:
        await ctx.send(f"❌ **Unknown event: `{event}`.**")@bot.command()
async def dbg_set_rank(ctx, user: discord.Member, rank_name: str):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    await ensure_user(user.id)
    clean_rank = rank_name.strip().capitalize()
    if clean_rank not in ["Beginner", "Intermediate", "Advanced", "None"]:
        await ctx.send("**Invalid rank choice. Pick Beginner, Intermediate, Advanced, or None.**")
        return
    USER_DATA[user.id]["rank_override"] = None if clean_rank == "None" else clean_rank
    await save_user_data()
    await ctx.send(f"⚙️ **Forced level rank profile property for {user.name} to: {clean_rank}**")

@bot.command()
async def dbg_set_xp(ctx, user: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    await ensure_user(user.id)
    USER_DATA[user.id]["xp"] = max(0, amount)
    await save_user_data()
    await ctx.send(f"⚙️ **Updated {user.name}'s experience pool directly to {USER_DATA[user.id]['xp']} XP.**")

@bot.command()
async def dbg_toggle_xp(ctx):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
    current = GLOBAL_SETTINGS["xp_enabled"]
    GLOBAL_SETTINGS["xp_enabled"] = not current
    status_text = "ENABLED" if not current else "DISABLED"
    await ctx.send(f"⚙️ **Global match experience point gathering systems are now {status_text}!**")

@bot.command()
async def isworking(ctx):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**", ephemeral=True)
        return
    img = Image.new("RGB", (1400, 300), "#111827")
    draw = ImageDraw.Draw(img)
    draw.text((60, 120), "Image Rendering Stats:", fill="#ffffff", font=font_large)
    draw.rectangle([(840, 100), (980, 200)], fill="#10b981", outline="#ffffff", width=4)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    file = discord.File(buffer, filename="status.png")
    embed = discord.Embed(title="🖼️ Canvas Diagnostics Output Check", color=0x10b981)
    embed.set_image(url="attachment://status.png")
    await ctx.send(file=file, embed=embed)

@bot.command()
async def plinko(ctx, bet: str = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if USER_DATA[user_id].get("trespassed", False):
        embed = discord.Embed(title="❌ Trespassed", description="You are **Trespassed** from this establishment. Security will not allow you to play.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    # Cooldown Check
    current_time = time.time()
    last_played = USER_DATA[user_id].get("last_command_timestamp", 0.0)
    if current_time - last_played < 3.0:
        remaining = 3.0 - (current_time - last_played)
        await ctx.send(f"⏳ Please wait **{remaining:.1f}** seconds before dropping another ball.")
        return

    if bet is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You must specify your bet amount.", color=0xff0000)
        embed.add_field(name="Correct Usage", value="`!plinko <bet_amount>`\n`!plinko <percentage>%`\n`!plinko all`", inline=False)
        await ctx.send(embed=embed)
        return

    author_balance = USER_DATA[user_id]["balance"]
    bet_clean = bet.lower().strip()

    if bet_clean == "all":
        bet_amount = author_balance
    elif bet_clean.endswith("%"):
        try:
            percentage = float(bet_clean[:-1])
            if percentage <= 0 or percentage > 100:
                embed = discord.Embed(title="❌ Invalid Percentage", description="Percentage must be between 1% and 100%!", color=0xff0000)
                await ctx.send(embed=embed)
                return
            bet_amount = int(author_balance * (percentage / 100))
        except ValueError:
            embed = discord.Embed(title="❌ Invalid Percentage Format", description="Please enter a valid percentage format (e.g., 25%).", color=0xff0000)
            await ctx.send(embed=embed)
            return
    else:
        try:
            bet_amount = int(bet_clean)
        except ValueError:
            embed = discord.Embed(title="❌ Invalid Bet Amount", description="Please enter a valid whole number, a percentage (e.g., 25%), or type `all`.", color=0xff0000)
            await ctx.send(embed=embed)
            return

    if bet_amount <= 0:
        embed = discord.Embed(title="❌ Invalid Bet Amount", description="Your bet must be greater than 0 chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    if USER_DATA[user_id]["balance"] < bet_amount:
        embed = discord.Embed(title="❌ Insufficient Funds", description=f"You do not have enough chips. Current Balance: **{USER_DATA[user_id]['balance']}** chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    # Commit Cooldown Timestamp
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await save_user_data()

    USER_DATA[user_id]["total_games"] += 1
    
    # Apply XP upgrade multiplier logic if present
    if "upgrades" not in USER_DATA[user_id]:
        USER_DATA[user_id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "xp_booster": 0}
    xp_level = USER_DATA[user_id]["upgrades"].get("xp_booster", 0)
    xp_to_add = int(1 * (1 + (xp_level * 0.25)))
    await add_xp(user_id, xp_to_add)
    await save_user_data()

    width, height = 360, 400
    rows = 8
    start_x, start_y = width // 2, 30
    row_spacing = 35
    peg_radius = 3
    ball_radius = 5

    base_multipliers = [5.0, 2.0, 0.5, 0.2, 0.0, 0.2, 0.5, 2.0, 5.0]
    
    # Calculate shop bonus additions
    plinko_level = USER_DATA[user_id]["upgrades"].get("plinko_boost", 0)
    bonus_multiplier = plinko_level * 0.1
    
    multipliers = [round(m + bonus_multiplier, 1) for m in base_multipliers]
    
    bucket_colors = [
        (220, 20, 60), (255, 140, 0), (255, 215, 0), (50, 205, 50), (128, 128, 128),
        (50, 205, 50), (255, 215, 0), (255, 140, 0), (220, 20, 60)
    ]
    bucket_w = width / len(multipliers)

    pegs = []
    for r in range(rows):
        y = start_y + (r * row_spacing) + 30
        count = r + 3
        row_w = (count - 1) * 26
        x_left = (width - row_w) // 2
        for i in range(count):
            pegs.append((x_left + (i * 26), y))

    GRAVITY = 0.35
    BOUNCE = 0.50
    MAX_VEL = 8

    px, py = start_x, start_y
    vx, vy = random.uniform(-1.0, 1.0), 0.0
    raw_path = [(px, py)]

    sim_frames = 0
    while py < height - 35 and sim_frames < 240:
        vy += GRAVITY
        vx = max(-MAX_VEL, min(vx, MAX_VEL))
        vy = max(-MAX_VEL, min(vy, MAX_VEL))
        px += vx
        py += vy
        
        if px - ball_radius < 5:
            px = 5 + ball_radius
            vx = -vx * BOUNCE
        elif px + ball_radius > width - 5:
            px = width - 5 - ball_radius
            vx = -vx * BOUNCE

        for peg_x, peg_y in pegs:
            dx = px - peg_x
            dy = py - peg_y
            distance = math.sqrt(dx*dx + dy*dy)
            min_dist = ball_radius + peg_radius
            
            if distance < min_dist:
                overlap = min_dist - distance
                nx = dx / distance if distance > 0 else 0
                ny = dy / distance if distance > 0 else -1
                px += nx * overlap
                py += ny * overlap
                dot_product = vx * nx + vy * ny
                vx = (vx - 2 * dot_product * nx) * BOUNCE
                vy = (vy - 2 * dot_product * ny) * BOUNCE
                vx += random.uniform(-0.6, 0.6)
                break
                
        raw_path.append((px, py))
        sim_frames += 1

    final_bucket_idx = int(px // bucket_w)
    final_bucket_idx = max(0, min(final_bucket_idx, len(multipliers) - 1))
    payout_multiplier = multipliers[final_bucket_idx]

    optimized_path = raw_path[::2]
    if raw_path[-1] not in optimized_path:
        optimized_path.append(raw_path[-1])

    frames = []
    for step in range(len(optimized_path)):
        frame = Image.new("RGB", (width, height), color=(20, 24, 30))
        draw = ImageDraw.Draw(frame)
        font = ImageFont.load_default()

        for b_idx, mult in enumerate(multipliers):
            bx1 = b_idx * bucket_w
            bx2 = bx1 + bucket_w
            by1 = height - 35
            by2 = height - 5
            draw.rectangle([bx1 + 2, by1, bx2 - 2, by2], fill=bucket_colors[b_idx], outline=(255, 255, 255), width=1)
            draw.text(((bx1 + bx2) / 2, (by1 + by2) / 2), f"{mult}x", fill=(255, 255, 255), font=font, anchor="mm")

        for px, py in pegs:
            draw.ellipse([px - peg_radius, py - peg_radius, px + peg_radius, py + peg_radius], fill=(240, 240, 240))

        bx, by = optimized_path[step]
        draw.ellipse([bx - ball_radius, by - ball_radius, bx + ball_radius, by + ball_radius], fill=(255, 50, 50), outline=(255, 255, 255), width=1)
        frames.append(frame)

    final_frame = frames[-1]
    for _ in range(15):
        frames.append(final_frame)

    processed_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE) for f in frames]

    final_buffer = io.BytesIO()
    processed_frames[0].save(
        final_buffer, 
        format="GIF", 
        save_all=True, 
        append_images=processed_frames[1:], 
        duration=40,
        optimize=True
    )
    final_buffer.seek(0)
    file = discord.File(fp=final_buffer, filename="plinko.gif")

    cost_deduction = bet_amount
    winnings = int(bet_amount * payout_multiplier)
    USER_DATA[user_id]["balance"] = (USER_DATA[user_id]["balance"] - cost_deduction) + winnings
    USER_DATA[user_id]["net_earnings"] += (winnings - cost_deduction)
    await save_user_data()

    if winnings > cost_deduction:
        result_color = 0x00ff00
        statement = f"📈 **Profit!** 📈\n\nYour ball landed in the **{payout_multiplier}x** bucket!\nReturned: **${winnings:,}** chips."
    elif winnings == cost_deduction:
        result_color = 0xffff00
        statement = f"⚖️ **Broke Even!** ⚖️\n\nYour ball landed in the **{payout_multiplier}x** bucket.\nReturned: **${winnings:,}** chips."
    else:
        result_color = 0xff0000
        statement = f"📉 **Loss!** 📉\n\nYour ball landed in the **{payout_multiplier}x** bucket.\nReturned: **${winnings:,}** chips (Lost **-${cost_deduction - winnings:,}**)."

    embed = discord.Embed(title="🔴 Plinko Drop Results 🔴", color=result_color)
    embed.add_field(name="💰 Wager Summary", value=f"Dropped **{bet_amount:,}** chips down the peg board.", inline=False)
    embed.add_field(name="📊 Outcome", value=statement, inline=False)
    embed.add_field(name="💵 Updated Balance", value=f"**{USER_DATA[user_id]['balance']:,}** chips", inline=False)
    embed.add_field(name="🔧 Context Info", value=f"Author: {ctx.author.mention} | Channel ID: {ctx.channel.id}", inline=False)
    embed.set_image(url="attachment://plinko.gif")
    await ctx.send(file=file, embed=embed)

class HelpPaginator(discord.ui.View):
    def __init__(self, commands_list, author_id, bot_ref, page_size=15):
        super().__init__(timeout=120)
        self.commands_list = commands_list
        self.author_id = author_id
        self.bot_ref = bot_ref
        self.page_size = page_size
        self.total_pages = max(1, (len(commands_list) + page_size - 1) // page_size)
        self.current_page = 1
        self.message = None
        self.update_button_states()

    def update_button_states(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "help_previous":
                    child.disabled = self.current_page <= 1
                elif child.custom_id == "help_next":
                    child.disabled = self.current_page >= self.total_pages

    def get_page_embed(self):
        start_index = (self.current_page - 1) * self.page_size
        page_commands = self.commands_list[start_index:start_index + self.page_size]
        command_lines = "\n".join(f"``{command}``" for command in page_commands) or "No commands available :("
        embed = discord.Embed(
            title="Available Commands",
            description=f"{command_lines}\n\nRun `!cmds [command]` for more info on a specific command.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can use these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="help_previous")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(1, self.current_page - 1)
        self.update_button_states()
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple, custom_id="help_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages, self.current_page + 1)
        self.update_button_states()
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class CommandHelpView(discord.ui.View):
    def __init__(self, commands_list, bot_ref):
        super().__init__(timeout=120)
        self.commands_list = commands_list
        self.bot_ref = bot_ref
        self.add_command_buttons()

    def add_command_buttons(self):
        for command_name in self.commands_list:
            button = discord.ui.Button(
                label=command_name,
                style=discord.ButtonStyle.secondary,
                custom_id=f"cmd_help_{command_name}"
            )
            button.callback = self.command_button_callback
            self.add_item(button)

    async def command_button_callback(self, interaction: discord.Interaction):
        command_name = interaction.data["custom_id"].replace("cmd_help_", "")
        command = self.bot_ref.get_command(command_name)
        
        if not command:
            await interaction.response.send_message(f"Command '{command_name}' not found.", ephemeral=True)
            return
        
        help_text = command.help or "No help information currently available for this command :("
        
        embed = discord.Embed(
            title=f"Help: {command_name}",
            description=help_text,
            color=discord.Color.green()
        )
        
        if command.usage:
            embed.add_field(name="Usage", value=f"!{command.name} {command.usage}", inline=False)
        else:
            embed.add_field(name="Usage", value=f"!{command.name}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class HelpDropdown(discord.ui.Select):
    def __init__(self, bot_ref):
        self.bot_ref = bot_ref
        options = [
            discord.SelectOption(label="Auction House", description="Marketplace, selling, bidding, and admin overrides.", emoji="🏛️"),
            discord.SelectOption(label="Gambling", description="Risk-based games, daily allowances, and statistics.", emoji="🎲"),
            discord.SelectOption(label="Commands", description="General system tools, settings, and standard profile profiles.", emoji="📜")
        ]
        super().__init__(placeholder="Select a command category...", min_values=1, max_values=1, options=options, custom_id="help_menu_dropdown")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.author_id:
            await interaction.response.send_message("Only the command author can interact with this menu.", ephemeral=True)
            return

        selected = self.values[0]
        
        if selected == "Auction House":
            commands_list = sorted([
                command.name for command in self.bot_ref.commands
                if command.name == "ah" or (command.parent and command.parent.name == "ah")
            ])
            if not commands_list:
                commands_list = ["ah", "ah sell", "ah buy", "ah bid", "ah cancel", "ah blacklist", "ah unblacklist"]
                
            view = HelpPaginator(commands_list, self.view.author_id, self.bot_ref, page_size=15)
            embed = view.get_page_embed()
            embed.title = "🏛️ Auction House Commands"
            await interaction.response.edit_message(embed=embed, view=view)
            view.message = self.view.message

        elif selected == "Gambling":
            gambling_suite = {"slots", "plinko", "roulette", "bj", "crash", "scratch", "daily", "coinflip", "diceduel", "keno", "race", "mines", "highlow", "dice"}
            commands_list = sorted([
                command.name for command in self.bot_ref.commands
                if command.name in gambling_suite and not command.hidden
            ])
            
            view = HelpPaginator(commands_list, self.view.author_id, self.bot_ref, page_size=15)
            embed = view.get_page_embed()
            embed.title = "🎲 Gambling Commands"
            await interaction.response.edit_message(embed=embed, view=view)
            view.message = self.view.message

        elif selected == "Commands":
            excluded_commands = {"strike", "untrespass", "dbg_reset_daily", "dbg_money", "dbg_reset_user", "dbg_set_rank", "dbg_give", "accept_tos", "dbg_set_xp", "dbg_toggle_xp", "isworking", "cups", "dbg_info", "dbg_reset_updates", "dbg_set_vip", "animate", "help", "rig_roulette"}
            gambling_suite = {"slots", "plinko", "roulette", "bj", "crash", "scratch", "daily", "coinflip", "diceduel", "keno", "race", "mines", "highlow", "dice"}
            
            commands_list = sorted([
                command.name for command in self.bot_ref.commands
                if not command.hidden 
                and command.name not in excluded_commands 
                and command.name not in gambling_suite
                and not (command.parent and command.parent.name == "ah")
                and command.name != "ah"
                and command.name != "cmds"
            ])
            
            view = HelpPaginator(commands_list, self.view.author_id, self.bot_ref, page_size=15)
            embed = view.get_page_embed()
            embed.title = "📜 Regular Commands"
            await interaction.response.edit_message(embed=embed, view=view)
            view.message = self.view.message


class HelpCategorySelectionView(discord.ui.View):
    def __init__(self, author_id, bot_ref):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.bot_ref = bot_ref
        self.message = None
        self.add_item(HelpDropdown(self.bot_ref))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can interact with this menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


@bot.command(name="cmds")
async def cmds(ctx, command_name: str = None):
    if command_name:
        command = bot.get_command(command_name)
        if not command:
            await ctx.send(f"No command named `{command_name}` found.")
            return

        usage = str(command.signature)
        usage_text = f"!{command.name} {usage}".strip()
        description_text = command.help or "No description available :("

        help_embed = discord.Embed(
            title=f"Command: {command.name}",
            color=discord.Color.purple()
        )
        help_embed.add_field(name="Usage", value=f"``{usage_text}``", inline=False)
        help_embed.add_field(name="Description", value=f"``{description_text}``", inline=False)

        await ctx.send(embed=help_embed)
        return

    embed = discord.Embed(
        title="📚 Help Menu Selection",
        description="Please select a category from the dropdown menu below to view its available commands:\n\n"
                    "🏛️ **Auction House** — Buying, selling, bidding, and marketplace options.\n"
                    "🎲 **Gambling** — Risk-based games, daily bonuses, and table systems.\n"
                    "📜 **Commands** — Profile views, general system tools, and secondary commands.",
        color=discord.Color.purple()
    )
    
    view = HelpCategorySelectionView(ctx.author.id, bot)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@bot.command()
async def coinflip(ctx, amount: str, side: str):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 5:
        remaining = int(5 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before flipping again.")
    
    side = side.lower()
    if side not in ["heads", "tails"]:
        await ctx.send("❌ Please choose **heads** or **tails**.")
        return
        
    if amount.lower() == "max":
        amount = USER_DATA[user_id]["balance"]
    else:
        try:
            amount = int(amount)
        except ValueError:
            await ctx.send("❌ Please enter a valid number or `max`.")
            return

    if amount <= 0:
        await ctx.send("❌ You must bet at least 1 chip.")
        return
        
    if USER_DATA[user_id]["balance"] < amount:
        await ctx.send("❌ You don't have enough chips in your wallet.")
        return

    USER_DATA[user_id]["balance"] -= amount
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    
    result = random.choice(["heads", "tails"])
    
    if side == result:
        winnings = amount * 2
        await apply_gambling_winnings(user_id, winnings)
        embed = discord.Embed(
            title="🪙 Coinflip Result: WIN",
            description=f"It was **{result.upper()}**! You doubled your bet and won **${winnings:,}**.",
            color=0x22c55e
        )
    else:
        global LOTTERY_POOL
        LOTTERY_POOL += amount
        embed = discord.Embed(
            title="🪙 Coinflip Result: LOSS",
            description=f"It was **{result.upper()}**. You lost your bet of **${amount:,}**.",
            color=0xef4444
        )
    
    await save_user_data()
    await ctx.send(embed=embed)

@bot.command()
async def diceduel(ctx, amount: int):
    global LOTTERY_POOL
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 5:
        remaining = int(5 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before dueling again.")
        
    if USER_DATA[user_id]["balance"] < amount: return await ctx.send("❌ Insufficient funds.")
    
    USER_DATA[user_id]["balance"] -= amount
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    
    player_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)
    
    if player_roll > bot_roll:
        winnings = amount * 2
        await apply_gambling_winnings(user_id, winnings)
        await ctx.send(f"🎲 You rolled {player_roll}, Bot rolled {bot_roll}. You won **${winnings:,}**!")
    elif player_roll < bot_roll:
        LOTTERY_POOL += amount
        await ctx.send(f"🎲 You rolled {player_roll}, Bot rolled {bot_roll}. You lost **${amount:,}**.")
    else:
        USER_DATA[user_id]["balance"] += amount
        await ctx.send(f"🎲 You rolled {player_roll}, Bot rolled {bot_roll}. It's a tie, bet refunded.")
    await save_user_data()

def generate_mines_image(revealed_indices, mines_locations, game_over):
    img = Image.new('RGB', (500, 500), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    for i in range(25):
        row, col = divmod(i, 5)
        x, y = col * 100, row * 100
        color = (60, 60, 60)
        if game_over and i in mines_locations:
            color = (200, 50, 50)
        elif i in revealed_indices:
            color = (50, 200, 50)
        draw.rectangle([x + 5, y + 5, x + 95, y + 95], fill=color, outline=(100, 100, 100))
    return img

class MinesModal(discord.ui.Modal, title='Dig a Square'):
    index_input = discord.ui.TextInput(label='Square Index (0-24)', placeholder='0-24 (Left to Right, Top to Bottom)', min_length=1, max_length=2)

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            index = int(self.index_input.value)
        except ValueError:
            return await interaction.response.send_message("Invalid number.", ephemeral=True)
        
        if not (0 <= index <= 24) or index in self.view.revealed:
            return await interaction.response.send_message("Invalid or already revealed tile.", ephemeral=True)

        if index in self.view.mines_locations:
            self.view.game_over = True
            USER_DATA[self.view.user_id]["total_games"] += 1
            await save_user_data()
            img = generate_mines_image(self.view.revealed, self.view.mines_locations, True)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            await interaction.response.edit_message(content=f"💥 BOOM! You lost **${self.view.bet:,}**.", attachments=[discord.File(buffer, filename="mines.png")], view=None)
        else:
            self.view.revealed.append(index)
            self.view.multiplier += 0.2 + (self.view.mines_count * 0.05)
            img = generate_mines_image(self.view.revealed, self.view.mines_locations, False)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            await interaction.response.edit_message(embed=discord.Embed(title="💣 Mines", description=f"Multiplier: **{self.view.multiplier:.2f}x**"), attachments=[discord.File(buffer, filename="mines.png")], view=self.view)

class MinesView(discord.ui.View):
    def __init__(self, user_id, bet, mines_count, mines_locations):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bet = bet
        self.mines_count = mines_count
        self.multiplier = 1.0
        self.revealed = []
        self.mines_locations = mines_locations
        self.game_over = False

    @discord.ui.button(label="Dig", style=discord.ButtonStyle.primary)
    async def dig_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MinesModal(self))

    @discord.ui.button(label="Cashout", style=discord.ButtonStyle.green)
    async def cashout(self, interaction: discord.Interaction, button: discord.ui.Button):
        winnings = int(self.bet * self.multiplier)
        USER_DATA[self.user_id]["balance"] += winnings
        USER_DATA[self.user_id]["wins"] += 1
        USER_DATA[self.user_id]["total_games"] += 1
        USER_DATA[self.user_id]["net_earnings"] += (winnings - self.bet)
        await save_user_data()
        self.game_over = True
        await interaction.response.edit_message(content=f"💰 Cashed out **${winnings:,}**!", view=None)

@bot.command()
async def mines(ctx, bet: int, mine_count: int):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    current_time = time.time()
    last_use = USER_DATA[user_id].get("last_command_timestamp", 0)
    if current_time - last_use < 30:
        remaining = int(30 - (current_time - last_use))
        return await ctx.send(f"❌ Please wait {remaining}s before starting a new game.")
    
    if not (1 <= mine_count <= 24): return await ctx.send("❌ Choose 1-24 mines.")
    if USER_DATA[user_id]["balance"] < bet: return await ctx.send("❌ Insufficient funds.")
    
    USER_DATA[user_id]["balance"] -= bet
    USER_DATA[user_id]["last_command_timestamp"] = current_time
    await save_user_data()
    
    view = MinesView(user_id, bet, mine_count, random.sample(range(25), mine_count))
    img = generate_mines_image([], view.mines_locations, False)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    await ctx.send(embed=discord.Embed(title="💣 Mines", description=f"Bet: **${bet:,}**"), file=discord.File(buffer, filename="mines.png"), view=view)

@bot.command()
async def dbg_reset_updates(ctx):
    if ctx.author.id not in ADMIN_IDS:
        return
        
    old_ver = LATEST_UPDATE["version"]
    version_parts = old_ver.replace("v", "").split(".")
    new_minor = int(version_parts[1]) + 1
    new_ver = f"v1.{new_minor}.0"
    
    LATEST_UPDATE["version"] = new_ver
    
    try:
        await ctx.author.send(f"🔔 Global update reset triggered. Version: {new_ver} sent to all users.")
    except discord.Forbidden:
        await ctx.send("❌ Could not DM you.")
    
    count = 0
    for user_id in USER_DATA:
        try:
            user = await bot.fetch_user(user_id)
            embed = discord.Embed(
                title="📢 New Bot Update Available!",
                description=f"A new update has been released: **{new_ver}**.\nPlease run `!update` to acknowledge the changes.\nOr `!fullupdate` for the full update log",
                color=0xf59e0b
            )
            await user.send(embed=embed)
            count += 1
        except (discord.Forbidden, discord.HTTPException):
            continue
            
    guild = bot.get_guild(1520275208592687275)
    if guild:
        channel = guild.get_channel(1520297389401833563)
        if channel:
            log = UPDATE_LOGS.get(new_ver, "No detailed log available for this version.")
            embed_full = discord.Embed(
                title=f"📜 Full Update Log - {new_ver}",
                description=log,
                color=0x3b82f6
            )
            embed_full.set_footer(text=f"Released on {LATEST_UPDATE['date']} at {LATEST_UPDATE['time']}")
            msg = await channel.send(embed=embed_full)
            await msg.add_reaction("✅")
            
    await ctx.send(f"✅ Reset triggered. Update notification sent to {count} users and published to announcement channel.")

@bot.event
async def on_command_completion(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    if ctx.command.name in ["update", "updates"]:
        return
        
    last_ver = USER_DATA[user_id].get("last_update_version", "0.0.0")
    if last_ver != LATEST_UPDATE["version"]:
        embed = discord.Embed(
            title="📢 New Bot Update Available!",
            description=f"You haven't acknowledged the latest update yet! Please run `!update` to continue.\n\n**Latest Version:** {LATEST_UPDATE['version']}\n**Date:** {LATEST_UPDATE['date']} at {LATEST_UPDATE['time']}\n\n**Notes:**\n{LATEST_UPDATE['notes']}",
            color=0xf59e0b
        )
        await ctx.send(embed=embed)

@bot.command()
async def update(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    USER_DATA[user_id]["last_update_version"] = LATEST_UPDATE["version"]
    await save_user_data()
    
    update_details = (
        f"**Version:** {LATEST_UPDATE['version']}\n"
        f"**Date:** {LATEST_UPDATE['date']}\n"
        f"**Time:** {LATEST_UPDATE['time']}\n"
        f"**Summary:** {LATEST_UPDATE['summary']}\n"
        f"**Full update:** Use **`!fullupdate`** to see the complete changelog."
    )
    
    embed = discord.Embed(
        title="📢 Latest Update Details",
        description=update_details,
        color=0x10b981
    )
    embed.set_footer(text=f"Version {LATEST_UPDATE['version']} acknowledged successfully.")
    await ctx.send(embed=embed)

class UpdateLogPaginator(discord.ui.View):
    def __init__(self, pages, version, date, time):
        super().__init__(timeout=60)
        self.pages = pages
        self.version = version
        self.date = date
        self.time = time
        self.current_page = 0

    def create_embed(self):
        embed = discord.Embed(
            title=f"📜 Full Update Log - {self.version}",
            description=self.pages[self.current_page],
            color=0x3b82f6
        )
        embed.set_footer(text=f"Released on {self.date} at {self.time} | Page {self.current_page + 1}/{len(self.pages)}")
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            
        self.next_button.disabled = False
        if self.current_page == 0:
            button.disabled = True
            
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            
        self.previous_button.disabled = False
        if self.current_page == len(self.pages) - 1:
            button.disabled = True
            
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

@bot.command()
async def fullupdate(ctx):
    version = LATEST_UPDATE["version"]
    log = UPDATE_LOGS.get(version, "No detailed log available for this version.")
    
    raw_sections = log.split("\n\n")
    pages = []
    current_page_text = ""
    
    for section in raw_sections:
        if len(current_page_text) + len(section) + 2 > 1500:
            if current_page_text:
                pages.append(current_page_text.strip())
            current_page_text = section + "\n\n"
        else:
            current_page_text += section + "\n\n"
            
    if current_page_text:
        pages.append(current_page_text.strip())
    
    if len(pages) <= 1:
        embed = discord.Embed(
            title=f"📜 Full Update Log - {version}",
            description=log,
            color=0x3b82f6
        )
        embed.set_footer(text=f"Released on {LATEST_UPDATE['date']} at {LATEST_UPDATE['time']}")
        await ctx.send(embed=embed)
    else:
        view = UpdateLogPaginator(pages, version, LATEST_UPDATE['date'], LATEST_UPDATE['time'])
        embed = view.create_embed()
        await ctx.send(embed=embed, view=view)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
        
    if payload.channel_id != 1520297389401833563:
        return
        
    if str(payload.emoji) != "✅":
        return
        
    try:
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
    except (discord.NotFound, discord.HTTPException):
        return
        
    if message.author.id == bot.user.id and len(message.embeds) > 0:
        if "Full Update Log" in str(message.embeds[0].title):
            user_id = payload.user_id
            await ensure_user(user_id)
            USER_DATA[user_id]["last_update_version"] = LATEST_UPDATE["version"]
            await save_user_data()

@bot.event
async def on_command_pre_invoke(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    # Skip TOS check for the accept_tos command
    if ctx.command.name == "accept_tos":
        return
        
    if not USER_DATA[user_id].get("tos_accepted", False):
        # Stop the command execution
        embed = discord.Embed(
            title="⚖️ Terms of Service Agreement",
            description=(
                "**Before using this bot, you must agree to the following:**\n\n"
                "1. You are fully responsible for your actions and use of this bot.\n"
                "2. The casino owner is not responsible for any lost virtual currency or account issues.\n"
                "3. You agree to abide by all platform rules.\n\n"
                "Please run `!accept_tos` to accept these terms and begin playing."
            ),
            color=0xffd700
        )
        await ctx.send(embed=embed)
        # Raise an error to prevent the actual command from running
        raise discord.ext.commands.CheckFailure("TOS not accepted.")

@bot.command()
async def accept_tos(ctx):
    user_id = ctx.author.id
    await ensure_user(user_id)
    
    USER_DATA[user_id]["tos_accepted"] = True
    await save_user_data()
    
    embed = discord.Embed(
        title="✅ TOS Accepted",
        description="You have agreed to the Terms of Service. You may now use the bot's features.",
        color=0x10b981
    )
    await ctx.send(embed=embed)

@bot.command()
async def countcmds(ctx):
    total_cmds = len(bot.commands)
    embed = discord.Embed(title="Total commands", description=f"This bot has a total of **{total_cmds}** commands", color=discord.Color.dark_blue())
    await ctx.send(embed=embed)

@bot.command(name="feedback")
async def feedback(ctx, *, content: str):
    if not PUBLIC_ACCESS:
        return
    
    try:
        target_user = await bot.fetch_user(DM_ID)
        
        embed = discord.Embed(
            title="New Bot Feedback Received",
            description=content,
            color=discord.Color.blue()
        )
        embed.set_author(name=f"{ctx.author.name} ({ctx.author.id})", icon_url=ctx.author.display_avatar.url)
        
        await target_user.send(embed=embed)
        await ctx.send("✅ Thank you! Your feedback has been sent directly to the developer.")
    except discord.Forbidden:
        await ctx.send("❌ I couldn't send the feedback because my DMs with the developer are closed or blocked.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred while sending feedback: {e}")

@bot.command(name="survey")
async def survey(ctx):
    if not PUBLIC_ACCESS:
        return

    try:
        await ctx.author.send("👋 Welcome to the Bot Feedback Survey! I will ask you 15 questions one by one. Please reply directly to this DM.")
        await ctx.send("📥 Check your DMs! I've sent you the first question.")
    except discord.Forbidden:
        await ctx.send("❌ I cannot send you DMs. Please open your privacy settings for this server and try again.")
        return

    answers = []
    
    def dm_check(m):
        return m.author.id == ctx.author.id and m.guild is None

    # Phase 1: Gathering Responses 1 by 1
    for index, question in enumerate(SURVEY_QUESTIONS, start=1):
        embed = discord.Embed(
            title=f"Survey Question {index} of 15",
            description=question,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Type your response and press enter.")
        
        await ctx.author.send(embed=embed)
        
        try:
            response = await bot.wait_for("message", check=dm_check, timeout=300.0)
            answers.append(str(response.content))
        except asyncio.TimeoutError:
            await ctx.author.send("⏱️ Survey timed out due to inactivity. Please run `!survey` again in the server if you wish to restart.")
            return

    # Phase 2: Review and Modification Loop
    while True:
        overview_embed = discord.Embed(
            title="📋 Survey Review Overview",
            description="Review your answers below. If you want to change one, type the number of that question (1-15). If everything looks perfect, type **done**.",
            color=discord.Color.green()
        )
        
        for i, (q, a) in enumerate(zip(SURVEY_QUESTIONS, answers), start=1):
            cleaned_string_answer = str(a)
            truncated_answer = cleaned_string_answer[:100] + "..." if len(cleaned_string_answer) > 100 else cleaned_string_answer
            overview_embed.add_field(name=f"{i}. {q[:60]}...", value=truncated_answer, inline=False)
            
        await ctx.author.send(embed=overview_embed)
        
        try:
            action = await bot.wait_for("message", check=dm_check, timeout=300.0)
            action_text = action.content.strip().lower()
            
            if action_text == "done":
                break
            
            if action_text.isdigit():
                num = int(action_text)
                if 1 <= num <= 15:
                    edit_embed = discord.Embed(
                        title=f"Editing Question {num}",
                        description=f"**Question:** {SURVEY_QUESTIONS[num-1]}\n\n**Current Answer:** {answers[num-1]}\n\n*Please type your new answer below:*",
                        color=discord.Color.orange()
                    )
                    await ctx.author.send(embed=edit_embed)
                    
                    new_response = await bot.wait_for("message", check=dm_check, timeout=300.0)
                    answers[num-1] = str(new_response.content)
                    await ctx.author.send(f"✅ Question {num} updated successfully!")
                else:
                    await ctx.author.send("❌ Invalid question number. Please provide a number between 1 and 15.")
            else:
                await ctx.author.send("❌ Invalid choice. Type a number (1-15) to edit, or **done** to submit.")
                
        except asyncio.TimeoutError:
            await ctx.author.send("⏱️ Review timed out. Your survey responses have been discarded.")
            return

    # Phase 3: Compiling and Sending Final Results to DM_ID
    try:
        dev_user = await bot.fetch_user(DM_ID)
        
        embed_part1 = discord.Embed(
            title=f"📊 Survey Submission from {ctx.author.name} (Part 1)",
            color=discord.Color.gold()
        )
        embed_part1.set_author(name=f"{ctx.author.name} ({ctx.author.id})", icon_url=ctx.author.display_avatar.url)
        
        for i in range(8):
            embed_part1.add_field(name=f"Q{i+1}: {SURVEY_QUESTIONS[i]}", value=answers[i], inline=False)
            
        embed_part2 = discord.Embed(
            title=f"📊 Survey Submission from {ctx.author.name} (Part 2)",
            color=discord.Color.gold()
        )
        
        for i in range(8, 15):
            embed_part2.add_field(name=f"Q{i+1}: {SURVEY_QUESTIONS[i]}", value=answers[i], inline=False)
            
        await dev_user.send(embed=embed_part1)
        await dev_user.send(embed=embed_part2)
        
        await ctx.author.send("✨ Your completed survey has been sent to the developer! Thank you for helping improve the bot.")
        
    except discord.Forbidden:
        await ctx.author.send("❌ The survey is complete, but I couldn't send the logs to the developer because their DMs are locked.")
    except Exception as e:
        await ctx.author.send(f"❌ Failed to transmit survey: {e}")

# =========================================================================
# 1. OPENCV DEMO: Cup & Ball Game (Lifting, Showing Ball, Smooth 3D Arc Shuffle)
# =========================================================================
@bot.command()
async def cvshow(ctx):
    """Generates a realistic 3-cup shuffle sequence using OpenCV matrix rendering."""
    await ctx.send("Generating Cup Game simulation...")

    def generate_cup_game():
        width, height = 600, 400
        frames = []
        
        # Initial positions for 3 cups [Cup 0, Cup 1, Cup 2]
        cup_xs = [150, 300, 450]
        cup_y_base = 250
        ball_x, ball_y = 300, 260 # Ball hidden under middle cup (Cup 1)

        def draw_scene(c_positions, lift_offset=0, show_ball=False):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (35, 45, 60) # Warm dark table background
            
            # Draw the hidden prize ball
            if show_ball:
                cv2.circle(frame, (ball_x, ball_y), 12, (50, 50, 220), -1) # Red Ball
                cv2.circle(frame, (ball_x, ball_y), 12, (100, 100, 255), 2) # Highlight

            # Draw the three cups
            for idx, x in enumerate(c_positions):
                y = cup_y_base
                if idx == 1: # Lift the middle cup at the start
                    y -= lift_offset
                
                # Draw a clean metallic copper cup structure
                pts = np.array([[x-35, y-70], [x+35, y-70], [x+25, y], [x-25, y]], np.int32)
                cv2.fillPoly(frame, [pts], (40, 90, 160)) # Copper base
                cv2.polylines(frame, [pts], True, (70, 140, 220), 2) # Polished rim
                cv2.circle(frame, (x, y-70), 35, (60, 110, 180), -1) # Cup top depth
            return frame

        # Phase A: Lift middle cup to reveal the ball (Frames 0-20)
        for f in range(20):
            lift = int(50 * math.sin((f / 20) * (math.pi / 2)))
            img = draw_scene(cup_xs, lift_offset=lift, show_ball=True)
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Phase B: Keep it paused in the air briefly (Frames 21-30)
        for _ in range(10):
            img = draw_scene(cup_xs, lift_offset=50, show_ball=True)
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Phase C: Lower the cup back over the ball (Frames 31-50)
        for f in range(20):
            lift = int(50 * math.cos((f / 20) * (math.pi / 2)))
            img = draw_scene(cup_xs, lift_offset=lift, show_ball=True)
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        # Phase D: Shuffle Cup 1 and Cup 2 in a circular arc path (Frames 51-80)
        start_x1, start_x2 = cup_xs[1], cup_xs[2]
        for f in range(30):
            t = f / 29
            # Horizontal interpolation
            cup_xs[1] = int(start_x1 + (start_x2 - start_x1) * t)
            cup_xs[2] = int(start_x2 + (start_x1 - start_x2) * t)
            
            # Add an arc height offset to give a 3D depth illusion during the swap
            arc_y_offset = int(30 * math.sin(t * math.pi))
            
            img = np.zeros((height, width, 3), dtype=np.uint8)
            img[:] = (35, 45, 60)
            
            # Draw stationary Cup 0
            pts0 = np.array([[cup_xs[0]-35, cup_y_base-70], [cup_xs[0]+35, cup_y_base-70], [cup_xs[0]+25, cup_y_base], [cup_xs[0]-25, cup_y_base]], np.int32)
            cv2.fillPoly(img, [pts0], (40, 90, 160))
            
            # Draw Cup 1 curving forward
            y1 = cup_y_base + arc_y_offset
            pts1 = np.array([[cup_xs[1]-35, y1-70], [cup_xs[1]+35, y1-70], [cup_xs[1]+25, y1], [cup_xs[1]-25, y1]], np.int32)
            cv2.fillPoly(img, [pts1], (40, 90, 160))
            
            # Draw Cup 2 curving backward
            y2 = cup_y_base - arc_y_offset
            pts2 = np.array([[cup_xs[2]-35, y2-70], [cup_xs[2]+35, y2-70], [cup_xs[2]+25, y2], [cup_xs[2]-25, y2]], np.int32)
            cv2.fillPoly(img, [pts2], (40, 90, 160))
            
            frames.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

        video_buffer = io.BytesIO()
        frames[0].save(video_buffer, format='GIF', save_all=True, append_images=frames[1:], duration=25, loop=0)
        video_buffer.seek(0)
        return video_buffer

    buffer = await asyncio.to_thread(generate_cup_game)
    await ctx.send(file=discord.File(fp=buffer, filename="cup_game.gif"))


# =========================================================================
# 2. WAND DEMO: Glowing Arcade Cup Game Swap
# =========================================================================
@bot.command()
async def wandshow(ctx):
    """Generates a premium glowing retro arcade variant of the cup shuffle game."""
    await ctx.send("Generating Arcade Cup Game...")

    def generate_wand_cups():
        gif_buffer = io.BytesIO()
        width, height = 400, 250
        
        with WandImage() as anim:
            for frame_idx in range(25):
                t = frame_idx / 24
                x1 = int(120 + 160 * t)
                x2 = int(280 - 160 * t)
                
                with WandImage(width=width, height=height, background='rgb(10,12,18)') as frame:
                    with Drawing() as draw:
                        # Draw high-tech neon glowing table base platform line
                        draw.stroke_color = 'rgb(0, 180, 255)'
                        draw.stroke_width = 3
                        draw.line((30, 200), (370, 200))
                        
                        # Render Cup 1 neon wireframe outline vector
                        draw.stroke_color = 'rgb(255, 0, 128)' # Hot Neon Pink
                        draw.fill_color = 'rgba(255, 0, 128, 0.2)'
                        draw.polygon([(x1-25, 120), (x1+25, 120), (x1+18, 195), (x1-18, 195)])
                        
                        # Render Cup 2 neon wireframe outline vector
                        draw.stroke_color = 'rgb(0, 255, 255)' # Cyber Cyan
                        draw.fill_color = 'rgba(0, 255, 255, 0.2)'
                        draw.polygon([(x2-25, 120), (x2+25, 120), (x2+18, 195), (x2-18, 195)])
                        
                        draw(frame)
                        
                    frame.blur(radius=0, sigma=0.5)
                    anim.sequence.append(frame)
                    
            for frame in anim.sequence:
                frame.delay = 4
                
            anim.format = 'gif'
            anim.save(file=gif_buffer)
        gif_buffer.seek(0)
        return gif_buffer

    buffer = await asyncio.to_thread(generate_wand_cups)
    await ctx.send(file=discord.File(fp=buffer, filename="arcade_cups.gif"))


# =========================================================================
# 3. PYMUNK + OPENCV DEMO: Full 7-Row True Physics Plinko Layout
# =========================================================================
@bot.command()
async def pymunkshow(ctx):
    """Runs a complete 7-tier triangular peg matrix physics Plinko simulation."""
    await ctx.send("Simulating high-stakes Plinko drop physics...")

    def run_plinko_sim():
        space = pymunk.Space()
        space.gravity = (0, 700)

        width, height = 500, 550
        peg_radius = 5
        ball_radius = 8

        # Create a full standard 7-tier triangular Plinko Peg Matrix setup
        pegs = []
        start_y = 100
        row_spacing = 45
        col_spacing = 40

        for row in range(7):
            num_pegs = row + 3
            row_width = (num_pegs - 1) * col_spacing
            start_x = (width - row_width) // 2
            
            for col in range(num_pegs):
                px = start_x + (col * col_spacing)
                py = start_y + (row * row_spacing)
                
                body = pymunk.Body(body_type=pymunk.Body.STATIC)
                shape = pymunk.Circle(body, peg_radius, (px, py))
                shape.elasticity = 0.65
                space.add(body, shape)
                pegs.append((px, py))

        # Spawn dynamic physics ball at the absolute top center with a slight random drop variance offset
        ball_body = pymunk.Body(1, 100)
        ball_body.position = (width // 2 + random.randint(-4, 4), 40)
        ball_shape = pymunk.Circle(ball_body, ball_radius)
        ball_shape.elasticity = 0.5
        space.add(ball_body, ball_shape)

        frames = []
        for _ in range(110):
            space.step(1/30.0)
            
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (24, 20, 18) # Clean charcoal background board
            
            # Draw bottom target score bucket slots lines
            for bx in range(0, width + 50, 50):
                cv2.line(frame, (bx, height-40), (bx, height), (40, 45, 50), 2)

            # Render all structural background fixed pegs
            for peg in pegs:
                cv2.circle(frame, peg, peg_radius, (220, 220, 225), -1) 
                cv2.circle(frame, peg, peg_radius + 2, (60, 60, 65), 1)  
                
            # Render the falling ball matrix coordinates
            bx, by = int(ball_body.position.x), int(ball_body.position.y)
            cv2.circle(frame, (bx, by), ball_radius, (40, 40, 255), -1)   
            cv2.circle(frame, (bx, by), ball_radius - 2, (100, 100, 255), -1) 
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb_frame))

        video_buffer = io.BytesIO()
        frames[0].save(video_buffer, format='GIF', save_all=True, append_images=frames[1:], duration=33, loop=0)
        video_buffer.seek(0)
        return video_buffer

    buffer = await asyncio.to_thread(run_plinko_sim)
    await ctx.send(file=discord.File(fp=buffer, filename="plinko_board.gif"))

class NativeChecklistModal(discord.ui.Modal, title="Notification Preferences"):
    ping_choices = discord.ui.Select(
        placeholder="Select what you want to get pinged for...",
        min_values=1,
        max_values=3,
        options=[
            discord.SelectOption(label="Air", value="air"),
            discord.SelectOption(label="Breathing", value="breathing"),
            discord.SelectOption(label="Death", value="death")
        ]
    )

    async def on_submit(self, interaction: discord.Interaction):
        selected = self.ping_choices.values
        choices_text = ", ".join([choice.capitalize() for choice in selected])
        await interaction.response.send_message(f"Preferences saved! You checked: **{choices_text}**", ephemeral=True)

class OpenChecklistView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Roles Checklist", style=discord.ButtonStyle.blurple)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NativeChecklistModal())

@bot.command(name="checklist")
async def send_checklist_button(ctx: commands.Context):
    await ctx.send("Click the button to pick your preferences!", view=OpenChecklistView())

@bot.command(name="id")
async def user_id_info(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    
    await ensure_user(member.id)
    user_data = USER_DATA.get(member.id, {})
    
    balance = user_data.get("balance", 5000)
    xp = user_data.get("xp", 0)
    vip_status = user_data.get("vip_status", False)

    if vip_status is True:
        vip_display = "👑 VIP Member"
    elif vip_status is False:
        vip_display = "❌ Regular"
    else:
        vip_display = f"✨ {vip_status}"

    embed = discord.Embed(
        title=f"📋 Target Dossier: {member.name}",
        color=member.color if member.color.value != 0 else discord.Color.blurple(),
        timestamp=ctx.message.created_at
    )
    
    if member.display_avatar:
        embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="👤 Username", value=f"`{member.name}`", inline=True)
    embed.add_field(name="🆔 Discord ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="📅 Account Age", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)

    embed.add_field(name="💰 Wallet Balance", value=f"`${balance:,}`", inline=True)
    embed.add_field(name="⚡ Experience", value=f"`{xp:,} XP`", inline=True)
    embed.add_field(name="👑 VIP Tier", value=f"**{vip_display}**", inline=True)

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
async def standing(ctx, member: discord.Member = None):
    target_user = member if member else ctx.author
    await ensure_user(target_user.id)
    
    user_id = target_user.id
    user_info = USER_DATA[user_id]
    
    flags = len(user_info.get("flags", [])) if isinstance(user_info.get("flags"), list) else user_info.get("flags", 0)
    strikes = user_info.get("strikes", 0)
    trespassed = user_info.get("trespassed", False)
    
    if trespassed or strikes >= 3:
        tier = 4
        status_text = "Suspended"
        sub_text = "This account has been suspended / trespassed due to safety violations."
    elif (strikes == 2 and flags == 1) or flags >= 3:
        tier = 3
        status_text = "At Risk"
        sub_text = "This account is at critical risk. Further violations will result in suspension."
    elif (strikes == 1 and flags == 1) or strikes == 2 or flags == 2:
        tier = 2
        status_text = "Very Limited"
        sub_text = "This account features are heavily restricted due to multiple safety concerns."
    elif strikes == 1 or flags == 1:
        tier = 1
        status_text = "Limited"
        sub_text = "This account has active restrictions from the Gambler safety team."
    else:
        tier = 0
        status_text = "in good standing."
        sub_text = "This account does not have any active violations or restrictions."

    width, height = 900, 420
    bg_color = (34, 37, 44)  
    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_bold = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 15)
        font_axis = ImageFont.truetype("arial.ttf", 13)
        font_history_hdr = ImageFont.truetype("arial.ttf", 16)
        font_history_item = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font_title = font_bold = font_sub = font_axis = font_history_hdr = font_history_item = ImageFont.load_default()

    draw.text((25, 20), f"Account Standing — {target_user.name}", fill=(255, 255, 255), font=font_title)
    
    green_color = (46, 184, 114)
    orange_color = (255, 167, 38)
    red_color = (239, 83, 80)
    gray_inactive = (74, 79, 88)
    text_white = (255, 255, 255)
    text_muted = (160, 165, 175)
    
    if tier == 0:
        status_color = green_color
    elif tier in [1, 2]:
        status_color = orange_color
    else:
        status_color = red_color
    
    circle_center = (55, 105)
    circle_radius = 22
    draw.ellipse([circle_center[0] - circle_radius, circle_center[1] - circle_radius, 
                  circle_center[0] + circle_radius, circle_center[1] + circle_radius], fill=status_color)
    
    if tier == 0:  
        draw.line([(47, 105), (52, 112)], fill=(255, 255, 255), width=3)
        draw.line([(52, 112), (65, 98)], fill=(255, 255, 255), width=3)
    elif tier in [1, 2]:  
        draw.line([(47, 105), (63, 105)], fill=(255, 255, 255), width=4)
    elif tier == 3:  
        draw.line([(55, 94), (55, 107)], fill=(255, 255, 255), width=3)
        draw.ellipse([54, 112, 56, 114], fill=(255, 255, 255))
    elif tier == 4:  
        draw.line([(47, 97), (63, 113)], fill=(255, 255, 255), width=3)
        draw.line([(63, 97), (47, 113)], fill=(255, 255, 255), width=3)

    draw.text((95, 85), f"Account status: {status_text}", fill=text_white, font=font_bold)
    draw.text((95, 115), sub_text, fill=text_muted, font=font_sub)
    
    start_x, end_x = 55, 845
    track_y = 210
    
    nodes = [
        {"name": "All Good", "x": start_x},
        {"name": "Limited", "x": start_x + 197},
        {"name": "Very Limited", "x": start_x + 394},
        {"name": "At Risk", "x": start_x + 591},
        {"name": "Suspended", "x": end_x}
    ]
    
    draw.line([(start_x, track_y), (end_x, track_y)], fill=gray_inactive, width=4)
    
    if tier > 0:
        target_fill_x = nodes[tier]["x"]
        draw.line([(start_x, track_y), (target_fill_x, track_y)], fill=status_color, width=4)
    
    for idx, node in enumerate(nodes):
        node_x = node["x"]
        if idx <= tier:
            radius = 7 if idx == tier else 5
            draw.ellipse([node_x - radius, track_y - radius, node_x + radius, track_y + radius], fill=status_color)
            w = draw.textlength(node["name"], font=font_axis)
            lbl_color = text_white if idx == tier else text_muted
            draw.text((node_x - w/2, track_y + 15), node["name"], fill=lbl_color, font=font_axis)
        else:
            draw.ellipse([node_x - 5, track_y - 5, node_x + 5, track_y + 5], fill=gray_inactive)
            w = draw.textlength(node["name"], font=font_axis)
            draw.text((node_x - w/2, track_y + 15), node["name"], fill=text_muted, font=font_axis)

    # 5. Render Recent History
    draw.line([(25, 275), (875, 275)], fill=gray_inactive, width=1)
    draw.text((25, 285), "Recent Moderation Actions History", fill=text_white, font=font_history_hdr)
    
    history_actions = user_info.get("moderation_history", [])[-3:][::-1]
    
    if not history_actions:
        draw.text((25, 315), "No history entries found.", fill=text_muted, font=font_history_item)
    else:
        y_offset = 315
        for action in history_actions:
            if isinstance(action, dict):
                timestamp = action.get('when', 'Unknown Time')
                if len(timestamp) > 19:
                    timestamp = timestamp[:19]
                
                act_type = str(action.get('what', 'ACTION'))
                act_reason = str(action.get('why', 'No reason specified'))
                act_admin = str(action.get('who', 'Staff')).split(" (")[0]
                
                action_text = f"• [{timestamp}] {act_type}: {act_reason} (By: {act_admin})"
            else:
                action_text = f"• {str(action)}"
                
            draw.text((25, y_offset), action_text, fill=text_muted, font=font_history_item)
            y_offset += 24

    with io.BytesIO() as image_binary:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        discord_file = discord.File(fp=image_binary, filename='account_standing.png')
        await ctx.send(file=discord_file)


# --- PARDON COMMAND ---
@bot.command()
async def pardon(ctx, member: discord.Member = None, *, reason: str = "Behavior improved / Management decision"):
    if not ctx.author.id in ADMIN_IDS:
        await ctx.send("**You don't have permission to use this command.**")
        return
        
    if member is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You forgot to specify a user to pardon.", color=0xFF0000)
        embed.add_field(name="Correct Format:", value="`!pardon <@user/ID> [reason]`")
        await ctx.send(embed=embed)
        return

    user_id = member.id
    await ensure_user(user_id)

    # Clean active penalty stats
    USER_DATA[user_id]["flags"] = []
    USER_DATA[user_id]["strikes"] = 0
    USER_DATA[user_id]["trespassed"] = False

    # Add historical log entry
    USER_DATA[user_id]["moderation_history"].append({
        "who": f"{ctx.author.name} (ID: {ctx.author.id})",
        "what": "PARDON / RESET",
        "when": str(datetime.datetime.now(datetime.UTC)),
        "why": str(reason)
    })

    await save_user_data()

    embed = discord.Embed(title="✅ User Standing Reset", description=f"{member.mention} has had all restrictions removed and is back in good standing.", color=0x2EB872)
    embed.add_field(name="Pardon Reason", value=reason)
    await ctx.send(embed=embed)

def get_text_wrapped_lines(text, font, max_width, draw_context):
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if draw_context.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def draw_vector_icon(draw, icon_type, cx, cy, color, zoom, is_locked):
    if is_locked:
        w = int(14 * zoom)
        h = int(12 * zoom)
        r = int(5 * zoom)
        draw.rectangle([cx - (w // 2), cy - (h // 4), cx + (w // 2), cy + (h // 2) + int(4 * zoom)], fill=None, outline=color, width=max(2, int(3 * zoom)))
        draw.arc([cx - r, cy - (h // 2) - r, cx + r, cy - (h // 4) + int(2 * zoom)], start=180, end=360, fill=color, width=max(2, int(3 * zoom)))
        draw.line([cx - r, cy - (h // 4) + int(1 * zoom), cx - r, cy - (h // 4) + int(3 * zoom)], fill=color, width=max(2, int(3 * zoom)))
        draw.line([cx + r, cy - (h // 4) + int(1 * zoom), cx + r, cy - (h // 4) + int(3 * zoom)], fill=color, width=max(2, int(3 * zoom)))
        return

    if icon_type == "nexus":
        r = int(12 * zoom)
        draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=color, width=max(2, int(3 * zoom)))
        draw.ellipse([cx - int(5 * zoom), cy - int(5 * zoom), cx + int(5 * zoom), cy + int(5 * zoom)], fill=color)
    elif icon_type == "card":
        w, h = int(16 * zoom), int(22 * zoom)
        left, top = cx - (w // 2), cy - (h // 2)
        right, bottom = cx + (w // 2), cy + (h // 2)
        draw.rectangle([left, top, right, bottom], outline=color, width=max(2, int(3 * zoom)))
        draw.polygon([(cx, cy - int(5 * zoom)), (cx + int(4 * zoom), cy), (cx, cy + int(5 * zoom)), (cx - int(4 * zoom), cy)], fill=color)
    elif icon_type == "token":
        radius = int(12 * zoom)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=color, width=max(2, int(3 * zoom)))
        draw.ellipse([cx - int(5 * zoom), cy - int(5 * zoom), cx + int(5 * zoom), cy + int(5 * zoom)], fill=color)
        for angle in [0, 45, 90, 135]:
            draw.line([cx - int(3 * zoom), cy, cx + int(3 * zoom), cy], fill=color, width=1)
    elif icon_type == "coin":
        radius = int(11 * zoom)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=None, outline=color, width=max(2, int(3 * zoom)))
        draw.text((cx - int(4 * zoom), cy - int(6 * zoom)), "$", fill=color, font=ImageFont.load_default())
    elif icon_type == "slots":
        w, h = int(24 * zoom), int(18 * zoom)
        draw.rectangle([cx - (w // 2), cy - (h // 2), cx + (w // 2), cy + (h // 2)], fill=None, outline=color, width=max(2, int(3 * zoom)))
        draw.line([cx - (w // 6), cy - (h // 2), cx - (w // 6), cy + (h // 2)], fill=color, width=1)
        draw.line([cx + (w // 6), cy - (h // 2), cx + (w // 6), cy + (h // 2)], fill=color, width=1)
        draw.rectangle([cx + (w // 2), cy - int(6 * zoom), cx + (w // 2) + int(4 * zoom), cy], fill=color)
    elif icon_type == "dice":
        w = int(18 * zoom)
        left, top = cx - (w // 2), cy - (w // 2)
        draw.rectangle([left, top, left + w, top + w], fill=None, outline=color, width=max(2, int(3 * zoom)))
        draw.ellipse([cx - int(4 * zoom), cy - int(4 * zoom), cx - int(2 * zoom), cy - int(2 * zoom)], fill=color)
        draw.ellipse([cx + int(2 * zoom), cy + int(2 * zoom), cx + int(4 * zoom), cy + int(4 * zoom)], fill=color)
    elif icon_type == "wheel":
        radius = int(12 * zoom)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=None, outline=color, width=max(2, int(3 * zoom)))
        draw.line([cx - radius, cy, cx + radius, cy], fill=color, width=1)
        draw.line([cx, cy - radius, cx, cy + radius], fill=color, width=1)

def generate_skill_tree_img(user_points, user_skills, target_name, cam_x, cam_y, zoom):
    width, height = 980, 480
    bg_color = (20, 22, 26)
    
    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    color_locked = (55, 58, 66)       
    color_unlocked = (0, 180, 216)    
    color_maxed = (46, 184, 114)     
    color_available = (240, 242, 245) 
    
    text_white = (255, 255, 255)
    text_muted = (141, 147, 161)

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 26)
        font_subtitle = ImageFont.truetype("arial.ttf", 14)
        font_name = ImageFont.truetype("arialbd.ttf", max(14, int(18 * zoom)))
        font_desc = ImageFont.truetype("arialbd.ttf", max(11, int(13 * zoom)))
        font_meta = ImageFont.truetype("arialbd.ttf", max(12, int(14 * zoom)))
    except IOError:
        font_title = font_name = font_desc = font_meta = font_subtitle = ImageFont.load_default()

    draw.text((40, 25), "PLAYER PROGRESSION DASHBOARD", fill=text_muted, font=font_subtitle)
    draw.text((40, 43), f"Skill Tree Matrix — {target_name.upper()}", fill=text_white, font=font_title)
    draw.text((40, 83), f"Available Points: PTS {user_points}", fill=color_unlocked, font=font_title)

    for skill_id, data in SKILL_TREE.items():
        for prereq_id in data["prereqs"]:
            parent_data = SKILL_TREE[prereq_id]
            p_world_x, p_world_y = parent_data["pos"]
            c_world_x, c_world_y = data["pos"]
            
            p_x = int((p_world_x - cam_x) * zoom + (width / 2))
            p_y = int((p_world_y - cam_y) * zoom + (height / 2))
            c_x = int((c_world_x - cam_x) * zoom + (width / 2))
            c_y = int((c_world_y - cam_y) * zoom + (height / 2))
            
            parent_lvl = user_skills.get(prereq_id, 0)
            parent_max = parent_data["max_level"]
            
            if parent_lvl >= parent_max:
                line_color = color_maxed if user_skills.get(skill_id, 0) > 0 else color_available
            else:
                line_color = color_locked
                
            draw.line([(p_x, p_y), (c_x, c_y)], fill=line_color, width=max(2, int(4 * zoom)))

    for skill_id, data in SKILL_TREE.items():
        world_x, world_y = data["pos"]
        x = int((world_x - cam_x) * zoom + (width / 2))
        y = int((world_y - cam_y) * zoom + (height / 2))
        
        box_w, box_h = int(220 * zoom), int(114 * zoom)
        left, top = x - (box_w // 2), y - (box_h // 2)
        right, bottom = x + (box_w // 2), y + (box_h // 2)
        
        current_lvl = user_skills.get(skill_id, 0)
        max_lvl = data["max_level"]
        
        is_prereq_met = True
        for prereq_id in data["prereqs"]:
            parent_info = SKILL_TREE[prereq_id]
            if user_skills.get(prereq_id, 0) < parent_info["max_level"]:
                is_prereq_met = False
                break
                
        if current_lvl >= max_lvl:
            node_color = color_maxed
            status_lbl = "MAX LEVEL"
            is_locked_icon = False
        elif current_lvl > 0:
            node_color = color_unlocked
            status_lbl = f"LEVEL {current_lvl} / {max_lvl}"
            is_locked_icon = False
        elif is_prereq_met:
            node_color = color_available
            status_lbl = f"UNLOCK: PTS {data['cost']}"
            is_locked_icon = False
        else:
            node_color = color_locked
            status_lbl = "LOCKED"
            is_locked_icon = True

        draw.rounded_rectangle([left, top, right, bottom], radius=int(6 * zoom), fill=(28, 31, 38))
        draw.rounded_rectangle([left, top, right, bottom], radius=int(6 * zoom), outline=node_color, width=max(2, int(3 * zoom)))
        
        draw_vector_icon(draw, data["icon"], left + int(30 * zoom), top + int(30 * zoom), node_color, zoom, is_locked_icon)
        
        draw.text((left + int(55 * zoom), top + int(14 * zoom)), data["name"], fill=text_white, font=font_name)
        
        desc_box_w = box_w - int(35 * zoom)
        desc_lines = get_text_wrapped_lines(data["desc"], font_desc, desc_box_w, draw)
        
        current_y_offset = top + int(42 * zoom)
        for line in desc_lines[:3]:
            draw.text((left + int(20 * zoom), current_y_offset), line, fill=text_muted, font=font_desc)
            current_y_offset += int(15 * zoom)
            
        draw.text((left + int(20 * zoom), bottom - int(20 * zoom)), status_lbl, fill=node_color, font=font_meta)

    image_binary = io.BytesIO()
    img.save(image_binary, 'PNG')
    image_binary.seek(0)
    return image_binary

class SkillTreeNavigator(discord.ui.View):
    def __init__(self, ctx, target_user):
        super().__init__(timeout=180.0)
        self.ctx = ctx
        self.target_user = target_user

    async def update_view(self, interaction: discord.Interaction):
        user_id = self.target_user.id
        session = VIEWPORT_SESSIONS[user_id]
        
        user_data = USER_DATA[user_id]
        points = user_data["skill_points"]
        skills_owned = user_data["skills"]
        
        loop = asyncio.get_running_loop()
        buffer = await loop.run_in_executor(
            None, generate_skill_tree_img, points, skills_owned, self.target_user.name,
            session["cam_x"], session["cam_y"], session["zoom"]
        )
        
        file = discord.File(fp=buffer, filename="skills_dashboard.png")
        await interaction.response.edit_message(attachments=[file], view=self)

    @discord.ui.button(label="Zoom In", style=discord.ButtonStyle.blurple, row=0)
    async def zoom_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["zoom"] = min(2.0, VIEWPORT_SESSIONS[self.target_user.id]["zoom"] + 0.35)
        await self.update_view(interaction)

    @discord.ui.button(label="Zoom Out", style=discord.ButtonStyle.blurple, row=0)
    async def zoom_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["zoom"] = max(0.3, VIEWPORT_SESSIONS[self.target_user.id]["zoom"] - 0.35)
        await self.update_view(interaction)

    @discord.ui.button(label="Up", style=discord.ButtonStyle.secondary, row=1)
    async def move_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["cam_y"] -= int(200 / VIEWPORT_SESSIONS[self.target_user.id]["zoom"])
        await self.update_view(interaction)

    @discord.ui.button(label="Down", style=discord.ButtonStyle.secondary, row=1)
    async def move_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["cam_y"] += int(200 / VIEWPORT_SESSIONS[self.target_user.id]["zoom"])
        await self.update_view(interaction)

    @discord.ui.button(label="Left", style=discord.ButtonStyle.secondary, row=2)
    async def move_left(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["cam_x"] -= int(250 / VIEWPORT_SESSIONS[self.target_user.id]["zoom"])
        await self.update_view(interaction)

    @discord.ui.button(label="Right", style=discord.ButtonStyle.secondary, row=2)
    async def move_right(self, interaction: discord.Interaction, button: discord.ui.Button):
        VIEWPORT_SESSIONS[self.target_user.id]["cam_x"] += int(250 / VIEWPORT_SESSIONS[self.target_user.id]["zoom"])
        await self.update_view(interaction)

@bot.command()
async def skills_help(ctx):
    user_id = ctx.author.id
    USER_ACKNOWLEDGED_HELP.add(user_id)
    
    embed = discord.Embed(
        title="Skill Tree System - Operational Manual",
        description="Welcome to the Skill Tree Progression System. Below is a detailed breakdown of how to navigate, unlock, and understand your abilities.",
        color=0x00B4D6
    )
    embed.add_field(
        name="1. How to View Your Tree",
        value="Use the `!skills` command to bring up your private dashboard interactive map. You can use the map manipulation utility buttons below the interface to pan or change sizing options.",
        inline=False
    )
    embed.add_field(
        name="2. Navigation Controls",
        value="• **Zoom In/Out:** Increases or decreases sizing parameters dynamically.\n• **Directional Pads (Up/Down/Left/Right):** Adjusts your current spatial mapping vector center fields by bulk scaling increments to navigate remote branches quickly.",
        inline=False
    )
    embed.add_field(
        name="3. Nodes and Special Paths",
        value="Your progression web originates directly at the center node, the **Nexus Core**. You must optimize prerequisite parent links outward before adjacent exterior paths reveal themselves. Advanced perks (like `Card Shark`) have high structural multi-dependencies that require multiple branches to be fully mastered before unlocking.",
        inline=False
    )
    embed.add_field(
        name="4. Node Colors and Visual Indicators",
        value="• **Gray Border + Lock Icon:** Blocked from view. Prerequisite path branches are unoptimized.\n• **White Border + Open Icon:** Ready for optimization. Purchase is available.\n• **Blue Border + Open Icon:** Partially filled node.\n• **Green Border + Open Icon:** Maximized node.",
        inline=False
    )
    embed.add_field(
        name="5. Purchasing Upgrades",
        value="To spend your gathered points and claim your perks, provide the specific selection identifier directly to the purchasing command:\n`!buy_skill double_down` or `!buy_skill lucky_seven`",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command()
async def skills(ctx, member: discord.Member = None):
    target_user = member if member else ctx.author
    await ensure_user(target_user.id)
    
    if ctx.author.id not in USER_ACKNOWLEDGED_HELP:
        await ctx.send(f"❌ You must view the operational documentation manual first. Please execute the `!skills_help` command before utilizing the progression terminals.")
        return
    
    if "skill_points" not in USER_DATA[target_user.id]:
        USER_DATA[target_user.id]["skill_points"] = 0
    if "skills" not in USER_DATA[target_user.id]:
        USER_DATA[target_user.id]["skills"] = {}
        
    VIEWPORT_SESSIONS[target_user.id] = {
        "cam_x": 500,
        "cam_y": 500,
        "zoom": 0.6
    }
        
    user_data = USER_DATA[target_user.id]
    points = user_data["skill_points"]
    skills_owned = user_data["skills"]
    
    loop = asyncio.get_running_loop()
    buffer = await loop.run_in_executor(
        None, generate_skill_tree_img, points, skills_owned, target_user.name,
        500, 500, 0.6
    )
    
    file = discord.File(fp=buffer, filename="skills_dashboard.png")
    view = SkillTreeNavigator(ctx, target_user)
    await ctx.send(file=file, view=view)

@bot.command()
async def buy_skill(ctx, skill_id: str = None):
    await ensure_user(ctx.author.id)
    user_id = ctx.author.id
    
    if ctx.author.id not in USER_ACKNOWLEDGED_HELP:
        await ctx.send(f"❌ You must view the operational documentation manual first. Please execute the `!skills_help` command before utilizing the progression terminals.")
        return
    
    if "skill_points" not in USER_DATA[user_id]:
        USER_DATA[user_id]["skill_points"] = 0
    if "skills" not in USER_DATA[user_id]:
        USER_DATA[user_id]["skills"] = {}

    if not skill_id or skill_id not in SKILL_TREE:
        valid_ids = ", ".join([f"`{k}`" for k in SKILL_TREE.keys()])
        await ctx.send(f"❌ Unknown Skill selection ID. Options: {valid_ids}")
        return
        
    skill = SKILL_TREE[skill_id]
    user_skills = USER_DATA[user_id]["skills"]
    current_level = user_skills.get(skill_id, 0)
    
    if current_level >= skill["max_level"]:
        await ctx.send("❌ Skill node is already at max capacity.")
        return
        
    if USER_DATA[user_id]["skill_points"] < skill["cost"]:
        await ctx.send("❌ You do not have enough skill points.")
        return
        
    for prereq_id in skill["prereqs"]:
        if user_skills.get(prereq_id, 0) < SKILL_TREE[prereq_id]["max_level"]:
            await ctx.send(f"❌ Prerequisite skill locked: `{SKILL_TREE[prereq_id]['name']}` must be maxed.")
            return

    USER_DATA[user_id]["skill_points"] -= skill["cost"]
    USER_DATA[user_id]["skills"][skill_id] = current_level + 1
    await save_user_data()
    
    await ctx.send(f"✨ Successfully upgraded **{skill['name']}** to level **{current_level + 1}**!")

@bot.command()
async def dbg_skill(ctx, action: str = None, member: discord.Member = None, amount: str = None):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send("**Permission denied.**")
        return

    if not action or not member or not amount:
        embed = discord.Embed(title="Developer Command Reference", color=0x00B4D6)
        embed.add_field(name="Points Control", value="`!dbg_skill add @user 50` \n`!dbg_skill remove @user 20` \n`!dbg_skill reset_points @user 0`", inline=False)
        embed.add_field(name="Skill Locks & Resets", value="`!dbg_skill skill @user all` \n`!dbg_skill skill @user 1` \n`!dbg_skill skill @user 1.5` \n`!dbg_skill reset_tree @user 0`", inline=False)
        await ctx.send(embed=embed)
        return

    user_id = member.id
    await ensure_user(user_id)
    
    if "skill_points" not in USER_DATA[user_id]:
        USER_DATA[user_id]["skill_points"] = 0
    if "skills" not in USER_DATA[user_id]:
        USER_DATA[user_id]["skills"] = {}

    action = action.lower()

    if action == "reset_points":
        USER_DATA[user_id]["skill_points"] = 0
        await save_user_data()
        await ctx.send(f"✨ Reset all skill points to 0 for {member.mention}.")
        return

    elif action == "reset_tree":
        USER_DATA[user_id]["skills"] = {}
        await save_user_data()
        await ctx.send(f"🔄 Completely wiped and reset the skill tree for {member.mention}.")
        return

    if action in ["add", "remove"]:
        try:
            val = int(amount)
            if val < 0: raise ValueError
        except ValueError:
            await ctx.send("❌ Amount parameter values must be positive integers.")
            return

        if action == "add":
            USER_DATA[user_id]["skill_points"] += val
            msg = f"✨ Added `{val}` skill points to {member.mention}'s profile balance."
        else:
            current_points = USER_DATA[user_id]["skill_points"]
            deduct_val = min(val, current_points)
            USER_DATA[user_id]["skill_points"] -= deduct_val
            msg = f"📉 Subtracted `{deduct_val}` skill points from {member.mention}'s balance. (Floored at 0)"

        await save_user_data()
        await ctx.send(msg)
        return

    elif action == "skill":
        target_path = amount.lower()
        
        if target_path == "all":
            for s_id, s_data in SKILL_TREE.items():
                USER_DATA[user_id]["skills"][s_id] = s_data["max_level"]
            msg = f"🧬 Fully unlocked and maxed out all skills for {member.mention}."
            
        elif target_path == "1":
            path_ids = ["double_down", "lucky_seven", "card_shark"]
            for s_id in path_ids:
                USER_DATA[user_id]["skills"][s_id] = SKILL_TREE[s_id]["max_level"]
            msg = f"⚡ Maxed progression path 1 (Blackjack specialization line) for {member.mention}."
            
        elif target_path == "1.5":
            path_ids = ["double_down", "high_roller", "card_shark"]
            for s_id in path_ids:
                USER_DATA[user_id]["skills"][s_id] = SKILL_TREE[s_id]["max_level"]
            msg = f"🔀 Maxed progression branch path 1.5 (High Roller/Limits specialization line) for {member.mention}."
            
        else:
            await ctx.send("❌ Invalid path selection option string. Choose `all`, `1`, or `1.5`.")
            return

        await save_user_data()
        await ctx.send(msg)
        return
    else:
        await ctx.send("❌ Action operator parameter error.")

@bot.command()
async def taskmgr(ctx):
    """Displays comprehensive backend system and bot metrics."""
    if ctx.author.id not in ADMIN_IDS:
        return

    await ctx.typing()

    # 1. Hardware, CPU Cores, and Detailed Process Stats
    pid = os.getpid()
    process = psutil.Process(pid)
    
    cpu_usage = psutil.cpu_percent(interval=0.1)
    cpu_cores_percent = psutil.cpu_percent(percpu=True)
    cpu_freq = psutil.cpu_freq()
    cpu_freq_str = f"{cpu_freq.current:.0f}MHz" if cpu_freq else "N/A"
    
    ram_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()
    disk_info = psutil.disk_usage('/')
    io_counters = psutil.disk_io_counters()
    net_counters = psutil.net_io_counters()
    
    # Detailed Process Diagnostics
    process_mem_info = process.memory_info()
    rss_mem = process_mem_info.rss / (1024 * 1024) 
    vms_mem = process_mem_info.vms / (1024 * 1024)
    ctx_switches = process.num_ctx_switches()
    open_files = len(process.open_files())
    net_connections = len(process.net_connections())

    # 2. Advanced Discord & Gateway Telemetry
    gateway_ping = round(bot.latency * 1000, 2)
    guild_count = len(bot.guilds)
    voice_clients = len(bot.voice_clients)
    
    # Database of Cached Structures
    total_users = len(bot.users)
    cached_emojis = len(bot.emojis)
    cached_stickers = len(bot.stickers)
    cached_messages = bot._connection._messages.maxlen if bot._connection._messages else 0
    
    # Shard breakdown (if applicable)
    shard_count = bot.shard_count or 1
    shard_id = ctx.guild.shard_id if ctx.guild else 0

    # 3. Asyncio Engine Diagnostics
    loop = asyncio.get_running_loop()
    asyncio_tasks = len(asyncio.all_tasks(loop))
    loop_time = loop.time()

    # 4. Engine & Time Metrics
    uptime_seconds = int(process.create_time())
    uptime_dt = datetime.datetime.fromtimestamp(uptime_seconds, tz=datetime.timezone.utc)
    uptime_str = f"<t:{int(uptime_dt.timestamp())}:R>"

    # 5. Construct Dashboard Embed
    embed = discord.Embed(
        title="🖥️ Ultimate Backend Diagnostics Engine",
        color=discord.Color.from_rgb(47, 49, 54),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    embed.add_field(
        name="📊 Host Hardware Topology",
        value=(
            f"**CPU Aggregate:** {cpu_usage}% @ {cpu_freq_str}\n"
            f"**Per-Core Load:** `{'% | '.join(map(str, cpu_cores_percent))}%`\n"
            f"**Physical RAM:** {ram_info.percent}% ({ram_info.used / (1024**3):.2f}GB / {ram_info.total / (1024**3):.2f}GB)\n"
            f"**Swap Memory:** {swap_info.percent}% ({swap_info.used / (1024**3):.2f}GB / {swap_info.total / (1024**3):.2f}GB)\n"
            f"**Main Drive Storage:** {disk_info.percent}% ({disk_info.free / (1024**3):.2f}GB free)"
        ),
        inline=False
    )

    embed.add_field(
        name="🐍 Active Python Process Metadata",
        value=(
            f"**Process ID (PID):** `{pid}`\n"
            f"**Physical Memory (RSS):** `{rss_mem:.2f} MB`\n"
            f"**Virtual Memory (VMS):** `{vms_mem:.2f} MB`\n"
            f"**Active OS Threads:** `{process.num_threads()}`\n"
            f"**File Handles Open:** `{open_files}`\n"
            f"**Active TCP/UDP Sockets:** `{net_connections}`\n"
            f"**Context Switches:** 🔄 Vol: `{ctx_switches.voluntary}` | ⚠️ Invol: `{ctx_switches.involuntary}`"
        ),
        inline=False
    )

    embed.add_field(
        name="📡 Network I/O & Gateway Pipe",
        value=(
            f"**Gateway Heartbeat:** `{gateway_ping} ms`\n"
            f"**Global Shard Registry:** Shard `{shard_id + 1}` of `{shard_count}`\n"
            f"**Host Network Sent:** `{net_counters.bytes_sent / (1024**2):.2f} MB`\n"
            f"**Host Network Recv:** `{net_counters.bytes_recv / (1024**2):.2f} MB`\n"
            f"**Disk Operations:** 📥 Read: `{io_counters.read_count}` | 📤 Write: `{io_counters.write_count}`"
        ),
        inline=False
    )

    embed.add_field(
        name="📦 Memory Cache Databases",
        value=(
            f"**Guild Clusters:** `{guild_count}`\n"
            f"**User Index Memory:** `{total_users}`\n"
            f"**Voice Pipelines:** `{voice_clients}`\n"
            f"**Emojis / Stickers:** `{cached_emojis}` / `{cached_stickers}`\n"
            f"**Message Cache Volatility:** `{cached_messages} entries max`"
        ),
        inline=True
    )

    embed.add_field(
        name="⚙️ Asyncio Engine & Environment",
        value=(
            f"**Concurrent Task Nodes:** `{asyncio_tasks}`\n"
            f"**Loop Clock Time:** `{loop_time:.2f}s`\n"
            f"**Uptime Engine Status:** {uptime_str}\n"
            f"**Core Interpreter:** `Python v{platform.python_version()}`\n"
            f"**Framework Version:** `discord.py v{discord.__version__}`"
        ),
        inline=True
    )

    embed.set_footer(text=f"Diagnostic System Hook Triggered by {ctx.author}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
async def slots(ctx, bet: str = None):
    user_id = ctx.author.id
    await ensure_user(user_id)
    if USER_DATA[user_id].get("trespassed", False):
        embed = discord.Embed(title="❌ Access Denied", description="You are **Trespassed** from this establishment. Security will not allow you to play.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    current_time = time.time()
    last_played = USER_DATA[user_id].get("last_command_timestamp", 0.0)
    if current_time - last_played < 3.0:
        remaining = 3.0 - (current_time - last_played)
        await ctx.send(f"⏳ Please wait **{remaining:.1f}** seconds before spinning the reels again.")
        return

    if bet is None:
        embed = discord.Embed(title="❌ Invalid Command Usage", description="You must specify your bet amount.", color=0xff0000)
        embed.add_field(name="Correct Usage", value="`!slots <bet_amount>`\n`!slots <percentage>%`\n`!slots all`", inline=False)
        await ctx.send(embed=embed)
        return

    current_balance = USER_DATA[user_id]["balance"]
    if bet.lower() == "all":
        bet_amount = current_balance
    elif bet.endswith("%"):
        try:
            percentage = float(bet[:-1])
            bet_amount = int(current_balance * (percentage / 100))
        except ValueError:
            embed = discord.Embed(title="❌ Invalid Bet Amount", description="Invalid percentage format. Use a number followed by '%'.", color=0xff0000)
            await ctx.send(embed=embed)
            return
    else:
        try:
            bet_amount = int(bet)
        except ValueError:
            embed = discord.Embed(title="❌ Invalid Bet Amount", description="Please enter a valid whole number for your wager, a percentage ending in '%', or type `all`.", color=0xff0000)
            await ctx.send(embed=embed)
            return

    if bet_amount <= 0:
        embed = discord.Embed(title="❌ Invalid Bet Amount", description="Your bet must be greater than 0 chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return
    if current_balance < bet_amount:
        embed = discord.Embed(title="❌ Insufficient Funds", description=f"You do not have enough chips. Current Balance: **{current_balance}** chips.", color=0xff0000)
        await ctx.send(embed=embed)
        return

    USER_DATA[user_id]["last_command_timestamp"] = current_time
    USER_DATA[user_id]["total_games"] += 1
    
    if "upgrades" not in USER_DATA[user_id]:
        USER_DATA[user_id]["upgrades"] = {"plinko_boost": 0, "slots_boost": 0, "slots_winboost": 0, "xp_booster": 0}
    xp_level = USER_DATA[user_id]["upgrades"].get("xp_booster", 0)
    xp_to_add = int(1 * (1 + (xp_level * 0.25)))
    await add_xp(user_id, xp_to_add)

    def draw_custom_shape(draw, shape_name, cx, cy):
        if shape_name == "SEVEN":
            draw.polygon([(cx-20, cy-25), (cx+20, cy-25), (cx+5, cy+25), (cx-5, cy+25), (cx+8, cy-15), (cx-20, cy-15)], fill=(212, 175, 55))
        elif shape_name == "DIAMOND":
            draw.polygon([(cx, cy-25), (cx+22, cy), (cx, cy+25), (cx-22, cy)], fill=(0, 238, 238), outline=(255, 255, 255), width=1)
        elif shape_name == "BELL":
            draw.pieslice([cx-22, cy-25, cx+22, cy+15], start=180, end=360, fill=(245, 215, 0))
            draw.rectangle([cx-22, cy+10, cx+22, cy+18], fill=(245, 215, 0))
            draw.ellipse([cx-6, cy+16, cx+6, cy+26], fill=(210, 105, 30))
        elif shape_name == "CHERRY":
            draw.line([(cx-12, cy+10), (cx, cy-20), (cx+12, cy+10)], fill=(139, 69, 19), width=3)
            draw.ellipse([cx-22, cy, cx-2, cy+20], fill=(220, 20, 60))
            draw.ellipse([cx+2, cy, cx+22, cy+20], fill=(220, 20, 60))
        elif shape_name == "CLOVER":
            draw.line([(cx, cy), (cx+10, cy+25)], fill=(34, 139, 34), width=4)
            draw.ellipse([cx-18, cy-18, cx-2, cy-2], fill=(46, 139, 87))
            draw.ellipse([cx+2, cy-18, cx+18, cy-2], fill=(46, 139, 87))
            draw.ellipse([cx-18, cy+2, cx-2, cy+18], fill=(46, 139, 87))
            draw.ellipse([cx+2, cy+2, cx+18, cy+18], fill=(46, 139, 87))
        elif shape_name == "STAR":
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = 25 if i % 2 == 0 else 10
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            draw.polygon(points, fill=(255, 165, 0), outline=(255, 215, 0), width=1)
        elif shape_name == "WATERMELON":
            draw.pieslice([cx-24, cy-24, cx+24, cy+24], start=0, end=180, fill=(34, 139, 34))
            draw.pieslice([cx-20, cy-24, cx+20, cy+20], start=0, end=180, fill=(220, 20, 60))
            draw.ellipse([cx-8, cy+4, cx-4, cy+8], fill=(0, 0, 0))
            draw.ellipse([cx+4, cy+4, cx+8, cy+8], fill=(0, 0, 0))
        elif shape_name == "LEMON":
            draw.ellipse([cx-22, cy-15, cx+22, cy+15], fill=(255, 215, 0))
            draw.polygon([(cx-26, cy), (cx-20, cy-5), (cx-20, cy+5)], fill=(255, 215, 0))
            draw.polygon([(cx+26, cy), (cx+20, cy-5), (cx+20, cy+5)], fill=(255, 215, 0))
        elif shape_name == "GRAPE":
            draw.line([(cx, cy-20), (cx+5, cy-25)], fill=(139, 69, 19), width=2)
            draw.ellipse([cx-14, cy-14, cx, cy], fill=(128, 0, 128))
            draw.ellipse([cx, cy-14, cx+14, cy], fill=(128, 0, 128))
            draw.ellipse([cx-7, cy, cx+7, cy+14], fill=(128, 0, 128))
        elif shape_name == "CROWN":
            draw.rectangle([cx-20, cy+10, cx+20, cy+18], fill=(220, 20, 60))
            draw.polygon([(cx-20, cy+10), (cx-20, cy-15), (cx-10, cy), (cx, cy-22), (cx+10, cy), (cx+20, cy-15), (cx+20, cy+10)], fill=(212, 175, 55))

    shapes = ["CHERRY", "BELL", "DIAMOND", "SEVEN", "CLOVER", "STAR", "WATERMELON", "LEMON", "GRAPE", "CROWN"]
    icons_discord = {
        "CHERRY": "🍒", "BELL": "🔔", "DIAMOND": "💎", "SEVEN": "7️⃣", "CLOVER": "🍀",
        "STAR": "⭐", "WATERMELON": "🍉", "LEMON": "🍋", "GRAPE": "🍇", "CROWN": "👑"
    }
    
    win_boost_level = USER_DATA[user_id]["upgrades"].get("slots_winboost", 0)
    win_chance_boost = min(win_boost_level * 0.002, 0.4)
    
    if random.random() < (0.15 + win_chance_boost):
        symbol = random.choice(shapes)
        final_reel1, final_reel2, final_reel3 = symbol, symbol, symbol
    else:
        final_reel1 = random.choice(shapes)
        final_reel2 = random.choice(shapes)
        final_reel3 = random.choice(shapes)

    won = False
    payout_multiplier = 0
    if final_reel1 == final_reel2 == final_reel3:
        won = True
        if final_reel1 == "SEVEN": payout_multiplier = 200
        elif final_reel1 == "CROWN": payout_multiplier = 150
        elif final_reel1 == "STAR": payout_multiplier = 100
        elif final_reel1 == "DIAMOND": payout_multiplier = 75
        elif final_reel1 == "CLOVER": payout_multiplier = 50
        elif final_reel1 == "BELL": payout_multiplier = 30
        else: payout_multiplier = 20
    elif final_reel1 == final_reel2 or final_reel2 == final_reel3 or final_reel1 == final_reel3:
        won = True
        payout_multiplier = 2

    frames = []
    total_frames = 26
    for f in range(total_frames):
        frame = Image.new("RGB", (440, 180), color=(24, 24, 24))
        draw = ImageDraw.Draw(frame)
        draw.rectangle([10, 10, 430, 170], outline=(184, 134, 11), width=6)
        draw.rectangle([15, 15, 425, 165], outline=(212, 175, 55), width=2)
        draw.line([20, 90, 420, 90], fill=(255, 0, 0), width=2)
        for idx, final_shape in enumerate([final_reel1, final_reel2, final_reel3]):
            x_left = 35 + (idx * 130)
            draw.rectangle([x_left, 25, x_left + 110, 155], fill=(10, 10, 10), outline=(70, 70, 70), width=3)
            stop_frame = 12 + (idx * 5)
            if f >= stop_frame:
                draw_custom_shape(draw, final_shape, x_left + 55, 90)
            else:
                shift_offset = (f * 40) % 100
                shape_p = shapes[(f + idx) % len(shapes)]
                shape_n = shapes[(f + idx + 1) % len(shapes)]
                draw_custom_shape(draw, shape_p, x_left + 55, 40 + shift_offset)
                draw_custom_shape(draw, shape_n, x_left + 55, 140 + shift_offset)
        frames.append(frame)

    final_frame = frames[-1]
    for _ in range(20): frames.append(final_frame)
    processed_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE) for f in frames]
    final_buffer = io.BytesIO()
    processed_frames[0].save(final_buffer, format="GIF", save_all=True, append_images=processed_frames[1:], duration=80, optimize=True)
    final_buffer.seek(0)
    file = discord.File(fp=final_buffer, filename="slots.gif")

    reel_display = f"{icons_discord[final_reel1]} | {icons_discord[final_reel2]} | {icons_discord[final_reel3]}"
    if won:
        base_gain = bet_amount * payout_multiplier
        slots_level = USER_DATA[user_id]["upgrades"].get("slots_boost", 0)
        net_gain = int(base_gain * (1 + (slots_level * 0.05)))
        USER_DATA[user_id]["balance"] += net_gain
        USER_DATA[user_id]["net_earnings"] += net_gain
        USER_DATA[user_id]["wins"] += 1
        result_color = 0x00ff00
        outcome_statement = f"🎉 **JACKPOT!** 🎉\n\nYou lined up matching symbols!\nResult: **{reel_display}**\nYou won **${net_gain:,}** chips."
    else:
        USER_DATA[user_id]["balance"] -= bet_amount
        USER_DATA[user_id]["net_earnings"] -= bet_amount
        result_color = 0xff0000
        outcome_statement = f"😭 **Bust!** 😭\n\nThe reels didn't sync up.\nResult: **{reel_display}**\nYou lost **${bet_amount:,}** chips."

    await save_user_data()
    embed = discord.Embed(title="🎰 Slot Machine Results 🎰", color=result_color)
    embed.add_field(name="📊 Result", value=outcome_statement, inline=False)
    embed.add_field(name="💵 Updated Balance", value=f"**{USER_DATA[user_id]['balance']:,}** chips", inline=False)
    embed.set_image(url="attachment://slots.gif")
    await ctx.send(file=file, embed=embed)


@bot.command()
async def servers(ctx):
    embed = discord.Embed(
        title="🌐 Server Count",
        description=f"The bot is currently in {len(bot.guilds)} servers.",
        color=0x5865F2
    )
    await ctx.send(embed=embed)

load_all_data()
bot.run("MTUxNjY3MjUzMTI1MDI4NjYyMg.Goo4NP.CbnG2MloaYjD4X17OqHrH9iyhz4u0L0bl4CM9I")
