import os
from langfuse import Langfuse

def setup_prompts():
    client = Langfuse()

    print("Creating day13-chat prompt version 1 (baseline, production)...")
    prompt_v1 = client.create_prompt(
        name="day13-chat",
        type="text",
        prompt="Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}",
        labels=["baseline", "production"],
    )
    print(f"Created version {prompt_v1.version}")

    print("Creating day13-chat prompt version 2 (candidate)...")
    prompt_v2 = client.create_prompt(
        name="day13-chat",
        type="text",
        prompt="Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n[Instruction: Keep responses highly concise]",
        labels=["candidate"],
    )
    print(f"Created version {prompt_v2.version}")

if __name__ == "__main__":
    if "pk-lf" not in os.getenv("LANGFUSE_PUBLIC_KEY", ""):
        print("Please set your real LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env first.")
    else:
        setup_prompts()
        print("Done!")
