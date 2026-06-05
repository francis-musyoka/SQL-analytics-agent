"""Interactive command-line interface. Run with: python -m src.cli"""
from src.agent import answer_question


def main():
    print("SQL Analytics Agent (Chinook). Ask a question. Ctrl-C to quit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        if not question:
            continue
        result = answer_question(question)
        print("\nAnswer:", result["answer"])
        if result["sql"]:
            print("\nSQL the agent ran:")
            for q in result["sql"]:
                print("  -", q)


if __name__ == "__main__":
    main()
