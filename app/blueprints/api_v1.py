from flask import Blueprint, jsonify

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "jaktrafic"})
