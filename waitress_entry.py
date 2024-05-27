from waitress import serve
from crm1.wsgi import (
    application,
)  # Replace 'your_project.wsgi' with your actual WSGI application

if __name__ == "__main__":
    serve(application, host="0.0.0.0", port=80)  # Adjust host and port as needed
