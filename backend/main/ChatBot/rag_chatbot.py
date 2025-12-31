"""
RAG Chatbot - Main Entry Point (Step 5) - Updated for v2.1
Supports both GitHub and Gmail vector databases
Run with: python rag_chatbot.py [--github-db PATH] [--gmail-db PATH]
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure backend package directory is on sys.path so imports like
# `from core.ChatBot.chatbot import RAGChatbot` work when executed directly
_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

from core.ChatBot.chatbot import RAGChatbot


def find_latest_vector_db(db_type="multi-index"):
    """Find the multi-index vector database (replaces single-index)"""
    multi_index_dir = Path("../../data/VectorDB/multi_index")

    if not multi_index_dir.exists():
        return None

    # Multi-index is a single directory with subdirectories per type
    if multi_index_dir.exists():
        # Check if it has the expected structure
        has_structure = any(
            (multi_index_dir / idx_type / "faiss.index").exists()
            for idx_type in ["code", "commit", "pr", "issue", "documentation", "all"]
        )
        if has_structure:
            return str(multi_index_dir)
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="RAG Chatbot v2.1 - GitHub + Gmail Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect latest databases
  python rag_chatbot.py
  
  # Specify multi-index database
  python rag_chatbot.py --github-db data/VectorDB/multi_index
  
  # Use multi-index with Gmail database
  python rag_chatbot.py --github-db data/VectorDB/multi_index --gmail-db data/VectorDB/gmail_chunks
  
  # Use Anthropic Claude
  python rag_chatbot.py --provider anthropic
  
  # Use local Ollama
  python rag_chatbot.py --provider ollama --model llama3.2
  
  # Single question mode
  python rag_chatbot.py --query "How does authentication work?"
  
  # Generate questions from codebase
  python rag_chatbot.py --query "Generate 10 questions about the authentication system"
  
  # Enable verbose mode
  python rag_chatbot.py --verbose --query "How do I set up the environment?"

Environment Variables:
  OPENAI_API_KEY      - For OpenAI provider
  ANTHROPIC_API_KEY   - For Anthropic provider
        """
    )

    parser.add_argument(
        '--github-db',
        dest='github_db_path',
        help='Path to GitHub vector database directory'
    )
    parser.add_argument(
        '--gmail-db',
        dest='gmail_db_path',
        help='Path to Gmail vector database directory'
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'anthropic', 'ollama'],
        default='openai',
        help='LLM provider (default: openai)'
    )
    parser.add_argument(
        '--model',
        help='Model name (optional, uses provider default)'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='LLM temperature 0-1 (default: 0.7)'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of chunks to retrieve (default: 5)'
    )
    parser.add_argument(
        '--query',
        help='Single query (non-interactive mode)'
    )
    parser.add_argument(
        '--filter-type',
        help='Filter by chunk type (function, class, documentation, email, etc.)'
    )
    parser.add_argument(
        '--hybrid',
        action='store_true',
        default=True,
        help='Enable hybrid retrieval with metadata boosting (default: enabled)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed retrieval information'
    )

    args = parser.parse_args()

    # Auto-detect multi-index vector DB if not provided
    github_db_path = args.github_db_path
    gmail_db_path = args.gmail_db_path

    if not github_db_path:
        print("🔍 Auto-detecting multi-index vector database...")

        github_db_path = find_latest_vector_db("multi-index")

        if github_db_path:
            print(f"✅ Found Multi-Index DB: {github_db_path}")
        else:
            print("❌ No multi-index vector database found in ../../data/VectorDB/multi_index/")
            print("\nRun step 4 first to build vector database:")
            print("  python core/VectorDB/build_indices.py")
            sys.exit(1)

        print()

    # Verify multi-index DB exists
    if not github_db_path:
        print(f"❌ Multi-index vector database not found")
        sys.exit(1)
    
    if not Path(github_db_path).exists():
        print(f"❌ Multi-index vector database not found: {github_db_path}")
        sys.exit(1)
    
    # Check for at least one index in multi-index directory
    has_indices = any(
        (Path(github_db_path) / idx_type / "faiss.index").exists()
        for idx_type in ["code", "commit", "pr", "issue", "documentation", "all"]
    )
    if not has_indices:
        print(f"❌ Invalid multi-index database (missing index files): {github_db_path}")
        print("Expected structure: multi_index/<type>/faiss.index")
        sys.exit(1)

    print(f"{'='*70}")
    print(f"🚀 STARTING RAG CHATBOT v2.1")
    print(f"{'='*70}\n")

    # Create chatbot (multi-index only)
    try:
        chatbot = RAGChatbot(
            vector_db_path=github_db_path,  # Multi-index path
            gmail_db_path=gmail_db_path,
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            top_k=args.top_k,
            use_hybrid_retrieval=args.hybrid,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        print(f"\nTroubleshooting:")

        if args.provider == "openai":
            print("  - Set OPENAI_API_KEY environment variable")
            print("  - Install: pip install openai")
        elif args.provider == "anthropic":
            print("  - Set ANTHROPIC_API_KEY environment variable")
            print("  - Install: pip install anthropic")
        elif args.provider == "ollama":
            print("  - Install Ollama from https://ollama.ai")
            print("  - Run: ollama pull llama3.2")
            print("  - Ensure Ollama is running: ollama serve")

        sys.exit(1)

    # Build filters if specified
    filters = {}
    if args.filter_type:
        filters['chunk_type'] = args.filter_type

    # Single query mode
    if args.query:
        print(f"{'='*70}")
        print(f"📝 SINGLE QUERY MODE")
        print(f"{'='*70}\n")
        print(f"You: {args.query}\n")

        result = chatbot.chat(args.query, filters if filters else None)

        print(f"\n🤖 Assistant:\n")
        print(result['answer'])

        # Show sources
        if result['sources']:
            print(f"\n{'='*70}")
            print(f"📚 Sources ({result['chunks_retrieved']} chunks retrieved):")
            print(f"{'='*70}")
            for i, source in enumerate(result['sources'], 1):
                source_db = source.get('source_db', 'unknown')
                if source_db == 'github':
                    print(f"  {i}. [GitHub] {source.get('file', 'unknown')}")
                    print(f"     Type: {source['type']} | Score: {source['score']:.3f}")
                elif source_db == 'gmail':
                    print(f"  {i}. [Gmail] {source.get('subject', 'No Subject')}")
                    print(f"     From: {source.get('sender', 'Unknown')} | Score: {source['score']:.3f}")

                if 'context_role' in source:
                    print(f"     Role: {source['context_role']}")

        # Show related knowledge
        related = result.get('related_knowledge', {})
        if any(related.values()):
            print(f"\n{'='*70}")
            print(f"🔗 Related Knowledge:")
            print(f"{'='*70}")

            if related.get('issues'):
                print(f"\n  Issues ({len(related['issues'])}):")
                for issue in related['issues'][:3]:
                    print(f"    - Issue #{issue['number']}: {issue['title']}")

            if related.get('prs'):
                print(f"\n  Pull Requests ({len(related['prs'])}):")
                for pr in related['prs'][:3]:
                    print(f"    - PR #{pr['number']}: {pr['title']}")

            if related.get('emails'):
                print(f"\n  Emails ({len(related['emails'])}):")
                for email in related['emails'][:3]:
                    print(f"    - {email['subject']} (from {email['sender']})")

        # Show flow diagram info
        if result.get('has_diagram'):
            print(f"\n{'='*70}")
            print(f"📊 Flow diagram generated!")
            print(f"{'='*70}")

        print(f"\n{'='*70}\n")

    # Interactive mode
    else:
        print(f"{'='*70}")
        print(f"💬 INTERACTIVE MODE")
        print(f"{'='*70}")
        print(f"Type your questions below. Commands:")
        print(f"  - 'exit' or 'quit': Exit the chatbot")
        print(f"  - 'clear': Clear conversation history")
        print(f"  - 'stats': Show database statistics")
        print(f"{'='*70}\n")

        while True:
            try:
                query = input("You: ").strip()

                if not query:
                    continue

                if query.lower() in ['exit', 'quit']:
                    print("\n👋 Goodbye!")
                    break

                if query.lower() == 'clear':
                    chatbot.clear_history()
                    continue

                if query.lower() == 'stats':
                    stats = chatbot.get_stats()
                    print(f"\n📊 Database Statistics:")

                    if 'github' in stats:
                        print(f"\n  GitHub Database:")
                        print(f"    Total chunks: {stats['github']['total_chunks']}")
                        print(f"    Chunk types: {stats['github'].get('chunk_types', {})}")

                    if 'gmail' in stats:
                        print(f"\n  Gmail Database:")
                        print(f"    Total chunks: {stats['gmail']['total_chunks']}")
                        print(f"    Chunk types: {stats['gmail'].get('chunk_types', {})}")

                    print(f"\n  Conversation turns: {stats['conversation_length']}")
                    print(f"  Features: {', '.join(stats['features'][:5])}\n")
                    continue

                print()
                result = chatbot.chat(query, filters if filters else None)

                print(f"🤖 Assistant:\n")
                print(result['answer'])

                if args.verbose and result['sources']:
                    print(f"\n📚 Sources:")
                    for i, source in enumerate(result['sources'][:5], 1):
                        source_db = source.get('source_db', 'unknown')
                        if source_db == 'github':
                            print(f"  {i}. [GitHub] {source.get('file', 'unknown')} ({source['type']}) - {source['score']:.3f}")
                        elif source_db == 'gmail':
                            print(f"  {i}. [Gmail] {source.get('subject', 'No Subject')} - {source['score']:.3f}")

                print()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                if args.verbose:
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    main()