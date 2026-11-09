from Backend.memory_extractor import extract_and_save_user_memories
from Backend.memory import get_memories


def main():
    print("=== YONA MEMORY DATABASE TEST ===")

    user_message = input("User message: ")

    result = extract_and_save_user_memories(user_message)

    print("\n=== EXTRACTION RESULT ===")
    print(f"Extracted: {result['extracted']}")
    print(f"Saved: {result['saved']}")
    print(f"Duplicates: {result['duplicates']}")

    print("\n=== STORED MEMORIES ===")

    memories = get_memories()

    for memory in memories:
        print(
            f"[{memory['category']}] "
            f"{memory['content']}"
        )


if __name__ == "__main__":
    main()