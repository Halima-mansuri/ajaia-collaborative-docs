import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "ajaia-dev-secret-change-in-production")
ALLOWED_EXTENSIONS = {"txt", "md", "docx"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
