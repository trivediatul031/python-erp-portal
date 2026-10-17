import os
from app import create_app

# Get environment from FLASK_ENV variable, default to development
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # Only use debug mode in development
    debug_mode = config_name == 'development'
    app.run(debug=debug_mode, host='0.0.0.0')
