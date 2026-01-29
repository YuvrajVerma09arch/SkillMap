import os
import json
from groq import Groq

# 1. GENERATE QUESTION (Now Context-Aware)
def generate_interview_question(role, topic, resume_text=None, difficulty="Medium"):
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    # If we have a resume, we tell the AI to ask about IT.
    context_instruction = ""
    if resume_text:
        context_instruction = f"""
        CONTEXT: The candidate has this experience on their resume:
        "{resume_text[:1000]}..." (truncated)
        
        INSTRUCTION: Ask a specific question related to a project or skill found in the resume snippet above, 
        but connect it to the role of {role}.
        """
    else:
        context_instruction = f"INSTRUCTION: Ask a standard behavioral or technical question for a {role}."

    prompt = f"""
    Act as a Senior Technical Recruiter.
    Role: {role}
    Topic: {topic}
    Difficulty: {difficulty}
    
    {context_instruction}
    
    Output ONLY the question text. No intro, no quotes.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8 # Higher temp = more creative questions
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Gen Error: {e}")
        return "Tell me about a time you solved a difficult technical problem."

# 2. EVALUATE ANSWER (The Grader)
def evaluate_answer(question, user_answer):
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    prompt = f"""
    You are a Hiring Manager.
    Question: "{question}"
    Candidate Answer: "{user_answer}"
    
    Task: Grade this answer.
    
    STRICT JSON OUTPUT FORMAT:
    {{
        "score": (integer 1-10),
        "feedback": "2 sentences on what was good/bad.",
        "improvement_tip": "One specific tip to make it a 10/10."
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, # Low temp = strict grading
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Eval Error: {e}")
        return {"score": 0, "feedback": "Could not grade.", "improvement_tip": "Try again."}