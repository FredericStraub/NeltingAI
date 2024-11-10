# test_config.py
from app.config import settings

def main():
    if settings.OPENAI_API_KEY:
        print("OPENAI_API_KEY loaded successfully.")
    else:
        print("Failed to load OPENAI_API_KEY.")

if __name__ == "__main__":
    main()