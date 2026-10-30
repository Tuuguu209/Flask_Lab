import os
from datetime import datetime, timezone

from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import HttpLib2Error

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['GOOGLE_SHEETS_SPREADSHEET_ID'] = os.environ.get(
    'GOOGLE_SHEETS_SPREADSHEET_ID',
    '1P93pzpe_-Vs8751x2xuyHaFGdCRaU8IiIqJVx7IE_Ts'
)
GOOGLE_SHEETS_URL = (
    'https://docs.google.com/spreadsheets/d/'
    f"{app.config['GOOGLE_SHEETS_SPREADSHEET_ID']}/edit"
)

db = SQLAlchemy(app)


class GoogleSheetsSyncError(RuntimeError):
    pass


def append_registration_to_sheet(registration):
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise GoogleSheetsSyncError(
            'Google Sheets is not configured. Set GOOGLE_APPLICATION_CREDENTIALS.'
        )
    if not os.path.isfile(credentials_path):
        raise GoogleSheetsSyncError(
            'The service-account credentials file was not found.'
        )

    try:
        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
        spreadsheet = sheets.spreadsheets().get(
            spreadsheetId=app.config['GOOGLE_SHEETS_SPREADSHEET_ID'],
            fields='sheets.properties.title'
        ).execute()

        sheet_tabs = spreadsheet.get('sheets', [])
        if not sheet_tabs:
            raise GoogleSheetsSyncError('The spreadsheet does not contain a sheet tab.')

        sheet_properties = sheet_tabs[0].get('properties', {})
        if not sheet_properties.get('title'):
            raise GoogleSheetsSyncError('The spreadsheet sheet tab has no title.')
        sheet_title = sheet_properties['title'].replace("'", "''")
        header_range = f"'{sheet_title}'!A1:E1"
        data_range = f"'{sheet_title}'!A:E"
        values_api = sheets.spreadsheets().values()
        header = values_api.get(
            spreadsheetId=app.config['GOOGLE_SHEETS_SPREADSHEET_ID'],
            range=header_range
        ).execute().get('values', [])

        if not header:
            values_api.update(
                spreadsheetId=app.config['GOOGLE_SHEETS_SPREADSHEET_ID'],
                range=header_range,
                valueInputOption='RAW',
                body={'values': [['Овог нэр', 'Утас', 'И-мэйл', 'Мэргэжил', 'Бүртгэсэн огноо (UTC)']]}
            ).execute()

        values_api.append(
            spreadsheetId=app.config['GOOGLE_SHEETS_SPREADSHEET_ID'],
            range=data_range,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [[
                registration.fullname,
                registration.phone,
                registration.email,
                registration.program,
                datetime.now(timezone.utc).isoformat(timespec='seconds')
            ]]}
        ).execute()
    except GoogleSheetsSyncError:
        raise
    except (GoogleAuthError, HttpError, HttpLib2Error, OSError, ValueError) as error:
        raise GoogleSheetsSyncError(
            'Google Sheets could not save this registration. Check the API setup and sheet permissions.'
        ) from error


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    program = db.Column(db.String(100), nullable=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()
    if not News.query.first():
        db.session.add(News(date="2026-10-12", title="Шинэ хичээлийн жилийн элсэлт эхэллээ"))
        db.session.add(News(date="2026-10-01", title="Оюутнуудын дунд спортын тэмцээн болно"))
        db.session.commit()

programs = {
    "web-programming": {
        "name": "Вэб програмчлал",
        "icon": "💻",
        "description": "Вэб сайт болон веб систем боловсруулах чиглэлээр мэргэжлийн мэдлэг, ур чадвар эзэмшинэ."
    },
    "graphic-design": {
        "name": "Хэвлэлийн график дизайн",
        "icon": "🎨",
        "description": "Хэвлэлийн болон график дизайны бүтээгдэхүүн боловсруулах ур чадвар эзэмшинэ."
    },
    "hairdressing": {
        "name": "Үсчин",
        "icon": "💇",
        "description": "Үс засалт, хэлбэржүүлэлт, будаг болон гоо сайхны үйлчилгээний ур чадвар эзэмшинэ."
    },
    "tourism": {
        "name": "Аялал жуулчлал",
        "icon": "✈️",
        "description": "Аялал жуулчлалын үйлчилгээ, аяллын хөтөлбөр боловсруулах мэдлэг эзэмшинэ."
    },
    "office": {
        "name": "Оффис бичиг хэрэг",
        "icon": "📑",
        "description": "Албан хэрэг хөтлөлт, бичиг баримт боловсруулах ур чадвар эзэмшинэ."
    },
    "beauty": {
        "name": "Гоо засалч",
        "icon": "💄",
        "description": "Гоо сайхны үйлчилгээ, нүүр будалт, арьс арчилгааны ур чадвар эзэмшинэ."
    },
    "nursing": {
        "name": "Сувилагч",
        "icon": "🩺",
        "description": "Эрүүл мэндийн байгууллагад сувилахуйн тусламж үйлчилгээ үзүүлэх ур чадвар эзэмшинэ."
    },
    "accounting": {
        "name": "Нярав",
        "icon": "💰",
        "description": "Байгууллагын бараа материал, хөрөнгийн бүртгэл хөтлөх мэдлэг эзэмшинэ."
    },
    "stage-screen": {
        "name": "Тайз дэлгэц",
        "icon": "🎬",
        "description": "Тайз, дэлгэцийн бүтээл, зураг авалт, техникийн чиглэлээр мэдлэг эзэмшинэ."
    },
    "fashion-design": {
        "name": "Хувцас дизайн",
        "icon": "👗",
        "description": "Хувцас загвар зохион бүтээх, эсгүүр хийх, оёх ур чадвар эзэмшинэ."
    },
    "construction": {
        "name": "Барилга",
        "icon": "🏗️",
        "description": "Барилгын технологи, зураг төсөл, барилгын ажил гүйцэтгэх мэдлэг эзэмшинэ."
    }
}

@app.route("/")
def index():
    news_items = News.query.order_by(News.id.desc()).all()
    return render_template("index.html", programs=programs, news=news_items)

@app.route("/hutulbur/<program_slug>")
def hutulbur(program_slug):
    program = programs.get(program_slug)
    if program is None:
        return "Хөтөлбөр олдсонгүй", 404
    return render_template("program_detail.html", program=program)

@app.route("/register", methods=["POST"])
def register():
    new_reg = Registration(
        fullname=request.form.get("fullname"),
        phone=request.form.get("phone"),
        email=request.form.get("email"),
        program=request.form.get("program")
    )
    db.session.add(new_reg)
    db.session.commit()
    try:
        append_registration_to_sheet(new_reg)
    except GoogleSheetsSyncError as error:
        app.logger.exception(
            "Could not sync registration %s to Google Sheets: %s",
            new_reg.id,
            error
        )
        flash(
            "Таны бүртгэл системд хадгалагдсан боловч Google Sheets рүү илгээгдсэнгүй. "
            "Админд мэдэгдэнэ үү.",
            "error"
        )
    else:
        flash("Таны бүртгэл амжилттай илгээгдлээ.", "success")
    return redirect(url_for('index') + '#register')

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            session['logged_in'] = True
            return redirect(url_for('view_submissions'))
        else:
            error = "Нэвтрэх нэр эсвэл нууц үг буруу байна!"
    return render_template("login.html", error=error)

@app.route("/admin/submissions")
def view_submissions():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    return render_template("admin.html", 
                         registrations=Registration.query.order_by(Registration.id.desc()).all(), 
                         news=News.query.order_by(News.id.desc()).all(),
                         google_sheet_url=GOOGLE_SHEETS_URL)

@app.route("/admin/news/add", methods=["POST"])
def add_news():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    date = request.form.get("date")
    title = request.form.get("title")
    if date and title:
        db.session.add(News(date=date, title=title))
        db.session.commit()
    return redirect(url_for('view_submissions'))

@app.route("/admin/news/delete/<int:news_id>")
def delete_news(news_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    db.session.delete(News.query.get_or_404(news_id))
    db.session.commit()
    return redirect(url_for('view_submissions'))

@app.route("/admin/registration/delete/<int:reg_id>")
def delete_registration(reg_id):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    db.session.delete(Registration.query.get_or_404(reg_id))
    db.session.commit()
    return redirect(url_for('view_submissions'))

@app.route("/admin/logout")
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    app.run(debug=True)