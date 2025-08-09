from runtime_models import Context, Event, Response


def handler(event: Event, ctx: Context):
    """
    This function is the entry point for the function.
    It will be invoked by the FaaS platform.
    """

    # User logic: can return dict (JSON), (dict, status), or Response()
    return {
        "message": "Hello World",
        "function_id": ctx.function_id,
        "request_id": ctx.request_id,
        "path": event.path,
        "contract": ctx.contract_version,
    }
