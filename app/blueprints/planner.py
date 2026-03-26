from flask import Blueprint

bp = Blueprint("planner", __name__, url_prefix="/planner")


@bp.get("/")
def index():
    return "Planner stub"
