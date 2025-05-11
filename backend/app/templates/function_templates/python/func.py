from flask import Flask, request, make_response
from handler import handler

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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)