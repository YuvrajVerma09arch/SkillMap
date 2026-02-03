import os
from groq import Groq

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key) if api_key else None

def generate_interview_question(role, topic, resume_text=""):
    client = get_client()
    if not client: return "Error: AI not connected."

    prompt = f"""
    You are an expert Technical Interviewer conducting a mock interview for a {role} position.
    Focus Area: {topic}.
    
    Candidate Context (Resume Snippet):
    {resume_text[:2000]}
    
    Task: Generate ONE specific, challenging interview question.
    
    Rules:
    1. Address the candidate directly as "you". (e.g., "Tell me about a time you...")
    2. Do NOT ask generic questions like "Tell me about yourself" unless it's the very first turn.
    3. Make it relevant to their resume if possible.
    4. Output ONLY the question text. No intro/outro.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Tell me about your experience with {topic}."

def evaluate_answer(question, user_answer):
    client = get_client()
    if not client: return {"feedback": "Error", "improvement_tip": "Check API Key"}

    prompt = f"""
    You are a Senior Interview Coach.
    
    Question Asked: "{question}"
    Candidate's Answer: "{user_answer}"
    
    Task: Evaluate the answer.
    
    OUTPUT JSON FORMAT:
    {{
        "feedback": "Direct feedback addressing the user as 'You'. Be constructive but critical. Mention what they missed.",
        "improvement_tip": "One specific actionable tip to improve this answer (e.g. 'Use the STAR method' or 'Mention X specific tool')."
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        import json
        return json.loads(completion.choices[0].message.content)
    except Exception:
        return {
            "feedback": "Your answer was recorded, but I couldn't generate detailed feedback right now.", 
            "improvement_tip": "Try to provide more specific examples next time."
        }