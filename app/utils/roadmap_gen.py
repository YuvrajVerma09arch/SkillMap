import os
import json
from groq import Groq

# 1. SETUP CLIENT
# This looks for GROQ_API_KEY in your environment
def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        return None
    return Groq(api_key=api_key)

def generate_roadmap(current_skills, target_role):
    client = get_client()
    if not client:
        return []

    print(f"Generating roadmap for {target_role} via Groq...")

    prompt = f"""
    Act as a Senior Career Mentor. 
    User's Current Skills: {current_skills}
    User's Target Role: {target_role}
    
    Create a detailed step-by-step learning roadmap.
    
    STRICT FORMATTING RULES:
    1. Output ONLY valid JSON. Do not write "Here is your JSON" or use markdown code blocks.
    2. The JSON must be a list of objects.
    3. Structure:
    [
        {{
            "title": "Month 1: [Topic]",
            "description": "What to learn...",
            "resources": ["Resource 1", "Resource 2"],
            "project_idea": "Build X"
        }}
    ]
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Reliable and fast
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5, # Low temperature = more consistent JSON
            stop=None,
        )
        
        # Extract content
        raw_text = completion.choices[0].message.content
        
        # Clean up (Remove markdown wrappers if the AI adds them)
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        roadmap_data = json.loads(clean_text)
        return roadmap_data

    except Exception as e:
        print(f"Groq API Error: {e}")
        # Fallback for debugging: Print what the AI actually sent if JSON parsing fails
        return []

# --- Quick Test Block ---
if __name__ == "__main__":
    # Test command: export GROQ_API_KEY="your_key" && python app/utils/roadmap_gen.py
    
    # Test Data
    skills = "Python Basics"
    role = "AI Engineer"
    
    result = generate_roadmap(skills, role)
    
    if result:
        print("\nSUCCESS! Groq generated this JSON:\n")
        print(json.dumps(result, indent=2))
    else:
        print("\nFAILED. Check error message above.")