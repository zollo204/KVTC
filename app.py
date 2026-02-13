import os
import csv
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, send_from_directory
)

app = Flask(__name__)
app.secret_key = "secret123"

# -----------------------------
# CONFIG
# -----------------------------
DATA_FILE = "registrations.csv"
CONTACT_FILE = "contact_messages.csv"
EXAMS_FILE = "exam_results.csv"
STUDENT_RESULTS = "student_results.csv"

UPLOAD_FOLDER = "static/uploads"
DOWNLOAD_FOLDER = "static/downloads"

UPLOAD_FOLDER = "static/uploads"
DOWNLOAD_FOLDER = "static/downloads"

PASSPORT_FOLDER = os.path.join(UPLOAD_FOLDER, "passports")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(PASSPORT_FOLDER, exist_ok=True)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# -----------------------------
# CREATE CSV FILES
# -----------------------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Full Name","DOB","Gender","Email","Phone",
            "Course","Constituency","Admission No",
            "Payment Status","Amount Paid","Notes",
            "Password","Passport"
        ])

if not os.path.exists(CONTACT_FILE):
    with open(CONTACT_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Date","Full Name","Email","Phone","Message","Attachment"
        ])

if not os.path.exists(EXAMS_FILE):
    with open(EXAMS_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Year","First Class","Second Upper",
            "Second Lower","Pass","Fail"
        ])

if not os.path.exists(STUDENT_RESULTS):
    with open(STUDENT_RESULTS, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            "Admission No","Full Name","Course",
            "Year","Achievement","Passport"
        ])

# -----------------------------
# PUBLIC PAGES
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/courses")
def courses():
    return render_template("courses.html")

@app.route("/downloads")
def downloads():
    return render_template("downloads.html")

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route("/admissions")
def admissions():
    return render_template("admissions.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/success")
def success():
    return render_template("success.html")

# -----------------------------
# STUDENT REGISTRATION
# -----------------------------
@app.route("/register", methods=["POST"])
def register():
    data = [
        request.form.get("fullname"),
        request.form.get("dob"),
        request.form.get("gender"),
        request.form.get("email"),
        request.form.get("phone"),
        request.form.get("course"),
        request.form.get("constituency"),
        "",          # Admission No
        "Pending",
        "0",
        "",
        "",          # Password (admin sets)
        ""
    ]
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(data)
    return redirect(url_for("success"))

# -----------------------------
# CONTACT FORM
# -----------------------------
@app.route("/contact-submit", methods=["POST"])
def contact_submit():
    file = request.files.get("attachment")
    filename = ""

    if file and file.filename:
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    with open(CONTACT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            request.form.get("fullName"),
            request.form.get("email"),
            request.form.get("phone"),
            request.form.get("message"),
            filename
        ])
    return jsonify({"success": True})

# -----------------------------
# ADMIN LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)

# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        students = list(enumerate(list(csv.reader(f))[1:]))

    with open(CONTACT_FILE, newline="", encoding="utf-8") as f:
        contacts = list(enumerate(list(csv.reader(f))[1:]))

    return render_template("admin.html", students=students, contacts=contacts)

# -----------------------------
# ADMIN – EXAMS
# -----------------------------
@app.route("/admin/exams", methods=["GET", "POST"])
def admin_exams():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        with open(EXAMS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                request.form.get("year"),
                request.form.get("first"),
                request.form.get("upper"),
                request.form.get("lower"),
                request.form.get("pass"),
                request.form.get("fail")
            ])
        return redirect(url_for("admin_exams"))

    with open(EXAMS_FILE, newline="", encoding="utf-8") as f:
        results = list(csv.reader(f))[1:]

    return render_template("admin_exams.html", results=results)

# -----------------------------
# EXPORT EXAM RESULTS TO EXCEL (CSV)
# -----------------------------
@app.route("/admin/export-exams")
def export_exams():
    if not session.get("admin"):
        return redirect(url_for("login"))

    return send_from_directory(
        directory=".",
        path=EXAMS_FILE,
        as_attachment=True,
        download_name="exam_performance.xlsx"
    )

# -----------------------------
# ADMIN – STUDENT RESULTS
# -----------------------------
@app.route("/admin/student-results", methods=["GET", "POST"])
def admin_student_results():
    if not session.get("admin"):
        return redirect(url_for("login"))

    if request.method == "POST":
        passport = request.files.get("passport")
        passport_path = ""

        if passport and passport.filename:
            filename = datetime.now().strftime("%Y%m%d%H%M%S_") + passport.filename
            passport_path = f"uploads/{filename}"
            passport.save(os.path.join("static", passport_path))

        with open(STUDENT_RESULTS, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                request.form.get("adm"),
                request.form.get("name"),
                request.form.get("course"),
                request.form.get("year"),
                request.form.get("achievement"),
                passport_path
            ])
        return redirect(url_for("admin_student_results"))

    with open(STUDENT_RESULTS, newline="", encoding="utf-8") as f:
        results = list(csv.reader(f))[1:]

    return render_template("admin_student_results.html", results=results)

# -----------------------------
# EDIT STUDENT
# -----------------------------
@app.route("/edit/<int:index>", methods=["POST"])
def edit(index):
    if not session.get("admin"):
        return redirect(url_for("login"))

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    student = rows[index + 1]

    fields = [
        "fullname","dob","gender","email","phone",
        "course","constituency","admission_no",
        "payment_status","amount_paid","notes","password"
    ]

    for i, field in enumerate(fields):
        value = request.form.get(field)
        if value:
            student[i] = value

    rows[index + 1] = student

    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    return redirect(url_for("admin"))

# -----------------------------
# DELETE STUDENT
# -----------------------------
@app.route("/delete-student/<int:index>", methods=["POST"])
def delete_student(index):
    if not session.get("admin"):
        return redirect(url_for("login"))

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if index + 1 < len(rows):
        rows.pop(index + 1)

    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    return redirect(url_for("admin"))

# -----------------------------
# STUDENT LOGIN
# -----------------------------
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    error = None
    if request.method == "POST":
        adm = request.form.get("admission_no")
        pwd = request.form.get("password")

        with open(DATA_FILE, newline="", encoding="utf-8") as f:
            students = list(csv.reader(f))[1:]

        for i, s in enumerate(students):
            if s[7] == adm and s[11] == pwd:
                session["student_index"] = i
                return redirect(url_for("student_dashboard"))

        error = "Invalid Admission Number or Password"

    return render_template("student_login.html", error=error)

# -----------------------------
# STUDENT FORGOT PASSWORD
# -----------------------------
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    admission_no = request.form.get("admission_no")

    if not admission_no:
        return render_template("student_login.html", error="Admission number required", show_forgot=True)

    # Log the request in contact CSV
    with open(CONTACT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "PASSWORD RESET REQUEST",
            "",
            "",
            f"Student with Admission No {admission_no} requested password reset",
            ""
        ])

    return render_template("student_login.html", message="Password reset request sent. Contact admin.", show_forgot=True)

# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
@app.route("/student/dashboard")
def student_dashboard():
    if "student_index" not in session:
        return redirect(url_for("student_login"))

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        student = list(csv.reader(f))[session["student_index"] + 1]

    return render_template("student_dashboard.html", student=student)

@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if "student_index" not in session:
        return redirect(url_for("student_login"))

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        student = rows[session["student_index"] + 1]

    message = None

    if request.method == "POST":

        # -----------------------------
        # HANDLE PASSPORT UPLOAD
        # -----------------------------
        passport = request.files.get("passport")
        if passport and passport.filename:
            filename = datetime.now().strftime("%Y%m%d%H%M%S_") + passport.filename
            save_path = os.path.join(PASSPORT_FOLDER, filename)
            passport.save(save_path)

            # Save filename in CSV (Passport column)
            student[12] = filename
            message = "Passport uploaded successfully"

        # -----------------------------
        # HANDLE PASSWORD CHANGE
        # -----------------------------
        password = request.form.get("password")
        if password:
            student[11] = password
            message = "Password updated successfully"

        rows[session["student_index"] + 1] = student
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)

    return render_template(
        "student_profile.html",
        student=student,
        passport=student[12],
        message=message
    )

# -----------------------------
# DELETE CONTACT (ADMIN)
# -----------------------------
@app.route("/delete-contact/<int:index>", methods=["POST"])
def delete_contact(index):
    if not session.get("admin"):
        return redirect(url_for("login"))

    with open(CONTACT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    if index + 1 < len(rows):
        rows.pop(index + 1)

    with open(CONTACT_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    return redirect(url_for("admin"))

# -----------------------------
# LOGOUTS
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student/logout")
def student_logout():
    session.clear()
    return redirect(url_for("student_login"))

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)