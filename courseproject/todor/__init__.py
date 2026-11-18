import os
from ipaddress import IPv6Address, ip_address

from flask import Flask, abort, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_mapping(
        DEBUG=os.environ.get("FLASK_DEBUG", "0") == "1",
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-not-for-production"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///todolist.db"),
        AUTHZ_MODE="rbac",
    )
    if config:
        app.config.update(config)
    if app.config['AUTHZ_MODE'] not in {'rbac', 'baseline'}:
        raise ValueError("AUTHZ_MODE must be 'rbac' or 'baseline'")

    db.init_app(app)

    from . import todo
    app.register_blueprint(todo.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    @app.before_request
    def restrict_baseline_to_loopback():
        if app.config['AUTHZ_MODE'] != 'baseline':
            return
        try:
            address = ip_address(request.remote_addr or '')
        except ValueError:
            abort(404)
        is_loopback = address.is_loopback
        if isinstance(address, IPv6Address) and address.ipv4_mapped:
            is_loopback = address.ipv4_mapped.is_loopback
        if not is_loopback:
            abort(404)

    @app.route('/')
    def index():
        """Render the public landing page."""
        return render_template('index.html')

    with app.app_context():
        db.create_all()
        from .models import User

        columns = {column['name'] for column in inspect(db.engine).get_columns(User.__tablename__)}
        if 'role' not in columns:
            with db.engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE user ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                ))

    return app
