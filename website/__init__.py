from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import spacy.cli


db = SQLAlchemy()
DB_NAME = "database.db"


def summarizer(rawdocs):
    stopwords = list(STOP_WORDS)

    # nlp = spacy.cli.download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(rawdocs)

    word_freq = {}
    for word in doc:
        if word.text.lower() not in stopwords and word.text.lower() not in punctuation:
            if word.text not in word_freq.keys():
                word_freq[word.text] = 1
            else:
                word_freq[word.text] += 1

    # Max Frequency
    max_freq = max(word_freq.values())

    # Normalizing the frequency
    for word in word_freq.keys():
        word_freq[word] = word_freq[word]/max_freq

    # Sentence tokenization
    sent_tokens = [sent for sent in doc.sents]

    # Sentence Scores
    sent_scores = {}
    for sent in sent_tokens:
        for word in sent:
            if word.text in word_freq.keys():
                if sent not in sent_scores.keys():
                    sent_scores[sent] = word_freq[word.text]
                else:
                    sent_scores[sent] += word_freq[word.text]

    # Summary things
    select_len = int(len(sent_tokens) * 0.25)
    summary = nlargest(select_len, sent_scores, key = sent_scores.get)
    final_summary = [word.text for word in summary]
    print(final_summary)
    summary = ' '.join(final_summary)

    return summary, doc


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Password'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')