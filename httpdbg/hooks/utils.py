# -*- coding: utf-8 -*-
import inspect

from httpdbg.utils import logger


def can_set_hook(hclass, hmethod, records):
    """Check if we can set a hook if it not already exists.

    Args:
        hclass (class): The class which contains the method to hook
        hmethod (str): The name of the method to hook
        records (HTTPRecords): The records

    Returns:
        bool, function: a tuple with two values: (True if we can set hook, the original method)
    """
    horiginal = f"_httpdbg_hook_original_{hmethod}_{records.id}"

    # the original method is backuped once to be reused to inspect call arguments (important for nested hooks)
    _httpdbg_original_method = f"_httpdbg_original_{hmethod}"
    if not hasattr(hclass, _httpdbg_original_method):
        setattr(hclass, _httpdbg_original_method, getattr(hclass, hmethod))

    if not hasattr(
        hclass,
        horiginal,
    ):
        # retrieve the original method (can be itself an hook)
        original_method = getattr(
            hclass,
            hmethod,
        )

        # backup the original method
        setattr(hclass, horiginal, original_method)

        logger.info(
            f"set hook - {original_method.__module__}.{original_method.__qualname__}"
        )

        return True, getattr(hclass, _httpdbg_original_method)
    else:
        return False, getattr(hclass, _httpdbg_original_method)


def unset_hook(hclass, hmethod, records):
    """Remove the hook if it exists.

    Args:
        hclass (class): The class which contains the hooked method
        hmethod (str): The name of the hooked method
        records (HTTPRecords): The records
    """
    horiginal = f"_httpdbg_hook_original_{hmethod}_{records.id}"

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

        logger.debug(
            f"unset hook - {original_method.__module__}.{original_method.__qualname__}"
        )


def getcallargs(original_method, *args, **kwargs):
    try:
        callargs = (
            inspect.signature(original_method).bind_partial(*args, **kwargs).arguments
        )
    except Exception as ex:
        logger.warning(
            f"getcallargs - {original_method.__module__}.{original_method.__qualname__} - args={args} - kwargs={kwargs} - exception={str(ex)}"
        )
        # if an error occurs here, we call the original method with all the arguments
        # to not change the behavior of the hooked method
        original_method(*args, **kwargs)

    callargs.update(kwargs)

    logger.info(
        f"getcallargs - {original_method.__module__}.{original_method.__qualname__} - {[arg for arg in callargs]}"
    )
    return callargs


def set_record(records, record, obj):
    logger.info(f"set_record - {records.id}.{record.id}--{obj}")
    setattr(obj, f"_httpdbg_{records.id}_record_id", record.id)


def get_record(records, obj):
    record = None
    record_id = getattr(obj, f"_httpdbg_{records.id}_record_id", None)
    if record_id:
        record = records.requests[record_id]
    logger.info(f"get_record - {records.id}.{record.id if record else 'not found'}")
    return record
