from flask import Flask, render_template, request, url_for, redirect
from werkzeug.utils import secure_filename
import os
import PyPDF2
import docx

# ---------------- Configuration ----------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# create uploads folder if missing
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- Skills list ----------------
ALL_SKILLS = [
    # Programming Languages
    "Python","Java","C++","C#","JavaScript","TypeScript","Go","Ruby","R","PHP",
    # Web
    "HTML","CSS","React","Angular","Vue","Flask","Django","Node.js","Bootstrap",
    # Databases
    "SQL","MySQL","PostgreSQL","MongoDB","SQLite","Oracle","Redis",
    # Cloud & DevOps
    "AWS","Azure","GCP","Docker","Kubernetes","CI/CD","Git","GitHub","Jenkins",
    # Data Science & AI/ML
    "Machine Learning","Deep Learning","TensorFlow","PyTorch","Keras","Numpy","Pandas","Scikit-learn",
    "Data Analysis","Data Visualization","Tableau","Power BI",
    # Others
    "Selenium","Unit Testing","API","REST","GraphQL","Agile","Scrum","Linux","Bash","Problem Solving"
]

# ---------------- Helper functions ----------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_pdf(filepath: str) -> str:
    text = ""
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        text += f"\n[Error extracting PDF: {e}]\n"
    return text

def extract_text_docx(filepath: str) -> str:
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    except Exception as e:
        text += f"\n[Error extracting DOCX: {e}]\n"
    return text

def extract_skills(text: str):
    found = []
    lower = text.lower()
    for skill in ALL_SKILLS:
        if skill.lower() in lower:
            found.append(skill)
    return found

# ---------------- Routes ----------------

@app.route("/", methods=["GET", "POST"])
def upload_resume():
    """
    Upload page: GET shows a form; POST saves file, extracts text & skills,
    then renders result.html
    """
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or file.filename == "":
            return "No file selected", 400
        if not allowed_file(file.filename):
            return "Invalid file type. Only PDF and DOCX allowed.", 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # extract text
        if filename.lower().endswith(".pdf"):
            text = extract_text_pdf(filepath)
        else:
            text = extract_text_docx(filepath)

        # extract skills
        skills_found = extract_skills(text)
        skills_str = ",".join(skills_found)  # used in link to job page

        return render_template("result.html",
                               text=text,
                               skills=skills_found,
                               skills_str=skills_str,
                               filename=filename)
    # GET
    return render_template("upload.html")


@app.route("/job", methods=["GET", "POST"])
def job_description():
    """
    Job page:
     - GET: shows job description form (accepts skills via ?skills=...)
     - POST: compares resume skills (from query string) with JD text
    """
    skills_param = request.args.get("skills", "")
    resume_skills = skills_param.split(",") if skills_param else []

    if request.method == "POST":
        job_desc = request.form.get("job_desc", "")
        job_desc_lower = job_desc.lower()

        matched_skills = [s for s in resume_skills if s and s.lower() in job_desc_lower]
        match_score = round(len(matched_skills) / len(resume_skills) * 100, 2) if resume_skills else 0

        return render_template("job_result.html",
                               resume_skills=resume_skills,
                               matched_skills=matched_skills,
                               match_score=match_score,
                               job_desc=job_desc)
    # GET
    return render_template("job.html", skills=skills_param)


# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
