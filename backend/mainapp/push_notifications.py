from webpush import send_user_notification

def send_push_notification(user):
    """ Send a push notification when motion is detected """
    payload = {
        "head": "Motion Alert 🚨",
        "body": "Motion detected in your birdhouse!",
        "icon": "/static/img/motion_alert.png",
    }
    send_user_notification(user=user, payload=payload, ttl=1000)
