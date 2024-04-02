TELEGRAM_START_MESSAGE = """
Hello, {}!

I will help you book a room!
To see my command catalog, click the button *<<See commands>>* or type /help
"""

COMMAND_CATALOG = """
*/help* - Displays the list of commands

*/show_available_rooms* - Finds available rooms with specified filters and sorts the list if necessary

*/book_room* - Reserves the selected room for the chosen time or alerts if it's already booked

*/cancel_booking* - Cancels a booking if your plans have changed

*/register* - Helps you register in the system (commands book_number and cancel_booking are available only for authorized users)

*/login* - If you are registered in our system, you need to log in with your Telegram account to unlock full functionality

*/logout* - Logs out of the user account
"""
