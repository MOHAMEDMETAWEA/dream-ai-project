"""
Dream AI Analysis System - Backend (Flask)
EEC10212 Integrated Project 1 - National University
Team: Zayana (230391), Noor (230393), Maram (230376), Reem (230390)

This is the main Flask application file. It handles all the API routes,
user authentication, and connects the frontend to the AI model and database.

We're using Flask because it's lightweight and we all had some exposure to it.
We considered FastAPI but Flask's session management was easier for us to work with
given our time constraints.
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import UTC, datetime, timedelta
from ai_model import analyse_emotion, detect_patterns, extract_keywords
from extensions import db
from password_utils import hash_password, verify_password

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))
DATABASE_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'database', 'dreams.db'))

# --- App setup ---
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db.init_app(app)
CORS(app, supports_credentials=True)

# We import the models down here to avoid circular imports
from models import User, Dream, AnalysisResult


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_user():
    """Check if user is logged in and return user object, or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(f):
    """Simple decorator to protect routes that need authentication."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return jsonify({'error': 'Please log in to continue.'}), 401
        return f(*args, **kwargs)
    return decorated


def _dream_created_at(dream, analysis=None):
    """Prefer dream.created_at, then analysis time, then current time."""
    if getattr(dream, 'created_at', None):
        return dream.created_at
    if analysis and getattr(analysis, 'analysed_at', None):
        return analysis.analysed_at
    return datetime.now(UTC).replace(tzinfo=None)


# ============================================================
# SERVE FRONTEND
# ============================================================

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/api/register', methods=['POST'])
def register():
    """Create a new user account."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    # Basic validation - not perfect but catches the obvious stuff
    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters.'}), 400
    if not password or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400

    # Check if username taken
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'That username is already taken.'}), 409

    # Hash the password with bcrypt (cost factor 12)
    hashed_pw = hash_password(password)

    new_user = User(username=username, email=email, password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    # Log them in right away
    session['user_id'] = new_user.id
    session.permanent = True

    return jsonify({'message': 'Account created successfully!', 'username': username}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate an existing user."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    user = User.query.filter_by(username=username).first()

    # Important: we check hash, never compare plaintext passwords directly
    if not user or not verify_password(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    session['user_id'] = user.id
    session.permanent = True
    return jsonify({'message': 'Logged in!', 'username': user.username}), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """Clear session."""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out.'}), 200


@app.route('/api/me', methods=['GET'])
@login_required
def me():
    """Return current user info."""
    user = get_current_user()
    return jsonify({'username': user.username, 'email': user.email,
                    'joined': user.created_at.isoformat()}), 200


# ============================================================
# DREAM ROUTES
# ============================================================

@app.route('/api/dreams', methods=['POST'])
@login_required
def submit_dream():
    """
    Receive a new dream entry, run AI analysis, store everything.
    This is the core endpoint of the whole project.
    """
    user = get_current_user()
    data = request.get_json()
    dream_text = data.get('text', '').strip()
    title = data.get('title', '').strip() or 'Untitled Dream'

    if len(dream_text) < 10:
        return jsonify({'error': 'Please describe your dream in more detail (at least 10 characters).'}), 400
    if len(dream_text) > 5000:
        return jsonify({'error': 'Dream text is too long (maximum 5000 characters).'}), 400

    # Save the dream first
    new_dream = Dream(user_id=user.id, title=title, content=dream_text)
    db.session.add(new_dream)
    db.session.flush()  # Get the ID without full commit

    # Run AI analysis
    try:
        emotion_label, confidence = analyse_emotion(dream_text)
    except Exception as e:
        # If the model fails for some reason, we still save the dream
        # but flag the analysis as unavailable
        emotion_label = 'unknown'
        confidence = 0.0
        print(f"AI analysis error: {e}")

    try:
        keywords = extract_keywords(dream_text)
    except Exception as e:
        keywords = []
        print(f"Keyword extraction error: {e}")

    # Save analysis result
    analysis = AnalysisResult(
        dream_id=new_dream.id,
        emotion=emotion_label,
        confidence=round(confidence, 3),
        keywords=json.dumps(keywords)
    )
    db.session.add(analysis)
    db.session.commit()

    return jsonify({
        'dream_id': new_dream.id,
        'emotion': emotion_label,
        'confidence': round(confidence * 100, 1),
        'message': 'Dream analysed successfully!'
    }), 201


@app.route('/api/dreams', methods=['GET'])
@login_required
def get_dreams():
    """Get all dreams for the current user, newest first."""
    user = get_current_user()
    dreams = Dream.query.filter_by(user_id=user.id).order_by(Dream.created_at.desc()).all()

    result = []
    for dream in dreams:
        analysis = AnalysisResult.query.filter_by(dream_id=dream.id).first()
        created_at = _dream_created_at(dream, analysis)
        result.append({
            'id': dream.id,
            'title': dream.title,
            'content': dream.content[:200] + '...' if len(dream.content) > 200 else dream.content,
            'created_at': created_at.isoformat(),
            'emotion': analysis.emotion if analysis else 'pending',
            'confidence': round(analysis.confidence * 100, 1) if analysis else 0
        })

    return jsonify(result), 200


@app.route('/api/dreams/<int:dream_id>', methods=['GET'])
@login_required
def get_dream(dream_id):
    """Get a single dream with full text and analysis."""
    user = get_current_user()
    dream = Dream.query.filter_by(id=dream_id, user_id=user.id).first()

    if not dream:
        return jsonify({'error': 'Dream not found.'}), 404

    analysis = AnalysisResult.query.filter_by(dream_id=dream.id).first()
    created_at = _dream_created_at(dream, analysis)

    return jsonify({
        'id': dream.id,
        'title': dream.title,
        'content': dream.content,
        'created_at': created_at.isoformat(),
        'emotion': analysis.emotion if analysis else 'unknown',
        'confidence': round(analysis.confidence * 100, 1) if analysis else 0,
        'keywords': json.loads(analysis.keywords) if analysis and analysis.keywords else []
    }), 200


@app.route('/api/dreams/<int:dream_id>', methods=['DELETE'])
@login_required
def delete_dream(dream_id):
    """Delete a dream and its analysis."""
    user = get_current_user()
    dream = Dream.query.filter_by(id=dream_id, user_id=user.id).first()

    if not dream:
        return jsonify({'error': 'Dream not found.'}), 404

    # Cascade delete analysis results too
    AnalysisResult.query.filter_by(dream_id=dream.id).delete()
    db.session.delete(dream)
    db.session.commit()

    return jsonify({'message': 'Dream deleted.'}), 200


# ============================================================
# DASHBOARD / ANALYTICS ROUTES
# ============================================================

@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    """
    Return aggregated stats for the user's dashboard.
    Includes: emotion distribution (last 30 days), recurring patterns,
    total dream count, and streak info.
    """
    user = get_current_user()

    # Get dreams from last 30 days
    thirty_days_ago = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=30)
    all_dreams = Dream.query.filter_by(user_id=user.id).all()

    recent_dreams = []
    for dream in all_dreams:
        analysis = AnalysisResult.query.filter_by(dream_id=dream.id).first()
        created_at = _dream_created_at(dream, analysis)
        if created_at >= thirty_days_ago:
            recent_dreams.append((dream, analysis, created_at))

    # Count emotions
    emotion_counts = {}
    for dream, analysis, _created_at in recent_dreams:
        if analysis and analysis.emotion != 'unknown':
            emotion = analysis.emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

    # Get recurring patterns from ALL user dreams
    all_texts = [d.content for d in all_dreams]
    patterns = detect_patterns(all_texts) if len(all_texts) >= 2 else []

    # Timeline data (last 14 days, one entry per day)
    timeline = []
    for i in range(13, -1, -1):
        day = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=i)
        day_dreams = []
        for dream in all_dreams:
            analysis = AnalysisResult.query.filter_by(dream_id=dream.id).first()
            created_at = _dream_created_at(dream, analysis)
            if created_at.date() == day.date():
                day_dreams.append(dream)
        timeline.append({
            'date': day.strftime('%d %b'),
            'count': len(day_dreams)
        })

    return jsonify({
        'total_dreams': len(all_dreams),
        'emotion_distribution': emotion_counts,
        'recurring_patterns': patterns[:8],  # top 8 patterns
        'timeline': timeline
    }), 200


@app.route('/api/export', methods=['GET'])
@login_required
def export_data():
    """Allow user to export all their data as JSON."""
    user = get_current_user()
    all_dreams = Dream.query.filter_by(user_id=user.id).all()

    export = {
        'exported_at': datetime.now(UTC).replace(tzinfo=None).isoformat(),
        'username': user.username,
        'dreams': []
    }
    for dream in all_dreams:
        analysis = AnalysisResult.query.filter_by(dream_id=dream.id).first()
        created_at = _dream_created_at(dream, analysis)
        export['dreams'].append({
            'title': dream.title,
            'content': dream.content,
            'date': created_at.isoformat(),
            'emotion': analysis.emotion if analysis else 'unknown',
            'confidence': analysis.confidence if analysis else 0,
        })

    return jsonify(export), 200


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created/verified.")
    app.run(debug=True, use_reloader=False, port=5000)
