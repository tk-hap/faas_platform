def handler(ctx):
    """
    This function is the entry point for the function.
    It will be invoked by the FaaS platform.
    """
    
    return {
        "statusCode": 200,
        "message": "Hello World"
    }