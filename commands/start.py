import db


def start(update, context):
    if db.get_user(update.message.from_user.id) is None:
        update.message \
            .reply_text("Send your location to start receiving notifications about flights over your location.")
    else:
        update.message \
            .reply_text("You are already receiving notifications. Send /stop to stop receiving notifications.")
