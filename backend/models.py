"""
Database Models - Dream AI System
Using Flask-SQLAlchemy ORM.
Reem designed the schema, Zayana reviewed it.

We went through a few iterations of this schema. The first version
jammed everything into two tables, which caused JOIN problems when
querying the dashboard. Three tables is cleaner.
"""

from datetime import UTC, datetime
from extensions import db


def utc_now():
    """Return a naive UTC datetime without using deprecated utcnow()."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)  # email optional
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationship: one user -> many dreams
    dreams = db.relationship('Dream', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class Dream(db.Model):
    __tablename__ = 'dreams'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), default='Untitled Dream')
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)

    # One dream -> one analysis result (one-to-one)
    analysis = db.relationship('AnalysisResult', backref='dream', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Dream {self.id}: {self.title[:30]}>'


class AnalysisResult(db.Model):
    """
    Separate table for analysis results. This way if we update the model later,
    we can re-run analysis without losing the original dream text.
    Reem's idea and it was a good one.
    """
    __tablename__ = 'analysis_results'

    id = db.Column(db.Integer, primary_key=True)
    dream_id = db.Column(db.Integer, db.ForeignKey('dreams.id'), nullable=False, unique=True)
    emotion = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    keywords = db.Column(db.Text, default='[]')  # JSON-serialised list of strings
    analysed_at = db.Column(db.DateTime, default=utc_now)

    def __repr__(self):
        return f'<Analysis dream_id={self.dream_id} emotion={self.emotion} conf={self.confidence:.2f}>'
