from flask import Flask, request, make_response

app = Flask(__name__)
app.logger.setLevel('INFO')

@app.route('/', methods=['GET', 'POST'])
def entry():
    """
    This function is the main entry point for the Flask app.
    Passes the request to the handler function to execute user logic.
    """
    app.logger.info(f"Received request: {request}")

    return handler(request)


@app.route('/healthz', methods=['GET'])
def health_check():
    """
    This function is the health check endpoint.
    It returns a 200 OK response to indicate that the service is healthy.
    """
    return make_response("OK", 200)


def handler(ctx: request):
    """
    This function is the entry point for the function.
    It will be invoked by the FaaS platform.
    """
    
    return {
        "statusCode": 200,
        "message": "Hello World"
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)