import os
import json
import pdfplumber
from groq import Groq

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def analyze_resume(resume_path, job_description):
    # 1. Setup Groq Client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        return {"score": 0, "missing_keywords": ["Server Error: API Key Missing"], "summary": "System configuration error."}
    
    client = Groq(api_key=api_key)

    # 2. Extract Text
    resume_text = extract_text_from_pdf(resume_path)
    if not resume_text or len(resume_text) < 50:
        return {"score": 0, "missing_keywords": ["Error: PDF empty or unreadable"], "summary": "Could not read file."}

    # 3. The "Recruiter" Prompt (Smart AI Logic)
    prompt = f"""
    Act as a strict Technical Recruiter.
    
    JOB DESCRIPTION:
    {job_description}
    
    CANDIDATE RESUME:
    {resume_text[:6000]} 
    
    Task: Evaluate this candidate against the job description.
    
    STRICT JSON OUTPUT FORMAT (No markdown, just JSON):
    {{
        "match_score": (integer 0-100),
        "missing_required_skills": ["Critical Skill 1", "Critical Skill 2"],
        "explanation": ["Point 1: Why the score is X", "Point 2: What is good/bad"]
    }}
    
    Rules:
    - Be strict. If they lack a required skill (like Python or AWS) explicitly mentioned in JD, deduct points.
    - If the resume is irrelevant (e.g., Chef resume for Coding job), score < 20.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, # Low temp = consistent, factual results
            response_format={"type": "json_object"}
        )
        
        # 4. Parse Result
        raw_json = completion.choices[0].message.content
        result = json.loads(raw_json)
        
        # Ensure keys match what our HTML expects
        return {
            "match_score": result.get("match_score", 0),
            "missing_required_skills": result.get("missing_required_skills", []),
            "explanation": result.get("explanation", ["Analysis failed."])
        }

    except Exception as e:
        print(f"Groq Analysis Error: {e}")
        return {"match_score": 0, "missing_required_skills": ["AI Error"], "explanation": ["Could not process resume."]}