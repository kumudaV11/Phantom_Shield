"""Route registration."""
from flask import jsonify


def ok(**data):
    return jsonify({"ok": True, **data})


def fail(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def register_routes(app):
    from .scan_routes import bp as scan_bp
    from .automata_routes import bp as automata_bp
    from .benchmark_routes import bp as benchmark_bp
    from .dataset_routes import bp as dataset_bp
    for bp in (scan_bp, automata_bp, benchmark_bp, dataset_bp):
        app.register_blueprint(bp)
