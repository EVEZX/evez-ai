
    def decorator(func: Callable[[NexusMessage], None]):
        sub_id = subscribe(event_type, func)
        func._nexus_sub_id = sub_id
        return func
    return decorator
