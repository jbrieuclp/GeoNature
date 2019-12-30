import logging

from flask import current_app, jsonify, Response

from pypnusershub.db.tools import InsufficientRightsError
from sqlalchemy.exc import SQLAlchemyError

from utils_flask_sqla.response import json_resp
from utils_flask_sqla.errors import UtilsSqlaError

from geonature.utils.env import DB
from geonature.utils.errors import GeonatureApiError


log = logging.getLogger(__name__)
gunicorn_error_logger = logging.getLogger("gunicorn.error")


@current_app.errorhandler(500)
@json_resp
def internal_error(error):  # pylint: disable=W0613
    gunicorn_error_logger.error(error)
    DB.session.rollback()
    return {"message": "internal server error"}, 500


@current_app.errorhandler(SQLAlchemyError)
@json_resp
def sqlalchemy_error(error):  # pylint: disable=W0613
    gunicorn_error_logger.error(error)
    DB.session.rollback()
    return {"message": "internal server error"}, 500


@current_app.errorhandler(GeonatureApiError)
def geonature_api_error(error):
    gunicorn_error_logger.error(error.to_dict())
    DB.session.rollback()
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@current_app.errorhandler(UtilsSqlaError)
def utils_flask_sql_error(error):
    gunicorn_error_logger.error(error.to_dict())
    DB.session.rollback()
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@current_app.errorhandler(InsufficientRightsError)
def geonature_insuffisant_rights_error(error):
    gunicorn_error_logger.error(error)
    DB.session.rollback()
    response = jsonify(str(error))
    response.status_code = 403
    return response
