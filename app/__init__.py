import os
from flask import Flask
from flask_smorest import Api
from flask_cors import CORS

from .config import Config
from .extensions import db, jwt, migrate

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa

    api = Api(app)

    from .api.auth_routes import blp as AuthBLP
    from .api.startup_routes import blp as StartupBLP
    from .api.post_routes import blp as PostBLP
    from .api.notification_routes import blp as NotificationBLP
    from .api.hub_routes import blp as HubBLP
    from .api.fx_routes import blp as FxBLP
    from .api.contract_routes import blp as ContractBLP
    from .api.task_routes import blp as TaskBLP
    from .api.calendar_routes import blp as CalendarBLP
    from .api.scoring_routes import blp as ScoringBLP
    
    api.register_blueprint(AuthBLP, url_prefix="/api")
    api.register_blueprint(StartupBLP, url_prefix="/api")
    api.register_blueprint(PostBLP, url_prefix="/api")
    api.register_blueprint(NotificationBLP, url_prefix="/api")
    api.register_blueprint(HubBLP, url_prefix="/api")
    api.register_blueprint(ContractBLP, url_prefix="/api")
    api.register_blueprint(FxBLP, url_prefix="/api")
    api.register_blueprint(TaskBLP, url_prefix="/api")
    api.register_blueprint(CalendarBLP, url_prefix="/api")
    api.register_blueprint(ScoringBLP, url_prefix="/api/scoring")
    
    
    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    from .seed.cli import seed_blp
    app.register_blueprint(seed_blp)

    return app
