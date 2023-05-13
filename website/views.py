from flask import Blueprint, render_template, request, flash, jsonify, redirect
from flask_login import login_required, current_user
import speech_recognition as sr
from website import summarizer
from .models import Note
from . import db
import json

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note') #Gets the note from the HTML

        if len(note) < 1:
            flash('Note is too short!', category='error')

        # To Summarize the notes, Note lenght have to be more than 100 words
        elif len(note) > 100:
            summary, original_txt = summarizer(note)
            # providing the schema for the note
            new_note_summary = Note(data=summary, user_id=current_user.id)
            # adding the note to the database
            db.session.add(new_note_summary)
            db.session.commit()
            flash(' Note Summarized!', category='success')
            return render_template("summary.html", user=current_user, summary=summary, original_txt=original_txt )

        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route("/speech-recognition", methods=["GET", "POST"])
def index():
    transcript = ""
    if request.method == "POST":

        # If file not exist
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            recognizer = sr.Recognizer()
            audioFile = sr.AudioFile(file)
            with audioFile as source:
                data = recognizer.record(source)
            transcript = recognizer.recognize_google(data, key=None)
            new_note = Note(data=transcript, user_id=current_user.id)  # providing the schema for the note
            db.session.add(new_note)  # adding the note to the database
            db.session.commit()
            flash('Transcribed!', category='success')

    return render_template('speech.html', transcript=transcript, user=current_user)

# Delete the notes
@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})
