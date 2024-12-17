from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from globals import AuthU
# Global variable to store authorized user IDs as a comma-separated string

OWNER = Config.OWNER
# Helper function to check if user is authorized
def is_authorized(user_id: int) -> bool:
    return str(user_id) in AuthU.split(",")

# Command to add a user ID to AuthU
@Client.on_message(filters.command("addauth"))
async def add_auth(client, message: Message):
    global AuthU  # Access the global AuthU variable
    args = message.text.split(" ", 1)  # Split command and argument

    # Check if user is authorized to add IDs
    if str(message.from_user.id) not in OWNER:
        await message.reply("❌ You are not authorized to add users!")
        return

    # Ensure the command has an ID argument
    if len(args) < 2:
        await message.reply("⚠️ Usage: `/addauth userid`")
        return

    new_id = args[1].strip()
    if not new_id.isdigit():
        await message.reply("⚠️ Please provide a valid numeric Telegram ID.")
        return

    # Add the new ID to AuthU if not already added
    if new_id in AuthU.split(","):
        await message.reply(f"✅ User ID `{new_id}` is already authorized.")
    else:
        AuthU += f",{new_id}" if AuthU else new_id
        await message.reply(f"✅ User ID `{new_id}` has been added to the authorized list.")

# Command to remove a user ID from AuthU
@Client.on_message(filters.command("removeauth"))
async def remove_auth(client, message: Message):
    global AuthU
    args = message.text.split(" ", 1)

    # Check if user is authorized to remove IDs
    if str(message.from_user.id) not in OWNER:
        await message.reply("❌ You are not authorized to remove users!")
        return

    # Ensure the command has an ID argument
    if len(args) < 2:
        await message.reply("⚠️ Usage: `/removeauth userid`")
        return

    remove_id = args[1].strip()
    if not remove_id.isdigit():
        await message.reply("⚠️ Please provide a valid numeric Telegram ID.")
        return

    # Remove the ID from AuthU if it exists
    auth_list = AuthU.split(",")
    if remove_id in auth_list:
        auth_list.remove(remove_id)
        AuthU = ",".join(auth_list)
        await message.reply(f"✅ User ID `{remove_id}` has been removed from the authorized list.")
    else:
        await message.reply(f"❌ User ID `{remove_id}` is not in the authorized list.")

# Command to view the current authorized list
@Client.on_message(filters.command("listauth"))
async def list_auth(client, message: Message):
    if str(message.from_user.id) not in OWNER:
      await message.reply("❌ You are not authorized to view the list!")
      return

    global AuthU
    auth_list = AuthU.split(",")
    auth_text = "\n".join([f"🔹 `{user_id}` - [User](tg://user?id={user_id})" for user_id in auth_list])
    await message.reply(f"**🔐 Authorized User IDs:**\n\n{auth_text}")

@Client.on_message(filters.command("checkauth"))
async def check_auth(client, message: Message):
    if str(message.from_user.id) not in OWNER:
      await message.reply("❌ You are not authorized to view the list!")
      return

    global AuthU
    await message.reply(f"**🔐 Authorized User IDs:**\n\n{AuthU}")



