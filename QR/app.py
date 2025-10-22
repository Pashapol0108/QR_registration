from flask import Flask, render_template, request, redirect, url_for, send_file, session, jsonify
import sqlite3, uuid, qrcode, os, csv
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'supersecretkey'
PIN_CODE = "1234"
INSTANCE_FOLDER = 'instance'
os.makedirs(INSTANCE_FOLDER, exist_ok=True)

app.permanent_session_lifetime = timedelta(days=1)

PARTICIPANTS_DB = os.path.join(INSTANCE_FOLDER, 'participants.db')
CHECKINS_DB     = os.path.join(INSTANCE_FOLDER, 'checkins.db')

QR_FOLDER = 'static/qr'
LOCATIONS = ['Вход', 'Регистрация', 'Актовый зал', 'Лаборатория']
os.makedirs(QR_FOLDER, exist_ok=True)

def normalize_phone(v: str) -> str:
    if not v:
        return ''
    digits = ''.join(ch for ch in v if ch.isdigit())
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 10 and digits[0] == '9':
        digits = '7' + digits
    if not digits.startswith('7'):
        digits = '7' + digits.lstrip('7')
    return digits[:11]

def init_db():
    conn = sqlite3.connect(PARTICIPANTS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY,
                    fio TEXT,
                    category TEXT,
                    phone TEXT UNIQUE,
                    email TEXT UNIQUE,
                    uuid TEXT,
                    registered_at TEXT
                )''')
    conn.commit()
    conn.close()

    conn = sqlite3.connect(CHECKINS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS checkins (
                    id INTEGER PRIMARY KEY,
                    participant_id INTEGER,
                    location TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        fio       = request.form['fio']
        category  = request.form['category']
        raw_phone = request.form['phone']
        email     = request.form['email']

        phone = normalize_phone(raw_phone)
        participant_uuid = str(uuid.uuid4())
        registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(PARTICIPANTS_DB)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO participants (fio, category, phone, email, uuid, registered_at) VALUES (?, ?, ?, ?, ?, ?)",
                (fio, category, phone, email, participant_uuid, registered_at)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('index.html', error="Телефон или Email уже зарегистрирован")


        qr_link = url_for('checkin', participant_uuid=participant_uuid, _external=True)
        qr_img = qrcode.make(qr_link)
        qr_path = os.path.join(QR_FOLDER, f"{participant_uuid}.png")
        qr_img.save(qr_path)


        qr_web_path = url_for('static', filename=f'qr/{participant_uuid}.png')
        return render_template('index.html', qr_path=qr_web_path, qr_link=qr_link)

    return render_template('index.html')

@app.route('/check_unique', methods=['POST'])
def check_unique():
    data = request.json or {}
    field = data.get('field')
    value = data.get('value', '')

    if field not in ['phone', 'email']:
        return jsonify({'exists': False})

    if field == 'phone':
        value = normalize_phone(value)

    conn = sqlite3.connect(PARTICIPANTS_DB)
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM participants WHERE {field}=?", (value,))
    exists = c.fetchone()[0] > 0
    conn.close()

    return jsonify({'exists': exists})

@app.route('/checkin/<participant_uuid>', methods=['GET', 'POST'])
def checkin(participant_uuid):

    if not session.get("verified"):

        return redirect(url_for("pin", next=url_for("checkin", participant_uuid=participant_uuid)))


    conn = sqlite3.connect(PARTICIPANTS_DB)
    c = conn.cursor()
    c.execute("SELECT id, fio FROM participants WHERE uuid=?", (participant_uuid,))
    participant = c.fetchone()
    conn.close()

    if not participant:
        return render_template('not_found.html'), 404

    pid, fio = participant

    if request.method == 'POST':
        location = request.form.get('location')
        if location not in LOCATIONS:
            return render_template('checkin.html', fio=fio, locations=LOCATIONS, ok=False, msg="Неверная локация")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(CHECKINS_DB)
        c = conn.cursor()
        c.execute("INSERT INTO checkins (participant_id, location, timestamp) VALUES (?,?,?)",
                  (pid, location, ts))
        conn.commit()
        conn.close()
        return render_template('checkin.html', fio=fio, locations=LOCATIONS, ok=True, msg=f"Отмечено: {location}")

    return render_template('checkin.html', fio=fio, locations=LOCATIONS, ok=None)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        if login == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin.html', error="Неверный логин или пароль")

    if not session.get('admin'):
        return render_template('admin.html')

    conn = sqlite3.connect(PARTICIPANTS_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM participants")
    participants = c.fetchall()
    conn.close()

    conn = sqlite3.connect(CHECKINS_DB)
    c = conn.cursor()
    c.execute("SELECT participant_id, location FROM checkins")
    checkins_raw = c.fetchall()
    checkins = {}
    for pid, loc in checkins_raw:
        if pid not in checkins:
            checkins[pid] = []
        checkins[pid].append(loc)
    conn.close()

    return render_template('admin.html', participants=participants, checkins=checkins, locations=LOCATIONS)


@app.route('/export_csv')
def export_csv():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = sqlite3.connect(PARTICIPANTS_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM participants")
    participants = c.fetchall()
    conn.close()

    conn = sqlite3.connect(CHECKINS_DB)
    c = conn.cursor()
    c.execute("SELECT participant_id, location FROM checkins")
    checkins_raw = c.fetchall()
    checkins = {}
    for pid, loc in checkins_raw:
        if pid not in checkins:
            checkins[pid] = []
        checkins[pid].append(loc)
    conn.close()

    csv_file = 'participants_export.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ['ID', 'ФИО', 'Категория', 'Телефон', 'Email', 'UUID', 'Зарегистрирован', *LOCATIONS]
        writer.writerow(header)
        for p in participants:
            row = list(p)
            row_checkins = [loc if loc in checkins.get(p[0], []) else '' for loc in LOCATIONS]
            writer.writerow(row + row_checkins)

    return send_file(csv_file, as_attachment=True)

@app.route('/pin', methods=['GET', 'POST'])
def pin():
    error = None
    next_url = request.args.get("next") or url_for("index")

    if request.method == "POST":
        code = request.form.get("code")
        if code == PIN_CODE:
            session.permanent = True
            session["verified"] = True
            return redirect(next_url)
        else:
            error = "Неверный код!"

    return render_template("pin.html", error=error, next_url=next_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
