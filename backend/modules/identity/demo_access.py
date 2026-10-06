from django.conf import settings

DEMO_GROUP = "mygym_demo_only"


def demo_access_denied(user):
    return (
        user is not None
        and not getattr(settings, "DEMO_ENABLED", False)
        and user.groups.filter(name=DEMO_GROUP).exists()
    )
