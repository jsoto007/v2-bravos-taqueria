import os

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request, make_response, render_template, send_from_directory
from jinja2 import TemplateNotFound
from flask_migrate import Migrate
from flask_restful import Api, Resource
from flask_cors import CORS

from models import db, Bird

app = Flask(
    __name__,
    static_url_path='',
    static_folder='../client/build',
    template_folder='../client/build'
)

# Enable CORS for client ↔ server requests (credentials allow session cookies)
CORS(app, supports_credentials=True)

# Long-cache for fingerprinted static assets; API/HTML handled below
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000  # 1 year

# Support both SQLALCHEMY_DATABASE_URI and DATABASE_URI env vars
db_uri = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False


# Ensure db is initialized before migrate
db.init_app(app)
migrate = Migrate(app, db)

# -------- Caching policy (static vs API vs HTML) -------- #
@app.after_request
def add_cache_headers(resp):
    # Normalize path
    p = (request.path or "").lower()

    # Treat JSON responses as API: never cache in the browser
    if (resp.mimetype or "").startswith("application/json") or p.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
        return resp

    # HTML shell (including SPA fallback via the 404->index.html render)
    if (resp.mimetype or "").startswith("text/html"):
        resp.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
        return resp

    # Static assets: cache for a year (hashed filenames are safe to cache immutably)
    if p.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".woff2", ".ttf")):
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp

    return resp


# Simple root route
@app.get('/')
def root_ok():
    return 'API is running', 200

# Minimal favicon handler
@app.get('/favicon.ico')
def favicon():
    static_dir = app.static_folder or os.path.join(os.path.dirname(__file__), 'static')
    icon_path = os.path.join(static_dir or '', 'favicon.ico')
    if os.path.exists(icon_path):
        return send_from_directory(static_dir, 'favicon.ico')
    return '', 204

@app.errorhandler(404)
def not_found(e):
    try:
        return render_template("index.html")
    except TemplateNotFound:
        return make_response(jsonify({
            'error': 'Not Found',
            'message': 'No matching route and no index.html present to serve.'
        }), 404)

api = Api(app)

class Birds(Resource):

    def get(self):
        birds = [bird.to_dict() for bird in Bird.query.all()]
        return make_response(jsonify(birds), 200)

    def post(self):

        data = request.get_json()

        new_bird = Bird(
            name=data['name'],
            species=data['species'],
            image=data['image'],
        )

        db.session.add(new_bird)
        db.session.commit()

        return make_response(new_bird.to_dict(), 201)

api.add_resource(Birds, '/api/birds')

class BirdByID(Resource):
    
    def get(self, id):
        bird = Bird.query.filter_by(id=id).first().to_dict()
        return make_response(jsonify(bird), 200)

    def patch(self, id):

        data = request.get_json()

        bird = Bird.query.filter_by(id=id).first()

        for attr in data:
            setattr(bird, attr, data[attr])

        db.session.add(bird)
        db.session.commit()

        return make_response(bird.to_dict(), 200)

    def delete(self, id):

        bird = Bird.query.filter_by(id=id).first()
        db.session.delete(bird)
        db.session.commit()

        return make_response('', 204)

api.add_resource(BirdByID, '/birds/<int:id>')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5555)))

