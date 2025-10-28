import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    env = os.environ.get("FLASK_ENV", "development")
    debug = env == "development"
    port = int(os.environ.get("PORT", 5000))

    print(f"🚀 Starting Flask in {env} mode on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
