import telebot
import os
import json
import logging


bot = telebot.TeleBot(
    token=os.getenv('BOT_TOKEN'),
    threaded = False
)

# Temporary storage for orders (consider using a database for production)
orders = {}
menu = {
    'cakes': [
        {'name': 'Chocolate Cake', 'price': '$20'},
        {'name': 'Chocolate Cake'},
        {'name': 'Chocolate Cake'},
        {'name': 'Chocolate Cake'},
        {'name': 'Chocolate Cake'},
    ]
}

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#TODO:
# Add functions to change menu
# Add function to show order to customer
# Add function to text customer when order status changes

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Jiggly Puff Cake Store!\nUse /menu to see our cakes or /order to place an order.")
    
@bot.message_handler(commands=['menu'])
def show_menu(message):
    menu_text = (
        "Here are our available cakes:\n"
        "1. Chocolate Cake - $20\n"
        "2. Red Velvet Cake - $25\n"
        "3. Vanilla Cake - $18\n"
        "\nUse /order to place an order!"
    )
    bot.send_message(message.chat.id, menu_text)

@bot.message_handler(commands=['order'])
def take_order(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Chocolate Cake', 'Red Velvet Cake', 'Vanilla Cake')
    msg = bot.send_message(message.chat.id, "What cake would you like to order?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_cake_selection)

def process_cake_selection(message):
    chat_id = message.chat.id
    cake = message.text

    if cake not in ['Chocolate Cake', 'Red Velvet Cake', 'Vanilla Cake']:
        bot.send_message(chat_id, "Sorry, I didn't understand that. Please use /order to start again.")
        return

    orders[chat_id] = {'cake': cake}
    msg = bot.send_message(chat_id, "How many would you like to order?")
    bot.register_next_step_handler(msg, process_quantity)

def process_quantity(message):
    chat_id = message.chat.id
    quantity = message.text

    if not quantity.isdigit():
        bot.send_message(chat_id, "Please enter a valid number for the quantity.")
        return

    orders[chat_id]['quantity'] = int(quantity)
    msg = bot.send_message(chat_id, "Please provide your delivery address.")
    bot.register_next_step_handler(msg, process_address)

def process_address(message):
    chat_id = message.chat.id
    address = message.text

    orders[chat_id]['address'] = address
    order_summary = (
        f"Thank you for your order!\n\n"
        f"Cake: {orders[chat_id]['cake']}\n"
        f"Quantity: {orders[chat_id]['quantity']}\n"
        f"Delivery Address: {orders[chat_id]['address']}\n"
        f"\nWe will contact you with updates soon!"
    )
    bot.send_message(chat_id, order_summary)

@bot.message_handler(commands=['update_order'])
def update_order(message):
    chat_id = message.chat.id
    if chat_id not in orders:
        bot.send_message(chat_id, "You don't have any active orders.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Preparing', 'Out for Delivery', 'Delivered')
    msg = bot.send_message(chat_id, "What's the current status of your order?", reply_markup=markup)
    bot.register_next_step_handler(msg, process_status_update)

def process_status_update(message):
    chat_id = message.chat.id
    status = message.text

    if status not in ['Preparing', 'Out for Delivery', 'Delivered']:
        bot.send_message(chat_id, "Invalid status. Please use /update_order to try again.")
        return

    orders[chat_id]['status'] = status
    bot.send_message(chat_id, f"Your order status has been updated to: {status}")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    username = message.chat.username or message.chat.first_name
    reply_text = f"I'm sorry {username} but I'm afraid I can only process a few commands only, why don't you type /help to find out how I can help you out?"
    if not username:
        reply_text = f"I'm sorry but I'm afraid I can only process a few commands only, why don't you type /help to find out how I can help you out?"
    
    bot.reply_to(message, reply_text)

# Lambda handler
def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")  # Log the incoming event for debugging
    try:
        body = json.loads(event['body'])
        json_string = json.dumps(body)
        update = telebot.types.Update.de_json(json_string)
        response = bot.process_new_updates([update])
        return {
            'statusCode': 200,
            'body': json.dumps('Message processed successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }