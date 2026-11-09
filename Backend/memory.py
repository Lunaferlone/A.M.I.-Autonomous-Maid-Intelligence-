
import sqlite3
import uuid
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "Database" / "yona_memory.db"


# Common words that do not provide useful search meaning.
# These are filters, not language restrictions.
STOPWORDS = {
    "en": {
        "what", "do", "does", "did", "you", "your",
        "i", "am", "is", "are", "the", "a", "an",
        "of", "to", "in", "on", "at", "for", "and",
        "or", "but", "about", "with", "my", "me",
        "know", "remember", "tell", "show", "can",
        "could", "would", "should", "how", "why",
        "when", "where", "which", "who", "please",
        "have", "has", "had", "it", "this", "that"
    },

    "id": {
        "apa", "yang", "dan", "atau", "di", "ke",
        "dari", "untuk", "dengan", "tentang", "saya",
        "aku", "gw", "gue", "lo", "lu", "kamu",
        "gimana", "bagaimana", "kenapa", "siapa",
        "kapan", "dimana", "ingat", "tahu", "tau",
        "apakah", "bisa", "boleh", "punya", "ini",
        "itu", "nya", "dong", "sih", "deh", "ya",
        "kok", "aja", "juga", "sudah", "udah",
        "belum", "lagi", "adalah", "sebuah"
    },

    "ja": {
        "私", "あなた", "これ", "それ", "あれ",
        "何", "どう", "です", "ます", "か",
        "の", "は", "が", "を", "に", "へ",
        "と", "で", "も", "から", "まで",
        "について", "そして", "また"
    }
}


def get_connection():
    """Create a database connection."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():
    """Initialize all memory tables and search indexes."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversation_session
            ON conversation_messages(session_id, id)
        """)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS conversation_search
            USING fts5(
                content,
                session_id UNINDEXED,
                role UNINDEXED,
                message_id UNINDEXED
            )
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS conversation_insert
            AFTER INSERT ON conversation_messages
            BEGIN
                INSERT INTO conversation_search (
                    content,
                    session_id,
                    role,
                    message_id
                )
                VALUES (
                    new.content,
                    new.session_id,
                    new.role,
                    new.id
                );
            END;
        """)

        conn.execute("""
            INSERT INTO conversation_search (
                content,
                session_id,
                role,
                message_id
            )
            SELECT
                content,
                session_id,
                role,
                id
            FROM conversation_messages
            WHERE id NOT IN (
                SELECT message_id FROM conversation_search
            )
        """)


def save_memory(category, content):
    """Save a permanent memory without creating duplicates."""

    category = category.strip().lower()
    content = content.strip()

    if not category or not content:
        return False

    with get_connection() as conn:

        existing = conn.execute(
            """
            SELECT id FROM memories
            WHERE category = ? AND content = ?
            LIMIT 1
            """,
            (category, content)
        ).fetchone()

        if existing:
            return False

        conn.execute(
            """
            INSERT INTO memories (category, content)
            VALUES (?, ?)
            """,
            (category, content)
        )

        return True


def get_memories(category=None):
    """Retrieve stored memories."""

    with get_connection() as conn:

        if category:
            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE category = ?
                ORDER BY id DESC
                """,
                (category,)
            ).fetchall()

        else:
            rows = conn.execute(
                """
                SELECT * FROM memories
                ORDER BY id DESC
                """
            ).fetchall()

        return [dict(row) for row in rows]


def delete_memory(memory_id):
    """Delete a specific memory."""

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,)
        )


def create_session():
    """Create a new conversation session."""

    return str(uuid.uuid4())


def save_message(session_id, role, content):
    """Save a conversation message."""

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_messages (
                session_id,
                role,
                content
            )
            VALUES (?, ?, ?)
            """,
            (session_id, role, content)
        )


def get_session_messages(session_id):
    """Retrieve messages from a specific session."""

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM conversation_messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def detect_language(query):
    """Detect the language using basic character patterns."""

    if re.search(r"[\u3040-\u30ff\u3400-\u9fff]", query):
        return "ja"

    if re.search(r"\b(apa|yang|kamu|saya|gw|gue|gimana|kenapa)\b", query.lower()):
        return "id"

    return "en"


def extract_keywords(query):
    """Extract meaningful keywords based on the detected language."""

    language = detect_language(query)
    stopwords = STOPWORDS.get(language, set())

    if language == "ja":
        words = re.findall(
            r"[\u3040-\u30ff\u3400-\u9fff]+",
            query
        )
    else:
        words = re.findall(r"\w+", query.lower())

    keywords = []

    for word in words:

        if word in stopwords:
            continue

        if len(word) <= 1:
            continue

        keywords.append(word)

    return list(dict.fromkeys(keywords))


def calculate_relevance(content, keywords):
    """Calculate keyword matching score."""

    content = content.lower()

    score = 0

    for keyword in keywords:
        if keyword in content:
            score += 1

    return score


def search_memories(query, limit=5):
    """Search user conversation history using relevant keywords."""

    keywords = extract_keywords(query)

    if not keywords:
        return []

    search_query = " OR ".join(
        f'"{word}"' for word in keywords
    )

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                message_id,
                session_id,
                role,
                content
            FROM conversation_search
            WHERE conversation_search MATCH ?
            AND role = 'user'
            """,
            (search_query,)
        ).fetchall()

        results = []

        for row in rows:

            memory = dict(row)

            score = calculate_relevance(
                memory["content"],
                keywords
            )

            memory["relevance"] = score

            if score > 0:
                results.append(memory)

        results.sort(
            key=lambda item: (
                item["relevance"],
                item["message_id"]
            ),
            reverse=True
        )

        return results[:limit]


def search_saved_memories(query, limit=5):
    """Search permanent memories using relevant keywords."""

    keywords = extract_keywords(query)

    if not keywords:
        return []

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT
                id,
                category,
                content,
                created_at
            FROM memories
            """
        ).fetchall()

        results = []

        for row in rows:

            memory = dict(row)

            score = calculate_relevance(
                memory["content"],
                keywords
            )

            memory["relevance"] = score

            if score > 0:
                results.append(memory)

        results.sort(
            key=lambda item: (
                item["relevance"],
                item["id"]
            ),
            reverse=True
        )

        return results[:limit]


def build_memory_context(query, limit=5):
    """Build context using relevant permanent memories and conversations."""

    saved_memories = search_saved_memories(query, limit)
    past_conversations = search_memories(query, limit)

    context = []

    if saved_memories:
        context.append("[PERMANENT MEMORIES]")

        for memory in saved_memories:
            context.append(
                f"[{memory['category']}] {memory['content']}"
            )

    if past_conversations:
        context.append("\n[PAST USER CONVERSATIONS]")

        for memory in past_conversations:
            context.append(
                f"[{memory['role']}] {memory['content']}"
            )

    return "\n".join(context)


initialize_database()
