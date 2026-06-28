import os
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify
)
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from config import Config
from model import db, Profile, Skill, Experience, Project, Contact, AboutSection
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

try:
    import cloudinary
    import cloudinary.uploader
except Exception:
    cloudinary = None

try:
    import resend
except Exception:
    resend = None

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Unhandled exception during request")
    return "Internal Server Error", 500

if cloudinary and Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_API_KEY,
        api_secret=Config.CLOUDINARY_API_SECRET,
        secure=True,
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def skill_icon(skill_name):
    name = (skill_name or "").strip().lower()
    icon_map = {
        "python": "fa-brands fa-python",
        "flask": "fa-solid fa-flask",
        "javascript": "fa-brands fa-js",
        "js": "fa-brands fa-js",
        "html": "fa-brands fa-html5",
        "css": "fa-brands fa-css3-alt",
        "sql": "fa-solid fa-database",
        "mysql": "fa-solid fa-database",
        "sqlite": "fa-solid fa-database",
        "postgres": "fa-solid fa-database",
        "postgresql": "fa-solid fa-database",
        "php": "fa-brands fa-php",
        "java": "fa-brands fa-java",
        "c++": "fa-solid fa-cog",
        "c#": "fa-solid fa-code",
        "react": "fa-brands fa-react",
        "node": "fa-brands fa-node-js",
        "nodejs": "fa-brands fa-node-js",
        "express": "fa-solid fa-rocket",
        "django": "fa-solid fa-layer-group",
        "git": "fa-brands fa-git-alt",
        "github": "fa-brands fa-github",
        "docker": "fa-brands fa-docker",
        "tailwind": "fa-solid fa-wand-magic-sparkles",
        "bootstrap": "fa-brands fa-bootstrap",
        "api": "fa-solid fa-plug",
        "rest": "fa-solid fa-plug",
        "figma": "fa-brands fa-figma",
        "linux": "fa-brands fa-linux",
        "ubuntu": "fa-brands fa-ubuntu",
        "firebase": "fa-solid fa-fire",
        "mongodb": "fa-solid fa-leaf",
        "excel": "fa-solid fa-chart-column",
        "office": "fa-solid fa-file-lines",
    }

    for keyword, icon_class in icon_map.items():
        if keyword in name:
            return icon_class

    return "fa-solid fa-code"


app.jinja_env.globals["skill_icon"] = skill_icon


def upload_image(file_storage, folder="portfolio"):
    """Upload ke Cloudinary jika konfigurasi tersedia. Jika belum, simpan lokal agar localhost tetap jalan."""
    if not file_storage or file_storage.filename == "":
        return None

    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename):
        raise ValueError("Format gambar harus png, jpg, jpeg, webp, atau gif.")

    if cloudinary and Config.CLOUDINARY_CLOUD_NAME and Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
        result = cloudinary.uploader.upload(file_storage, folder=folder)
        return result.get("secure_url")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOAD_DIR / filename
    file_storage.save(save_path)
    return url_for("static", filename=f"uploads/{filename}")


def send_contact_email(contact):
    """Kirim email menggunakan Resend jika API key tersedia."""
    if not (resend and Config.RESEND_API_KEY and Config.CONTACT_RECEIVER_EMAIL):
        return "saved_local_only"

    resend.api_key = Config.RESEND_API_KEY
    html = f"""
    <h2>Pesan Baru dari Website Portofolio</h2>
    <p><strong>Nama:</strong> {contact.name}</p>
    <p><strong>Email:</strong> {contact.email}</p>
    <p><strong>Subject:</strong> {contact.subject}</p>
    <p><strong>Pesan:</strong></p>
    <p>{contact.message}</p>
    """
    resend.Emails.send({
        "from": Config.CONTACT_SENDER_EMAIL,
        "to": [Config.CONTACT_RECEIVER_EMAIL],
        "subject": f"Portfolio Contact: {contact.subject}",
        "html": html,
        "reply_to": contact.email,
    })
    return "sent_resend"


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped_view


@app.after_request
def add_admin_no_cache_headers(response):
    if request.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route("/")
def home():
    profile = Profile.query.first()
    about_section = AboutSection.query.order_by(AboutSection.id.desc()).first()
    skills = Skill.query.order_by(Skill.category.asc(), Skill.name.asc()).all()
    experiences = Experience.query.order_by(Experience.id.desc()).all()
    projects = Project.query.order_by(Project.id.desc()).all()
    return render_template(
        "utama/index.html",
        profile=profile,
        about_section=about_section,
        skills=skills,
        experiences=experiences,
        projects=projects,
    )


@app.post("/contact")
def contact_submit():
    contact = Contact(
        name=request.form.get("name", "").strip(),
        email=request.form.get("email", "").strip(),
        subject=request.form.get("subject", "").strip(),
        message=request.form.get("message", "").strip(),
    )
    if not all([contact.name, contact.email, contact.subject, contact.message]):
        flash("Semua field contact wajib diisi.", "danger")
        return redirect(url_for("home") + "#contact")

    db.session.add(contact)
    db.session.commit()

    try:
        contact.email_status = send_contact_email(contact)
        db.session.commit()
        flash("Pesan sudah terkirim.", "success")
    except Exception as exc:
        contact.email_status = "email_failed"
        db.session.commit()
        flash("Pesan sudah terkirim.", "success")

    return redirect(url_for("home") + "#contact")


@app.route("/api/portfolio")
def api_portfolio():
    profile = Profile.query.first()
    about_section = AboutSection.query.order_by(AboutSection.id.desc()).first()
    return jsonify({
        "profile": {
            "name": profile.name if profile else "Nama Kamu",
            "title": profile.title if profile else "Backend Developer",
            "email": profile.email if profile else "",
            "instagram": profile.instagram if profile else "",
            "tiktok": profile.tiktok if profile else "",
        },
        "about": {
            "title": about_section.title if about_section else "Tentang Saya",
            "subtitle": about_section.subtitle if about_section else "",
            "description": about_section.description if about_section else (profile.bio if profile else ""),
        },
        "skills": [{"name": s.name, "category": s.category, "level": s.level} for s in Skill.query.all()],
        "experiences": [{"title": e.title, "organization": e.organization, "period": e.period} for e in Experience.query.all()],
        "projects": [{"title": p.title, "tech_stack": p.tech_stack, "image_url": p.image_url} for p in Project.query.all()],
    })


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "GET":
        session.pop("admin_logged_in", None)

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Username atau password salah."
    return render_template("admin/login.html", error=error)



@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = {
        "profiles": Profile.query.count(),
        "skills": Skill.query.count(),
        "experiences": Experience.query.count(),
        "projects": Project.query.count(),
        "contacts": Contact.query.count(),
    }
    contacts = Contact.query.order_by(Contact.id.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, contacts=contacts)


@app.route("/admin/profiles", methods=["GET", "POST"])
@login_required
def admin_profiles():
    profile = Profile.query.first()
    if not profile:
        profile = Profile(
            name="Nama Kamu",
            title="Backend Developer | Python | Flask | Database | API",
            bio="Tulis deskripsi profil kamu di sini.",
            email="emailkamu@example.com",
        )
        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":
        profile.name = request.form.get("name")
        profile.title = request.form.get("title")
        profile.bio = request.form.get("bio")
        profile.email = request.form.get("email")
        profile.instagram = request.form.get("instagram")
        profile.tiktok = request.form.get("tiktok")
        profile.whatsapp = request.form.get("whatsapp")
        image_url = request.form.get("image_url")
        if image_url:
            profile.image_url = image_url
        image_file = request.files.get("image_file")
        try:
            uploaded = upload_image(image_file, folder="portfolio/profile")
            if uploaded:
                profile.image_url = uploaded
            db.session.commit()
            flash("Profil berhasil diperbarui.", "success")
        except Exception as exc:
            flash(str(exc), "danger")
        return redirect(url_for("admin_profiles"))

    return render_template("admin/profiles.html", profile=profile)


@app.route("/admin/about", methods=["GET", "POST"])
@app.route("/admin/about/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def admin_about(item_id=None):
    item = AboutSection.query.get(item_id) if item_id else None
    if item is None:
        item = AboutSection.query.order_by(AboutSection.id.desc()).first()

    if request.method == "POST":
        if item is None:
            item = AboutSection()
            db.session.add(item)
        item.title = "Tentang Saya"
        item.subtitle = ""
        item.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Deskripsi Tentang berhasil disimpan.", "success")
        return redirect(url_for("admin_about"))

    items = AboutSection.query.order_by(AboutSection.id.desc()).all()
    return render_template("admin/about.html", items=items, item=item)


@app.post("/admin/about/<int:item_id>/delete")
@login_required
def delete_about(item_id):
    db.session.delete(AboutSection.query.get_or_404(item_id))
    db.session.commit()
    flash("Data Tentang berhasil dihapus.", "success")
    return redirect(url_for("admin_about"))


@app.route("/admin/skills", methods=["GET", "POST"])
@app.route("/admin/skills/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def admin_skills(item_id=None):
    item = Skill.query.get(item_id) if item_id else None
    if request.method == "POST":
        if item is None:
            item = Skill()
            db.session.add(item)
        item.name = request.form.get("name")
        item.category = request.form.get("category")
        item.level = int(request.form.get("level") or 70)
        item.description = request.form.get("description")
        db.session.commit()
        flash("Skill berhasil disimpan.", "success")
        return redirect(url_for("admin_skills"))

    items = Skill.query.order_by(Skill.category.asc(), Skill.name.asc()).all()
    return render_template("admin/skills.html", items=items, item=item)


@app.post("/admin/skills/<int:item_id>/delete")
@login_required
def delete_skill(item_id):
    db.session.delete(Skill.query.get_or_404(item_id))
    db.session.commit()
    flash("Skill berhasil dihapus.", "success")
    return redirect(url_for("admin_skills"))


@app.route("/admin/experiences", methods=["GET", "POST"])
@app.route("/admin/experiences/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def admin_experiences(item_id=None):
    item = Experience.query.get(item_id) if item_id else None
    if request.method == "POST":
        if item is None:
            item = Experience()
            db.session.add(item)
        item.title = request.form.get("title")
        item.organization = request.form.get("organization")
        item.period = request.form.get("period")
        item.description = request.form.get("description")
        db.session.commit()
        flash("Pengalaman berhasil disimpan.", "success")
        return redirect(url_for("admin_experiences"))

    items = Experience.query.order_by(Experience.id.desc()).all()
    return render_template("admin/experiences.html", items=items, item=item)


@app.post("/admin/experiences/<int:item_id>/delete")
@login_required
def delete_experience(item_id):
    db.session.delete(Experience.query.get_or_404(item_id))
    db.session.commit()
    flash("Pengalaman berhasil dihapus.", "success")
    return redirect(url_for("admin_experiences"))


@app.route("/admin/projects", methods=["GET", "POST"])
@app.route("/admin/projects/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def admin_projects(item_id=None):
    item = Project.query.get(item_id) if item_id else None
    if request.method == "POST":
        if item is None:
            item = Project()
            db.session.add(item)
        item.title = request.form.get("title")
        item.description = request.form.get("description")
        item.tech_stack = request.form.get("tech_stack")
        item.demo_url = request.form.get("demo_url")
        item.github_url = request.form.get("github_url")
        image_url = request.form.get("image_url")
        if image_url:
            item.image_url = image_url
        image_file = request.files.get("image_file")
        try:
            uploaded = upload_image(image_file, folder="portfolio/projects")
            if uploaded:
                item.image_url = uploaded
            db.session.commit()
            flash("Project berhasil disimpan.", "success")
        except Exception as exc:
            flash(str(exc), "danger")
        return redirect(url_for("admin_projects"))

    items = Project.query.order_by(Project.id.desc()).all()
    return render_template("admin/projects.html", items=items, item=item)


@app.post("/admin/projects/<int:item_id>/delete")
@login_required
def delete_project(item_id):
    db.session.delete(Project.query.get_or_404(item_id))
    db.session.commit()
    flash("Project berhasil dihapus.", "success")
    return redirect(url_for("admin_projects"))


@app.route("/admin/contacts")
@login_required
def admin_contacts():
    contacts = Contact.query.order_by(Contact.id.desc()).all()
    return render_template("admin/contacts.html", contacts=contacts)


@app.post("/admin/contacts/<int:item_id>/read")
@login_required
def mark_contact_read(item_id):
    contact = Contact.query.get_or_404(item_id)
    contact.is_read = True
    db.session.commit()
    flash("Kontak ditandai sudah dibaca.", "success")
    return redirect(url_for("admin_contacts"))


@app.post("/admin/contacts/<int:item_id>/delete")
@login_required
def delete_contact(item_id):
    db.session.delete(Contact.query.get_or_404(item_id))
    db.session.commit()
    flash("Kontak berhasil dihapus.", "success")
    return redirect(url_for("admin_contacts"))


def seed_database():
    existing_profile = Profile.query.first()
    if existing_profile and existing_profile.title == "Portfolio Dinamis Berbasis Web":
        existing_profile.title = "Backend Developer | Python | Flask | Database | API"

    if Profile.query.count() == 0:
        db.session.add(Profile(
            name="Nama Kamu",
            title="Backend Developer | Python | Flask | Database | API",
            bio="Saya adalah Backend Developer yang fokus membangun REST API, database design, autentikasi, upload gambar, dan integrasi layanan email untuk aplikasi web portofolio.",
            email="emailkamu@example.com",
            instagram="#",
            tiktok="#",
            whatsapp="#",
        ))

    if AboutSection.query.count() == 0:
        db.session.add(AboutSection(
            title="Tentang Saya",
            subtitle="Mahasiswa & Backend Developer",
            description="Saya adalah mahasiswa yang memiliki minat pada pengembangan aplikasi web, database, dan backend development menggunakan Python serta Flask.",
        ))

    if Skill.query.count() == 0:
        db.session.add_all([
            Skill(name="Python", category="Programming", level=88, description="Logic, backend, automation."),
            Skill(name="Flask", category="Backend", level=85, description="Routing, API, template, admin CRUD."),
            Skill(name="SQL / TiDB", category="Database", level=82, description="Schema, query, relational database."),
            Skill(name="Cloudinary", category="API Integration", level=78, description="Upload dan penyimpanan gambar."),
            Skill(name="Resend", category="API Integration", level=76, description="Pengiriman email dari form kontak."),
            Skill(name="HTML, CSS, JavaScript", category="Frontend", level=80, description="Antarmuka responsive."),
        ])

    if Experience.query.count() == 0:
        db.session.add_all([
            Experience(title="Pengembangan Aplikasi Portofolio", organization="Project PA", period="2026", description="Membangun portfolio website dengan Flask, database, admin CRUD, Cloudinary, dan Resend."),
            Experience(title="Belajar Backend Development", organization="Mandiri", period="2025 - Sekarang", description="Mempelajari routing, database, API, authentication, dan deployment dasar."),
            Experience(title="Mahasiswa Teknik Informatika", organization="Kampus", period="Aktif", description="Mempelajari pemrograman, database, dan pengembangan aplikasi web."),
        ])

    if Project.query.count() == 0:
        db.session.add_all([
            Project(title="Portfolio Website Dinamis", description="Website portofolio yang menampilkan profil, skill, pengalaman, project, dan contact secara dinamis dari database.", tech_stack="Python, Flask, TiDB, HTML, CSS, JavaScript"),
            Project(title="Admin CRUD Portfolio", description="Dashboard admin untuk mengelola profil, skill, pengalaman, project, kontak, dan upload gambar.", tech_stack="Flask, SQLAlchemy, Cloudinary"),
            Project(title="Contact Form dengan Resend", description="Form kontak yang menyimpan data ke database dan mengirim email menggunakan Resend API.", tech_stack="Flask, Resend, SQL"),
        ])

    db.session.commit()



def ensure_profile_social_columns():
    """Menambahkan kolom sosial baru jika user masih memakai database lokal versi lama."""
    inspector = inspect(db.engine)
    if "profiles" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("profiles")}
    statements = []
    if "instagram" not in existing_columns:
        statements.append("ALTER TABLE profiles ADD COLUMN instagram VARCHAR(255)")
    if "tiktok" not in existing_columns:
        statements.append("ALTER TABLE profiles ADD COLUMN tiktok VARCHAR(255)")

    for statement in statements:
        db.session.execute(text(statement))
    if statements:
        db.session.commit()


def create_database_tables():
    for model in (Profile, Skill, Experience, Project, Contact, AboutSection):
        try:
            db.metadata.create_all(bind=db.engine, tables=[model.__table__], checkfirst=True)
        except OperationalError as exc:
            message = str(exc).lower()
            if "already exists" in message or "information schema is changed" in message:
                continue
            raise


def initialize_database():
    try:
        create_database_tables()
        ensure_profile_social_columns()
        seed_database()
    except OperationalError as exc:
        app.logger.error("Database initialization failed at request time: %s", exc)
    except Exception as exc:
        app.logger.exception("Unexpected error during request-time database setup: %s", exc)


def create_app():
    return app

if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True)
