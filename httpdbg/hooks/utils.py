def can_set_hook(hclass, hmethod, horiginal):
    """Check if we can set a hook if it not already exists.

    Args:
        hclass (class): The class which contains the method to hook
        hmethod (str): The name of the method to hook
        horiginal (str): The name of the backup of the method to hook

    Returns:
        bool: True if we can set hook
    """
    if not hasattr(
        hclass,
        horiginal,
    ):
        # retrieve the original method
        original_method = getattr(
            hclass,
            hmethod,
        )

        # backup the original method
        setattr(hclass, horiginal, original_method)

        return True
    else:
        return False


def unset_hook(hclass, hmethod, horiginal):
    """Remove the hook if it exists.

    Args:
        hclass (class): The class which contains the hooked method
        hmethod (str): The name of the hooked method
        horiginal (str): The name of the original version of the hooked method
    """

    if hasattr(
        hclass,
        horiginal,
    ):
        # retrieve the original method
        original_method = getattr(
            hclass,
            horiginal,
        )

        # point the hooked method to the original method
        setattr(hclass, hmethod, original_method)

        # delete the backup (the ref) of the original method
        delattr(
            hclass,
            horiginal,
        )
