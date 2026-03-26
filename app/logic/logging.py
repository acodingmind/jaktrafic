from __future__ import annotations

from datetime import datetime, timezone
import uuid

from flask import Flask, Response, current_app, g, jsonify, request
from werkzeug.exceptions import HTTPException

from app.logic.feed_status import FeedStatusError
from app.logic.gtfs_loader import GtfsSourceError
from app.logic.service_calendar import ServiceCalendarError
from app.logic.validators import RequestValidationError


def register_request_logging(app: Flask) -> None:
    @app.before_request
    def track_request_start() -> None:
        g.request_started_at = datetime.now(timezone.utc)
        g.request_id = uuid.uuid4().hex[:12]

    @app.after_request
    def log_request(response: Response) -> Response:
        if not current_app.config.get("LOG_ALL_REQUESTS", False):
            return response

        started_at = getattr(g, "request_started_at", None)
        duration_ms = None
        if started_at is not None:
            duration_ms = round((datetime.now(timezone.utc) - started_at).total_seconds() * 1000, 2)

        current_app.logger.info(
            "request_completed request_id=%s method=%s route=%s endpoint=%s status=%s duration_ms=%s",
            getattr(g, "request_id", "unknown"),
            request.method,
            _get_safe_route(),
            request.endpoint or "unknown",
            response.status_code,
            duration_ms if duration_ms is not None else "unknown",
        )
        return response


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(RequestValidationError)
    def handle_request_validation_error(error: RequestValidationError):
        _log_error("validation_failed", error)
        payload = {
            "error": "bad_request",
            "message": str(error),
        }
        if error.field_name:
            payload["field"] = error.field_name
        return _make_error_response(payload, status_code=400)

    @app.errorhandler(GtfsSourceError)
    @app.errorhandler(ServiceCalendarError)
    @app.errorhandler(FeedStatusError)
    def handle_feed_processing_error(error: Exception):
        _log_error("feed_processing_failed", error)
        return _make_error_response(
            {
                "error": "service_unavailable",
                "message": "Transit data is unavailable or invalid. Please try again later.",
            },
            status_code=503,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        _log_error("http_exception", error)
        return _make_error_response(
            {
                "error": error.name.lower().replace(" ", "_"),
                "message": error.description,
            },
            status_code=error.code or 500,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        _log_error("unhandled_exception", error, include_stack=True)
        return _make_error_response(
            {
                "error": "internal_server_error",
                "message": "An unexpected error occurred while processing the request.",
            },
            status_code=500,
        )


def _make_error_response(payload: dict[str, str], *, status_code: int):
    if _prefers_json_response():
        return jsonify(payload), status_code

    body = (
        "<!doctype html>"
        "<html lang='en'><head><meta charset='utf-8'><title>JakTrafic Error</title></head>"
        "<body><main>"
        f"<h1>{payload['message']}</h1>"
        "<p>Please adjust your input and try again.</p>"
        "</main></body></html>"
    )
    return Response(body, status=status_code, mimetype="text/html")


def _prefers_json_response() -> bool:
    if request.blueprint == "api_v1":
        return True
    if request.path.startswith("/api/") or request.path.startswith("/lapi/"):
        return True
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json" and request.accept_mimetypes[best] > request.accept_mimetypes["text/html"]


def _get_safe_route() -> str:
    if request.url_rule is not None:
        return request.url_rule.rule
    return request.path


def _log_error(event_name: str, error: Exception, *, include_stack: bool = False) -> None:
    logger = current_app.logger
    message = "%s request_id=%s route=%s endpoint=%s error_type=%s message=%s"
    args = (
        event_name,
        getattr(g, "request_id", "unknown"),
        _get_safe_route(),
        request.endpoint or "unknown",
        error.__class__.__name__,
        str(error),
    )
    if include_stack:
        logger.exception(message, *args)
    else:
        logger.warning(message, *args)


__all__ = ["register_error_handlers", "register_request_logging"]