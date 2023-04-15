import db


def stop(update, context):
    if db.get_user(update.message.from_user.id) is None:
        update.message \
            .reply_text("You are not receiving notifications. Send your location to start receiving notifications.")
    else:
        db.remove_user(update.message.from_user.id)
        update.message \
            .reply_text("Notifications stopped. Send your location again to start receiving notifications again.")
