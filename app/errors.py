from flask import render_template
from . import app
from app.app_logging import logger



@app.errorhandler(404)
def not_found_error(error):
    logger.error("Not Found Error: 404")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal Error: 500")
    return render_template('500.html'), 500
