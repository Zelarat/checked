from app.models import User, Poll, Answer, Question
from flask_login import login_required, current_user, login_user, logout_user
from app import app, login_manager, db
from flask import render_template, flash, redirect, url_for, json, request, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import csv
from io import BytesIO


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Фильтр для шаблонов
@app.template_filter('from_json')
def from_json_filter(data):
    try:
        return json.loads(data) if data else []
    except:
        return []


# Маршруты
@app.route('/')
def index():
    polls = Poll.query.all()
    return render_template('index.html', polls=polls)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        user = User(username=username)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Registration successful!', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    if request.method == 'POST':
        try:
            poll = Poll(
                title=request.form['title'],
                user_id=current_user.id
            )
            db.session.add(poll)
            db.session.flush()

            questions = request.form.getlist('question[]')
            types = request.form.getlist('type[]')
            options_list = request.form.getlist('options[]')

            for q_text, q_type, opts in zip(questions, types, options_list):
                if not q_text.strip():
                    raise ValueError("Question text cannot be empty")

                options = None
                if q_type in ['radio', 'checkbox']:
                    options = json.loads(opts)
                    if not isinstance(options, list):
                        raise ValueError("Options must be a JSON array")

                question = Question(
                    text=q_text.strip(),
                    type=q_type,
                    options=json.dumps(options, ensure_ascii=False) if q_type in ['radio', 'checkbox'] else "text",
                    poll_id=poll.id
                )
                db.session.add(question)

            db.session.commit()
            flash('Poll created successfully!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('create_poll.html')


@app.route('/poll/<int:poll_id>', methods=['GET', 'POST'])
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    print(poll.questions)
    if request.method == 'POST':
        try:
            for question in poll.questions:
                response = None
                if question.type == 'checkbox':
                    response = ','.join(request.form.getlist(f'q_{question.id}'))
                else:
                    response = request.form.get(f'q_{question.id}')

                if response:
                    answer = Answer(
                        content=response,
                        question_id=question.id,
                        user_id=current_user.id if current_user.is_authenticated else None,
                        poll_id=poll_id
                    )
                    db.session.add(answer)

            db.session.commit()
            flash('Thank you for participating!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('poll.html', poll=poll, question=poll.questions)


@app.route('/results/<int:poll_id>')
@login_required
def poll_results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    #if poll.user_id != current_user.id:
    #    flash('Access denied', 'error')
    #    return redirect(url_for('index'))

    return render_template('poll_results.html', poll=poll)


@app.route('/export_csv/<int:poll_id>')
@login_required
def export_csv(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    csv_buffer = BytesIO()
    writer = csv.writer(csv_buffer)

    headers = ['User', 'Timestamp'] + [q.text for q in poll.questions]
    writer.writerow(headers)

    answers_data = {}
    for answer in Answer.query.join(Question).filter(Question.poll_id == poll_id).all():
        user_key = answer.user_id or 'anonymous'
        if user_key not in answers_data:
            answers_data[user_key] = {
                'user': f"User {answer.user_id}" if answer.user_id else "Anonymous",
                'timestamp': answer.timestamp,
                'answers': {}
            }
        answers_data[user_key]['answers'][answer.question_id] = answer.content

    for data in answers_data.values():
        row = [
            data['user'],
            data['timestamp'].strftime('%Y-%m-%d %H:%M')
        ]
        for question in poll.questions:
            row.append(data['answers'].get(question.id, ''))
        writer.writerow(row)

    csv_buffer.seek(0)
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{poll.title}_results.csv"
    )