"""PHANTOM SHIELD - Flask application entry point."""
from flask import Flask, jsonify, render_template

import config
from automata import get_automata
from routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES + 64 * 1024
    get_automata()                      # build NFA + DFA once at start-up
    register_routes(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"ok": False, "error": "Not found."}), 404

    @app.errorhandler(405)
    def bad_method(_):
        return jsonify({"ok": False, "error": "Method not allowed."}), 405

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"ok": False, "error": "Upload too large."}), 413

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"ok": False, "error": "Internal server error."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    print(f"PHANTOM SHIELD running at http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
