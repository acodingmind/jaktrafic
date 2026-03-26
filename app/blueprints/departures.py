from flask import Blueprint

bp = Blueprint("departures", __name__, url_prefix="/departures")


@bp.get("/")
def index():
    return "Departures stub"
