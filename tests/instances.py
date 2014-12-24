import os
import time

from flask import Flask
from flask.ext.celery import Celery, single_instance
from flask.ext.redis import Redis
from flask.ext.sqlalchemy import SQLAlchemy


def generate_config():
    """Generates a Flask config dict with settings for a specific broker based on an environment variable.

    To be merged into app.config.

    Returns:
    A dict to be fed into app.config.update().
    """
    config = dict()

    if os.environ.get('BROKER') == 'rabbit':
        config['CELERY_BROKER_URL'] = 'amqp://user:pass@localhost//'
    elif os.environ.get('BROKER') == 'redis':
        config['REDIS_URL'] = 'redis://localhost/1'
        config['CELERY_BROKER_URL'] = config['REDIS_URL']
    elif os.environ.get('BROKER', '').startswith('redis_sock,'):
        config['REDIS_URL'] = 'redis+socket://' + os.environ['BROKER'].split(',', 1)[1]
        config['CELERY_BROKER_URL'] = config['REDIS_URL']
    elif os.environ.get('BROKER') == 'mongo':
        config['CELERY_BROKER_URL'] = 'mongodb://user:pass@localhost/test'
    elif os.environ.get('BROKER') == 'couch':
        config['CELERY_BROKER_URL'] = 'couchdb://user:pass@localhost/test'
    elif os.environ.get('BROKER') == 'beanstalk':
        config['CELERY_BROKER_URL'] = 'beanstalk://user:pass@localhost/test'
    elif os.environ.get('BROKER') == 'iron':
        config['CELERY_BROKER_URL'] = 'ironmq://project:token@/test'
    else:
        if os.environ.get('BROKER') == 'mysql':
            config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/test'
        elif os.environ.get('BROKER') == 'postgres':
            config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/test'
        else:
            config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_database.sqlite'
        config['CELERY_BROKER_URL'] = 'sqla+' + config['SQLALCHEMY_DATABASE_URI']
        config['CELERY_RESULT_BACKEND'] = 'db+' + config['SQLALCHEMY_DATABASE_URI']

    if 'CELERY_BROKER_URL' in config and 'CELERY_RESULT_BACKEND' not in config:
        config['CELERY_RESULT_BACKEND'] = config['CELERY_BROKER_URL']

    return config


def generate_context(config):
    """Creates the Flask app context and initializes any extensions such as Celery, Redis, SQLAlchemy, etc.

    Positional arguments:
    config -- partial Flask config dict from generate_config().

    Returns:
    The Flask app instance.
    """
    flask_app = Flask(__name__)
    flask_app.config.update(config)
    flask_app.config['TESTING'] = True
    Celery(flask_app)

    if 'SQLALCHEMY_DATABASE_URI' in flask_app.config:
        db = SQLAlchemy(flask_app)
        db.create_all()
    elif 'REDIS_URL' in flask_app.config:
        Redis(flask_app)

    return flask_app


def get_flask_celery_apps():
    """Calls generate_context() and generate_config().

    Returns:
    Tuple, first item is the Flask app instance, second is the Celery app instance.
    """
    config = generate_config()
    flask_app = generate_context(config=config)
    celery_app = flask_app.extensions['celery'].celery
    return flask_app, celery_app


app, celery = get_flask_celery_apps()


@celery.task(bind=True)
@single_instance
def add(x, y):
    return x + y


@celery.task(bind=True)
@single_instance(include_args=True)
def mul(x, y):
    return x * y


@celery.task(bind=True)
@single_instance
def sub(x, y):
    time.sleep(1)
    return x + y