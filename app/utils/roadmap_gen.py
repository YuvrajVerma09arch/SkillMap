import os
import json
from groq import Groq

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key) if api_key else None

def generate_roadmap(current_skills, target_role):
    client = get_client()
    if not client:
        return []

    print(f"Generating roadmap for {target_role}...")

    prompt = f"""
    Act as a Senior Career Mentor.
    User Skills: {current_skills}
    Target Role: {target_role}
    
    Create a 3-6 month step-by-step learning roadmap.
    
    OUTPUT JSON FORMAT (List of objects):
    {{
        "roadmap": [
            {{
                "month": "Month 1",
                "topic": "Foundations & Syntax",
                "description": "Master the basics of...",
                "action_items": ["Learn X", "Build simple Y console app"]
            }},
            {{
                "month": "Month 2",
                "topic": "Frameworks & Tools",
                "description": "Start working with...",
                "action_items": ["Create a REST API", "Learn Database integration"]
            }}
        ]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        data = json.loads(completion.choices[0].message.content)
        # Handle cases where AI wraps list in a key or returns direct list
        return data.get("roadmap", [])

    except Exception as e:
        print(f"Groq Error: {e}")
        return []