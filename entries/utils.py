def user_has_subscription(user):
    """Проверяет, есть ли у пользователя активная подписка."""
    if not user.is_authenticated:
        return False
    return getattr(user, "is_paid", False)
