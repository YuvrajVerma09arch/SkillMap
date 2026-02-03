from google import genai
import os

def list_my_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        return

    client = genai.Client(api_key=api_key)
    
    print("--- Contacting Google API ---")
    try:
        # This lists all models available to your specific Key
        pager = client.models.list()
        
        print("\nAVAILABLE MODELS FOR YOU:")
        print(f"{'Model Name':<30} | {'Supported?'}")
        print("-" * 50)
        
        found_any = False
        for model in pager:
            # We only care about models that can 'generateContent'
            if "generateContent" in model.supported_generation_methods:
                # Remove the "models/" prefix if present to get the clean ID
                clean_name = model.name.replace("models/", "")
                print(f"{clean_name:<30} | ✅ YES")
                found_any = True
                
        if not found_any:
            print("\nWARNING: No text-generation models found for this API Key.")
            print("Check if 'Generative AI API' is enabled in your Google Cloud Console.")

    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    list_my_models()