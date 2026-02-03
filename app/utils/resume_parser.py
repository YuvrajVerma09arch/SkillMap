import os
import json
import PyPDF2
from groq import Groq

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def analyze_resume(resume_path, job_description):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"match_score": 0, "missing_required_skills": ["API Key Missing"], "explanation": ["System config error."]}
    
    client = Groq(api_key=api_key)

    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text or len(resume_text) < 50:
        return {"match_score": 0, "missing_required_skills": ["Unreadable PDF"], "explanation": ["The file appears empty or encrypted."]}

    # THE "RUTHLESS RECRUITER" PROMPT
    prompt = f"""
    You are a Senior Technical Recruiter at a top tech company. 
    Evaluate the Candidate Resume against the Job Description.

    JOB DESCRIPTION:
    {job_description}

    CANDIDATE RESUME:
    {resume_text[:6000]}

    TASK:
    1. Identify key hard skills (languages, frameworks, tools) missing from the resume.
    2. Assign a match score (0-100). Be strict. 100 means perfect match.
    3. Provide brief, direct feedback on why points were deducted.

    OUTPUT JSON FORMAT:
    {{
        "match_score": 75,
        "missing_required_skills": ["Docker", "Kubernetes", "React"],
        "explanation": [
            "Candidate lacks containerization experience required for this role.",
            "Strong Python background, but this role requires more Frontend experience."
        ]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, # Low temp = consistent scoring
            response_format={"type": "json_object"}
        )
        
        result = json.loads(completion.choices[0].message.content)
        
        return {
            "match_score": result.get("match_score", 0),
            "missing_required_skills": result.get("missing_required_skills", []),
            "explanation": result.get("explanation", ["Analysis failed."])
        }

    except Exception as e:
        print(f"Groq Analysis Error: {e}")
        return {"match_score": 0, "missing_required_skills": ["AI Analysis Failed"], "explanation": ["Please try again."]}