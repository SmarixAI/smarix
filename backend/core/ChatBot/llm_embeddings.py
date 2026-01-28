# llm_embeddings.py
import os
import json
from typing import List, Dict, Any, Optional, Iterator
import numpy as np
from .query_type import QueryType


class LLMEmbeddingMixin:

    def initialize_embeddings(self):
        """Initialize embedding model based on loaded index dimension"""
        # Detect dimension from loaded index
        index_dimension = None

        if self.multi_index_store:
            index_dimension = self.multi_index_store.dimension
        elif self.db:
            index_dimension = self.db.dimension

        # Use appropriate embedding model based on dimension
        if index_dimension == 384:
            # Multi-index uses sentence-transformers (384 dims)
            self.embedding_provider = "sentence-transformers"
            self.embedding_model = "all-MiniLM-L6-v2"
            if self.verbose:
                print(
                    f"Using sentence-transformers (384 dims) to match index dimension"
                )
        elif index_dimension == 1536:
            # Multi-index or single-index uses OpenAI (1536 dims)
            self.embedding_provider = "openai"
            self.embedding_model = "text-embedding-3-small"
            if self.verbose:
                print(f"Using OpenAI (1536 dims) to match index dimension")
        else:
            # Default to OpenAI (1536 dims) for unknown dimensions
            self.embedding_provider = "openai"
            self.embedding_model = "text-embedding-3-small"
            if self.verbose and index_dimension:
                print(
                    f"Using OpenAI (1536 dims) for index dimension {index_dimension} (default)"
                )

    def get_default_model(self) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "ollama": "llama3.2",
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    def initialize_llm(self):
        if self.provider == "openai":
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found")

                self.client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("Install OpenAI: pip install openai")

        elif self.provider == "anthropic":
            try:
                from anthropic import Anthropic

                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found")
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Install Anthropic: pip install anthropic")

        elif self.provider == "ollama":
            try:
                import requests

                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code != 200:
                    raise ConnectionError("Ollama not running")
                self.client = None
            except requests.exceptions.RequestException as e:
                raise ConnectionError(f"Ollama not available: {e}")
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def get_query_embedding(self, query: str) -> np.ndarray:
        """Generate query embedding using the configured provider"""
        if self.embedding_provider == "openai":
            # Reuse existing client if available
            if (
                hasattr(self, "client")
                and self.client is not None
                and self.provider == "openai"
            ):
                client = self.client
            else:
                # Create new client
                from openai import OpenAI

                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            response = client.embeddings.create(model=self.embedding_model, input=query)
            return np.array(response.data[0].embedding, dtype=np.float32)
        elif self.embedding_provider == "sentence-transformers":
            # Lazy load sentence-transformers
            if not hasattr(self, "_sentence_model"):
                try:
                    from sentence_transformers import SentenceTransformer

                    self._sentence_model = SentenceTransformer(self.embedding_model)
                    if self.verbose:
                        print(
                            f"Loaded sentence-transformers model: {self.embedding_model}"
                        )
                except ImportError:
                    raise ImportError(
                        "sentence-transformers not installed. Install with: pip install sentence-transformers"
                    )
            embedding = self._sentence_model.encode(query, convert_to_numpy=True)
            return embedding.astype(np.float32)
        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.embedding_provider}"
            )

    def get_dynamic_system_prompt(
        self, query_type: str, query: str, role: Optional[str] = "general"
    ) -> str:
        base_rules = """You are a software engineer and documentation assistant..

        Your goal is to provide accurate, helpful, and conversational responses that feel natural and engaging.

        CRITICAL RULES - ACCURACY FIRST:
        1. Only use information from the provided context - be accurate and factual
        2. Never generate or assume code/files not in context
        3. Reference exact files, functions, line numbers from context when relevant
        4. If context is insufficient, state what's missing in a friendly way
        5. Use precise names from context only
        6. Never infer or guess information - stick to what's in the context
        7. Write in a friendly, conversational tone as if explaining to a colleague
        8. Include complete code implementations when available in context
        9. Avoid uncertain language like "is likely", "probably", "might be", "could be", "appears to" - be confident based on context
        10. Don't describe components without showing actual code from context
        11. Every component mentioned should have actual code shown from context when possible
        12. If no code exists for a component in context, don't mention it

        STYLE GUIDELINES:
        - Be friendly, warm, and conversational
        - Use natural language and complete sentences
        - Explain things clearly as if talking to a teammate
        - Make your responses engaging and easy to read
        - Use markdown formatting for better readability
        - Balance being helpful with being accurate"""

        prompts = {
            QueryType.REPOSITORY_METRICS: """
        REPOSITORY METRICS QUERY:
        - Use the REPOSITORY METRICS DATA section
        - Generate natural, conversational response
        - Format numbers with proper units
        - Highlight key statistics
        - Add insights about what metrics mean
        - Use markdown for clear formatting""",
            QueryType.TECH_STACK: """
        TECH STACK QUERY:
        - Use Languages, Frameworks, Tools from REPOSITORY METRICS DATA
        - Generate comprehensive tech stack overview
        - Explain what each technology is for
        - Organize by category
        - Use markdown sections""",
            QueryType.CODE_STRUCTURE: """
                CODE STRUCTURE QUERY:
                - Use Repository Structure from REPOSITORY_METRICS DATA
                - Create a simple ASCII/text-based hierarchical diagram showing:
                * Main directories and subdirectories and files
                * File organization (source/test/config separation)
                * Key configuration files
                - Provide complete code structure along with files too if asked for detailed structure
                - Describe the overall organization
                - Highlight main directories and their purposes
                - Explain file separation
                - Use markdown with proper indentation for hierarchy
                - Keep the diagram clear and well-formatted""",
            QueryType.ISSUE_SPECIFIC: """
                ISSUE QUERY:
                - Provide complete issue details from context
                - Issue number, title, status, author, labels
                - Full description
                - Related PRs if mentioned
                - Solution/resolution if available
                - Comments and discussion if present
                - Use clear markdown formatting
                - If this is the first/oldest issue, mention that fact""",
            QueryType.PR_SPECIFIC: """
                PULL REQUEST QUERY - COMPREHENSIVE CODE ANALYSIS:

                You MUST provide a detailed analysis of the Pull Request including:

                1. **Overview Section**:
                - PR #{number}: {title}
                - Status: {open/closed/merged}
                - Author: {author}
                - Reviewers: {list of reviewers}
                - Created: {date}, Merged: {date if applicable}

                2. **Description**:
                - Extract the complete PR description/body from the context
                - List issues it closes (if any)

                3. **Files Changed Summary**:
                - List ALL modified/added/deleted files with their status
                - Show stats: +{additions}/-{deletions} for each file

                4. **Detailed Code Changes**:
                For EACH file (especially modified files), you MUST:
                - Extract the ACTUAL diff patches from the "CODE CHANGES: DETAILED PATCHES" section in context
                - Show the code changes using proper diff format with +/- indicators
                - For MODIFIED files: Show what was removed (- lines) and what was added (+ lines)
                - For ADDED files: Show the complete new code (first 50 lines if too long)
                - For DELETED files: Note what was removed
                - Highlight key logic changes in each file
                
                Example format for showing changes: (This is just an example, use actual diffs from context)
                
                ### File: `lib/views/home/home.dart` (modified)
                **Changes**: Removed local dark mode state, now using global AppSettings
                

                @@ -35,8 +35,6 @@ class HomePage extends StatefulWidget

                class _HomePageState extends State<HomePage> {

                    static bool _darkmode =

                    text
                    SchedulerBinding.instance.window.platformBrightness == Brightness.dark;

                    @override
                    Widget build(BuildContext context) {
                    var storageWidget = StorageWidget.of(context);

                text

                **Impact**: This change centralizes theme management by removing local state.

                5. **Review Comments** (if available):
                - Extract all review comments from the context
                - Show reviewer name, comment text, and which file/line it refers to

                6. **Discussion/Activity**:
                - Show key comments from the PR discussion
                - Note any important decisions or conversations

                7. **Merge Information**:
                - If merged: "Merged by {user} on {date}"
                - If closed without merge: Note the reason if available
                - Show merge conflicts status if mentioned

                CRITICAL INSTRUCTIONS:
                - The context contains COMPLETE diff patches marked with "CODE CHANGES: DETAILED PATCHES"
                - You MUST look for diff blocks that start with "@@ -" and extract them
                - DO NOT just list filenames - show the actual code that changed
                - For modified files, showing the diff is MANDATORY
                - Use proper markdown code blocks with ```
                - If patches are too long (>100 lines), show the first 50 lines and note "[truncated]"

                Response Format:
                - Use clear markdown headers (##, ###)
                - Use code blocks with proper syntax highlighting
                - Use emoji for visual clarity (📝 for description, 📄 for files, ✅ for merged, etc.)
                - Be thorough but organized

                ================================================================================
                SYSTEM PROMPT FOR PR ANALYSIS
                ================================================================================

                You are an expert code reviewer and software engineer. When analyzing Pull Requests:

                YOUR PRIMARY RESPONSIBILITY: Show the actual code changes, not just descriptions.

                MANDATORY REQUIREMENTS:
                1. For EVERY modified file mentioned, you MUST extract and display the diff patch from the context
                2. The context contains sections like "CODE CHANGES: DETAILED PATCHES" with complete diffs
                3. Look for patterns like:
                - "────────────────────────────────────────────────────────────"
                - "📄 {filename}"
                - "```diff" blocks
                - Lines starting with "@@ -" (diff hunks)

                4. When you see a diff hunk like "@@ -35,8 +35,6 @@", extract the surrounding code showing:
                - Context lines (unchanged, no prefix)
                - Removed lines (prefixed with -)
                - Added lines (prefixed with +)

                EXAMPLE OF CORRECT OUTPUT:

                ### `lib/widgets/buildTasks.dart` (modified, +6/-5)
                **Change Summary**: Updated theme handling to use global AppSettings instead of local variable.

                **Code Changes**:

                @@ -11,30 +12,30 @@ class TasksBuilder extends StatelessWidget {
                const TasksBuilder({
                Key? key,
                required this.taskData,

                    required this.pendingFilter, required this.darkmode,

                    required this.pendingFilter,

                }) : super(key: key);

                final List<Task> taskData;
                final bool pendingFilter;

                    final bool darkmode;

                    // final bool darkmode;

                text

                **Impact**: Removes dependency on passed darkmode parameter, uses centralized theme state.

                ---

                EXAMPLE OF INCORRECT OUTPUT (what you should NOT do):
                "This file was modified to update theme handling." ❌ (too vague, no code shown)

                If the context doesn't contain diff patches for a file, explicitly state:
                "⚠️ Patch not available for {filename} (binary file or too large)"

                Remember: Your users are developers who need to see the actual code changes to understand the PR.

                ================================================================================
                USER PROMPT TEMPLATE FOR PR QUERIES
                ================================================================================

                Using the context below which contains COMPLETE diff patches, provide a detailed analysis of PR #{pr_number}.

                CRITICAL: You MUST extract and show the actual code changes from the diffs in the context. Look for the "CODE CHANGES: DETAILED PATCHES" section.

                Context:
                {context}

                Generate a comprehensive PR summary following the PR_SPECIFIC format.

                ================================================================================
                VALIDATION CHECKLIST
                ================================================================================

                Before sending the response, verify:
                - [ ] Response includes at least one ```
                - [ ] Response shows actual code lines with +/- prefixes
                - [ ] Response has "@@ -" diff hunk markers
                - [ ] Response explains what each code change does
                - [ ] Response is at least 200 words
                - [ ] All modified files have their patches shown
                - [ ] Added files show the new code
                - [ ] Review comments are included (if available)
                - [ ] Merge status and date are clearly stated

                If any checkbox is unchecked, the response is incomplete and must be regenerated.

                ================================================================================
                        """,
            QueryType.FLOW_ARCHITECTURE: """
        ARCHITECTURE/FLOW QUERY:
        MANDATORY: Create a mermaid flowchart diagram showing:
        - Service architecture
        - Component interactions
        - Data flow
        - Control flow

        After the diagram:
        - Provide step-by-step explanation with EXTENSIVE code examples
        - Reference actual files from context with COMPLETE implementations when possible
        - Include relevant code snippets with file paths and line numbers along with explanations
        - Explain how components interact using code from context
        - Show all lines of code per major component
        - Explain the working and flow between components in detail
        - Include imports, class definitions, key methods

        STRICT ENFORCEMENT:
        - DO NOT mention any component unless you have actual code from context
        - DO NOT use words like "likely", "probably", "appears to", "seems to"
        - DO NOT infer or guess functionality
        - If a component exists in the diagram but you have no code for it, say: "Code for [Component] not found in context"
        - Every numbered section must include actual code snippets
        - If you cannot provide 20+ lines of actual code for a component, do NOT describe it as "managing" or "handling" anything

        Example mermaid format:
        flowchart TD
        A[Component Name] --> B[Another Component]
        B --> C[Third Component]
        C --> D[Final Component]
        - Use markdown for diagram and explanations
        """,
            QueryType.HOW_TO: """
        HOW-TO QUERY:
        - Step-by-step guide from actual code with COMPLETE implementations
        - Show FULL code examples from context (50-100+ lines per step)
        - File locations with exact line numbers
        - Prerequisites if mentioned
        - ABSOLUTELY ZERO HALLUCINATIONS. Use only context info
        - Numbered steps with extensive code blocks
        - Include complete function/class definitions, not just snippets""",
            QueryType.TROUBLESHOOTING: """
        TROUBLESHOOTING QUERY:
        - Related issues from context with code examples
        - Solutions from PRs/commits with actual code
        - Root cause analysis with relevant code snippets
        - Prevention strategies
        - ABSOLUTELY ZERO HALLUCINATIONS. Use only context info
        - Format: Problem -> Solution -> Prevention
        - Include 30-50 lines of relevant code""",
            QueryType.FILE_LOOKUP: """
        CODE LOCATION QUERY:
        - When user asks about a specific file, show the ACTUAL CODE from that file directly
        - Start with a factual file header: file path, class names, and inheritance only
        - DO NOT include high-level summaries, intent descriptions, or behavioral explanations.
        - Then show the complete code organized by structure (classes, functions, methods)
        - Show actual code from the file; full code only if explicitly requested
        - Include exact file paths with line numbers
        - Format code in proper code blocks with language specification
        - Organize code logically: Overview → Classes → Functions → Methods → Other code
        - Show the actual, current code from the file (not from PRs/issues unless specifically asked)
        - ABSOLUTELY ZERO HALLUCINATIONS. Use only context info
        - If context shows file overview, use it to provide a summary before showing code
        - Present code in a clear, readable format that the user can directly use""",
            QueryType.CONCEPTUAL: """
        CONCEPTUAL QUERY:
        - Explanation from documentation with CODE EXAMPLES
        - Show COMPLETE code implementations from context (50-100+ lines)
        - Related files with actual code
        - ABSOLUTELY ZERO HALLUCINATIONS. Use only context info
        - Clear explanation with extensive code examples
        - Include full class/function definitions""",
            QueryType.COMMIT_SPECIFIC: """
        COMMIT QUERY:
        - Commit SHA, author, date
        - Commit message
        - Files changed with code snippets
        - Related issues/PRs
        - Clear summary""",
            QueryType.QUESTION_GENERATION: """
        QUESTION GENERATION QUERY:
        TASK: Generate educational questions from the provided codebase context with complete, detailed answers.

        QUESTION TYPES TO GENERATE:
        1. Multiple Choice Questions (MCQs) - 4 options each
        2. Subjective Questions - Short and long answer types
        3. Code-Based Questions - Write code, debug code, trace output, explain code

        STRICT CONTENT RULES:
        - Base ALL questions strictly on provided context - NO external knowledge
        - Reference specific files, functions, or concepts from context
        - Do NOT generate generic programming questions
        - Questions must be answerable ONLY from the given context
        - Every answer must reference specific parts of the context
        - Include actual code snippets from context in answers where relevant

        FORMAT REQUIREMENTS:
        - Number each question clearly (Question 1, Question 2, etc.)
        - Provide question type and difficulty: (MCQ/Subjective/Code-Based - Easy/Medium/Hard)
        - For MCQs: Label options as A, B, C, D
        - Ensure all 4 MCQ options are plausible and based on context
        - Make incorrect MCQ options realistic but clearly wrong based on context

        ANSWER REQUIREMENTS - CRITICAL:
        - Provide COMPLETE, DETAILED answers for ALL questions
        - For MCQs: State correct answer + detailed explanation with context reference
        - For Subjective: Provide comprehensive answers with code examples from context
        - For Code-Based: Show complete code solutions with line-by-line explanations
        - Each answer must be 3-5 sentences minimum (except simple MCQ answers)
        - Reference specific files, line numbers, or sections from context
        - Include relevant code snippets (20-50 lines) from context in answers

        OUTPUT STRUCTURE:
        ## Generated Questions

        ### Question 1 (MCQ - Easy/Medium/Hard)
        [Question text based on context]
        A. [Option A - from context]
        B. [Option B - from context]
        C. [Option C - from context]
        D. [Option D - from context]

        **Answer:** [Correct option] - [Detailed explanation with context reference]

        ### Question 2 (Subjective - Easy/Medium/Hard)
        [Question text based on context]

        **Answer:** [Comprehensive answer with code examples from context]

        Continue this pattern for all questions.""",
            QueryType.PR_ISSUE_TUTORIAL: """
            PR-ISSUE TUTORIAL GENERATION:
            TASK: Create a step-by-step educational TUTORIAL showing how a real GitHub issue was solved through a PR.

            MANDATORY STRUCTURE:
            1. **Tutorial Overview**
               - Issue #{number}: {title}
               - Resolved by PR #{number}
               - Difficulty: {Easy/Intermediate/Hard}
               - What you'll learn (3-4 bullet points)
               - Files modified (list with brief descriptions)

            2. **Problem Context**
               - Describe the issue in 2-3 sentences
               - Why it needed to be fixed
               - Impact on the codebase

            3. **Step-by-Step Solution**
               CRITICAL: Break down the COMPLETE solution into sequential steps:
               - Easy difficulty: EXACTLY 5-6 steps
               - Intermediate difficulty: EXACTLY 7-8 steps
               - Hard difficulty: EXACTLY 9-10 steps

               IMPORTANT: Each step builds incrementally toward the complete solution.
               Do NOT provide the full solution in one step - distribute code changes across all required steps.

               For EACH step:
               **Step X: [Action-oriented title]**

               **What We're Doing:**
               Write 5-6 sentences explaining:
               - What specific changes are made in THIS step only
               - Which exact files are modified in this step
               - How this step contributes to solving the issue
               - Design decisions behind these particular changes
               - How it connects to previous steps and prepares for next steps

               **Code Implementation:**
               ```
               // File: actual/path/from/pr.ext
               [Show 10-20 lines of ACTUAL code from the PR for THIS STEP ONLY]
               [Must be real code from the context, not placeholders]
               [Include inline comments explaining what THIS code does]
               [Show only the portion relevant to THIS step's changes]
               ```

               STEP CODE REQUIREMENTS:
               - Each step must show 10-20 lines of actual code from the PR
               - Code must be specific to what THIS step accomplishes
               - Do NOT repeat the same code across multiple steps
               - Distribute different parts of the solution across steps
               - Show incremental progress step-by-step
               - For Easy (5-6 steps): each step covers one small change
               - For Intermediate (7-8 steps): each step covers one moderate change
               - For Hard (9-10 steps): each step covers one specific component/function

               **Key Concepts:**
               1. [Technical concept demonstrated in THIS step]
               2. [Best practice followed in THIS step's code]
               3. [Design pattern used in THIS step]
               4. [Why this approach was chosen for THIS change]
               5. [Performance/maintainability benefit of THIS step]

               **Common Pitfalls:**
               1. [Mistake beginners might make in THIS step]
               2. [Edge case to watch for in THIS step]
               3. [Testing consideration for THIS step]

            4. **Testing the Solution**
               - How to verify the complete fix works
               - Test cases to run for each major step
               - Expected outcomes after all steps are complete

            5. **Summary**
               - How the PR resolved the issue (3-4 sentences)
               - Key takeaways (3 technical lessons learned)
               - Skills practiced in this tutorial

            STRICT CONTENT RULES:
            - Use ONLY code from the actual PR in context
            - Every code block must be 10-20 lines from the real implementation
            - Reference exact file paths from the PR
            - NO placeholders, NO made-up code, NO TODOs
            - NO diagrams (Mermaid, flowcharts, UML)
            - Code must be from .dart/.ts/.py/.java files, NOT .md files
            - DO NOT show the complete solution in step 1 - break it down incrementally
            - Each step should show different code sections from the PR
            - If PR doesn't have enough code changes for required steps, state: "Insufficient code in PR for full tutorial"

            STEP BREAKDOWN EXAMPLES:

            For Easy PR (5-6 steps):
            - Step 1: Set up basic structure/imports
            - Step 2: Implement core logic part 1
            - Step 3: Implement core logic part 2
            - Step 4: Add error handling
            - Step 5: Update related components
            - Step 6: Add validation/tests

            For Intermediate PR (7-8 steps):
            - Step 1: Define interfaces/models
            - Step 2: Implement data layer
            - Step 3: Create service/business logic
            - Step 4: Build UI components
            - Step 5: Wire up state management
            - Step 6: Add error handling
            - Step 7: Implement validation
            - Step 8: Add tests

            For Hard PR (9-10 steps):
            - Step 1: Architecture setup
            - Step 2: Define core abstractions
            - Step 3: Implement data models
            - Step 4: Create repository layer
            - Step 5: Build business logic services
            - Step 6: Develop UI components
            - Step 7: Integrate state management
            - Step 8: Add middleware/interceptors
            - Step 9: Implement error handling
            - Step 10: Add comprehensive tests

            TUTORIAL TONE:
            - Explanatory and educational
            - "In this step, we're implementing X because Y"
            - "This code handles Z by doing..."
            - Build the solution incrementally across all steps
            - Guide the learner through each piece of the implementation
            - Show progression from setup to complete solution""",
            QueryType.PR_ISSUE_CODING_QUESTION: """
                PR-ISSUE CODING QUESTION GENERATION:
                TASK: Create an educational CODING QUESTION/CHALLENGE based on a RANDOMLY SELECTED real GitHub issue or PR, where the learner must implement the solution themselves.

                IMPORTANT - RANDOM PR SELECTION WITH DIFFICULTY FILTERING:
                - DO NOT always select the same PR/Issue
                - If user specifies difficulty (easy/intermediate/hard), FILTER BY THAT DIFFICULTY FIRST
                - RANDOMLY choose from PRs that meet the difficulty criteria
                - Each time this prompt is run, select a DIFFERENT PR
                - Vary your selection - don't pick PR #1 or the first one you see
                - Avoid recently used PRs - try to pick different ones each time
                - RESPECT THE DIFFICULTY CONSTRAINT - if user asks for "easy", ONLY return easy questions

                MANDATORY STRUCTURE:
                1. **Challenge Overview**
                   - Question based on randomly selected Issue/PR #{issue_number/pr_number}
                   - Difficulty: {Easy/Intermediate/Hard} - MUST MATCH USER'S REQUEST
                   - Estimated time: {15-30 min for Easy, 30-60 min for Intermediate, 60-90 min for Hard}
                   - Skills tested (3-4 bullet points)

                2. **Problem Description**
                   - Describe the issue/challenge in detail (3-4 sentences)
                   - What needs to be implemented/fixed
                   - Requirements and acceptance criteria
                   - Expected behavior after fix

                3. **Context & Setup**
                   - Relevant files in the codebase
                   - Existing code structure (show key parts without giving solution)
                   - Dependencies and imports needed
                   - Brief architecture context if needed

                4. **Your Task**
                   Number of sub-tasks based on difficulty:
                   - Easy: 2-3 sub-tasks (keep it simple)
                   - Intermediate: 4-5 sub-tasks
                   - Hard: 5-6 sub-tasks

                   For EACH sub-task:
                   **Task X: [Clear objective]**
                   - What needs to be implemented
                   - Which file(s) to modify
                   - Function/method signatures to implement
                   - Input/output specifications
                   - Edge cases to handle

                5. **Hints** (Progressive difficulty)
                   - Hint 1: High-level approach
                   - Hint 2: Specific technique or pattern to use
                   - Hint 3: Partial code snippet (5-10 lines) showing structure
                   - Hint 4: More detailed guidance for complex parts (omit for Easy)

                6. **Testing Requirements**
                   - Test cases to validate solution
                   - Expected outputs for given inputs
                   - Edge cases to verify
                   - How to run tests

                7. **Evaluation Criteria**
                   - Correctness (does it solve the issue?)
                   - Code quality (readability, maintainability)
                   - Edge case handling
                   - Performance considerations
                   - Best practices followed

                8. **Solution** (OPTIONAL - can be hidden/revealed)
                   **Complete Implementation:**
                   Show the actual solution from the PR with:
                   - All code changes (10-20 lines per file)
                   - Explanations of key decisions
                   - Why this approach was taken
                   - Alternative approaches considered

                   **Explanation:**
                   - Step-by-step breakdown of the solution
                   - Design patterns used
                   - Performance implications
                   - Testing strategy

                STRICT CONTENT RULES - IMPLEMENTATION CODE ONLY:
                - Base the problem on the ACTUAL issue/PR from context
                - ONLY use PRs that modify IMPLEMENTATION code files (.dart, .java, .py, .ts, .js, .cpp, .go, .rs, .kt, .swift)
                - The PR MUST contain actual business logic, algorithms, or feature implementation
                - Use real file structure and code patterns from the repository
                - Requirements must match what the actual PR solved
                - Solution (if included) must use REAL code from the PR (10-20 lines per section)

                EXCLUSION RULES - DO NOT CREATE QUESTIONS FROM:
                - PRs that ONLY modify .md, .txt, README files (documentation changes)
                - PRs that ONLY update .json, .yaml, .xml config files
                - PRs that ONLY modify package.json, pubspec.yaml, pubspec.lock, requirements.txt (dependency updates)
                - PRs that ONLY add/modify test files (test/, __tests__/, spec/ folders)
                - PRs that ONLY change CI/CD files (.github/workflows, Dockerfile, Makefile)
                - PRs that ONLY update assets (.png, .jpg, .svg, .css)
                - PRs that create templates or boilerplate without real implementation
                - PRs with only formatting changes, linting fixes, or comment updates

                VALID PR REQUIREMENTS:
                - Must modify at least ONE implementation code file (.dart, .java, .py, .ts, .js, etc.)
                - Must contain actual functions, classes, or business logic changes
                - Must solve a real technical problem (bug fix, new feature, refactoring)
                - Main changes should be in code, not documentation/configs

                If the provided PR/Issue does not meet these requirements, respond:
                "This PR/Issue primarily involves [documentation/configuration/dependencies/tests] changes and is not suitable for a coding challenge. Selecting a different PR..."

                DIFFICULTY CALIBRATION (STRICT FILTERING):
                - Easy: Well-defined problem, 1-3 code files modified, clear path to solution, single component
                - Intermediate: Multiple files (4-8 files), some design decisions needed, multiple related components
                - Hard: Complex changes (9+ code files), architectural considerations, system-wide impact

                RANDOMIZATION STRATEGY WITH DIFFICULTY FILTERING:
                1. **FIRST**: Check if user specified difficulty (easy/intermediate/hard/Easy/Intermediate/Hard)
                2. **SECOND**: Filter ALL merged PRs by:
                   a. Must have implementation code changes (not just docs/config)
                   b. Must match requested difficulty level (count modified code files)
                3. **THIRD**: From the filtered list, RANDOMLY select ONE PR
                4. **FOURTH**: Ensure you don't pick the same PR as last time
                5. **FIFTH**: Verify the selected PR matches the difficulty constraint

                DIFFICULTY MATCHING ALGORITHM:
                - Count ONLY implementation code files modified (exclude .md, .json, .yaml, test files, etc.)
                - Easy: 1-3 implementation files modified
                - Intermediate: 4-8 implementation files modified
                - Hard: 9+ implementation files modified
                - If user asks for "easy", filter out all PRs with 4+ files
                - If user asks for "intermediate", filter PRs with 4-8 files only
                - If user asks for "hard", filter PRs with 9+ files only

                QUESTION TONE:
                - Clear and challenging
                - "You need to implement..."
                - "Your task is to..."
                - "Ensure that your solution..."
                - Don't give away the solution in the problem description
                - Provide enough context to solve without seeing the PR
                - NO diagrams unless specifically requested
                - NO placeholders in the problem description

                FINAL VALIDATION:
                Before generating the question, verify:
                1. Does this PR modify actual implementation code? (YES required)
                2. Does it contain functions/classes/business logic? (YES required)
                3. Is the main purpose code implementation, not docs/config/tests? (YES required)
                4. Can a learner write meaningful code to solve this? (YES required)
                5. Is this a DIFFERENT PR than the last one selected? (YES required)
                6. **DOES THIS PR MATCH THE REQUESTED DIFFICULTY?** (YES required)
                   - Count implementation files modified
                   - Verify it falls within the difficulty range
                   - If user said "easy", ensure ≤3 files modified
                7. Is the "Difficulty" field in the output set to the CORRECT difficulty matching the user's request? (YES required)

                If any answer is NO, select a different PR and try again.

                CRITICAL: If user specifies difficulty, the generated question MUST match that difficulty. Do not return intermediate when user asks for easy, or easy when user asks for hard.

                Remember: The goal is to provide VARIETY while RESPECTING DIFFICULTY CONSTRAINTS - each question should be based on a DIFFERENT randomly selected PR with real code changes that MATCHES the requested difficulty level.""",
            QueryType.IMPACT_ANALYSIS: """
        IMPACT & DEPENDENCY ANALYSIS QUERY:
        
        TASK: Analyze dependencies, call graphs, and historical impact using the Knowledge Graph.

        MANDATORY SECTIONS:
        1. **Dependency Diagram**: Create a mermaid flowchart showing:
           - The entity in question (File/Function)
           - Callers/Callees (Code Structure)
           - **Related PRs/Issues** (Historical Context)

        2. **Impact Assessment**:
           - **Code Impact**: List files/functions that break if this changes.
           - **Process Impact**: List open PRs or Issues that might be affected (check 'related_to' edges).
           - **Expertise**: List users who have modified this code recently (check 'modified_by' edges).

        3. **Code Context**:
           - Show actual code snippets for dependencies.

        STRICT RULES:
        - Use "Graph Context" for both code dependencies (CALLS) and metadata (MODIFIES, CLOSES).
        - Highlight if a file is "Hot" (modified by many PRs).
        """,
            QueryType.GENERAL: """
        GENERAL QUERY:
        - Direct answer from context
        - Supporting documentation
        - Code examples where relevant
        - Clear, concise response""",
            QueryType.TRACEABILITY: """
        TRACEABILITY QUERY (History & Authorship):
        
        TASK: Trace the history of code changes, identify authors, and link code to Pull Requests.

        MANDATORY:
        1. **Timeline**: Show a chronological list of changes based on PRs and Commits in context.
        2. **Attribution**: Identify the "User" or "Author" nodes from the graph context.
        3. **Linkage**: Connect specific files to the PRs that modified them (MODIFIES edge).

        STRICT RULES:
        - Use "Graph Context" to find 'CREATED_BY' and 'MODIFIES' edges.
        - If the graph shows User X created PR Y which modified File Z, state: "User X modified File Z in PR Y".
        - Do not guess authors; use only the explicit graph data.
        """,
        }

        specific_prompt = prompts.get(query_type, prompts[QueryType.GENERAL])

        needs_diagram = any(
            kw in query.lower()
            for kw in [
                "architecture",
                "flow",
                "diagram",
                "structure of",
                "how does",
                "service",
                "call graph",
                "dependencies",
                "impact",
            ]
        )

        if needs_diagram and query_type not in [
            QueryType.CODE_STRUCTURE,
            QueryType.QUESTION_GENERATION,
            QueryType.FILE_LOOKUP,
        ]:
            specific_prompt += "\n\nIMPORTANT: This query requires a mermaid flowchart diagram. Include it first in your response."

            if query_type == QueryType.IMPACT_ANALYSIS:
                specific_prompt += ""

        return f"{base_rules}\n\n{specific_prompt}"

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=4000,
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return response.content[0].text

            elif self.provider == "ollama":
                import requests

                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": self.temperature},
                    },
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()["message"]["content"]

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(f"{error_msg}")
            import traceback

            traceback.print_exc()
            return f"Error: {error_msg}\n\nPlease check your API configuration."

    def call_llm_stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=4000,
                    stream=True,
                )

                for chunk in response:
                    # openai streaming chunk structure may vary; guard access
                    try:
                        delta = getattr(chunk.choices[0], "delta", None)
                        if delta and getattr(delta, "content", None):
                            yield delta.content
                        elif "choices" in chunk and chunk["choices"][0].get(
                            "delta", {}
                        ).get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except Exception:
                        # fallback: try to extract content
                        if hasattr(chunk, "choices") and chunk.choices:
                            choice = chunk.choices[0]
                            content = getattr(choice, "text", None) or getattr(
                                choice, "message", {}
                            ).get("content", None)
                            if content:
                                yield content

            elif self.provider == "anthropic":
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=4000,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            elif self.provider == "ollama":
                import requests

                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": True,
                        "options": {"temperature": self.temperature},
                    },
                    timeout=120,
                    stream=True,
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(f"{error_msg}")
            import traceback

            traceback.print_exc()
            yield f"Error: {error_msg}\n\nPlease check your API configuration."

    def verify_and_refine_response(
        self, answer: str, query: str, query_type: str
    ) -> str:
        verification_prompt = f"""Review the following response and identify any unnecessary or irrelevant content that should be removed.

        QUERY: {query}
        QUERY TYPE: {query_type}

        RESPONSE TO VERIFY:
        {answer}

        VERIFICATION RULES:
        1. Remove any content that lists unrelated issues/PRs not directly answering the query
        2. Remove generic statements that don't add value
        3. Remove repeated information
        4. Keep only relevant, specific information that directly answers the question
        5. If response seems to include random examples, remove them
        6. Keep technical content, code, diagrams, and direct answers

        Provide the refined response with unnecessary content removed. If response is already good, return it as-is.
        Return ONLY the refined response, no explanations."""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a response quality verifier. Remove only unnecessary content, keep all relevant information.",
                        },
                        {"role": "user", "content": verification_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=4000,
                )
                refined = response.choices[0].message.content

                if len(refined) < len(answer) * 0.3:
                    self.logger.warning(
                        f"VERIFICATION | Refined response too short ({len(refined)} vs {len(answer)}), keeping original"
                    )
                    return answer

                self.logger.info(
                    f"VERIFICATION | Response refined: {len(answer)} -> {len(refined)} chars"
                )
                return refined

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.3,
                    system="You are a response quality verifier. Remove only unnecessary content, keep all relevant information.",
                    messages=[{"role": "user", "content": verification_prompt}],
                )
                refined = response.content[0].text

                if len(refined) < len(answer) * 0.3:
                    self.logger.warning(
                        f"VERIFICATION | Refined response too short, keeping original"
                    )
                    return answer

                self.logger.info(
                    f"VERIFICATION | Response refined: {len(answer)} -> {len(refined)} chars"
                )
                return refined

            else:
                self.logger.info("VERIFICATION | Skipped (provider not supported)")
                return answer

        except Exception as e:
            self.logger.error(f"VERIFICATION | Error during verification: {e}")
            return answer

    def build_user_prompt(
        self,
        query: str,
        context: str,
        email_context: str,
        query_type: str,
        entity: Optional[Dict[str, Any]] = None,
        metrics_context: Optional[str] = None,
    ) -> str:
        prompt_parts: List[str] = []

        if metrics_context and query_type in [
            QueryType.REPOSITORY_METRICS,
            QueryType.TECH_STACK,
            QueryType.CODE_STRUCTURE,
        ]:
            prompt_parts.append(metrics_context)
            prompt_parts.append("\n" + "=" * 70 + "\n")

        if context:
            prompt_parts.append("# CODEBASE CONTEXT\n")
            prompt_parts.append(context)

        if email_context:
            prompt_parts.extend(["\n\n# EMAIL DISCUSSIONS\n", email_context])

        if entity:
            prompt_parts.append(f"\n\n# QUERY TARGET\n")
            prompt_parts.append(f"Entity Type: {entity.get('type')}")
            if entity.get("number"):
                prompt_parts.append(f"Entity Number: {entity.get('number')}")
            if entity.get("sha"):
                prompt_parts.append(f"Commit SHA: {entity.get('sha')}")

        prompt_parts.extend(["\n\n# USER QUESTION\n", query])

        prompt_parts.append("\n\n# RESPONSE INSTRUCTIONS\n")
        prompt_parts.append("Please answer the question in a friendly, natural, and conversational tone.")
        prompt_parts.append("Answer using ONLY information from the context above - be accurate and factual.")
        prompt_parts.append("Write as if you're explaining to a colleague or teammate - be warm and engaging.")
        prompt_parts.append("Use complete sentences and natural language flow.")
        prompt_parts.append("Ensure proper grammar, clarity, and readability.")
        prompt_parts.append("Use markdown formatting for better readability (headings, code blocks, lists, etc.).")
        prompt_parts.append("Make your response helpful, clear, and easy to understand.")

        # Query-type specific instructions
        if query_type == QueryType.QUESTION_GENERATION:
            prompt_parts.append(
                "Generate educational questions with answers based on the context."
            )
            prompt_parts.append("Do NOT include mermaid diagrams in questions.")
            prompt_parts.append(
                "Use code blocks only where questions require showing code."
            )
        elif query_type in [QueryType.HOW_TO, QueryType.CONCEPTUAL]:
            # For documentation queries, allow documentation text, not just code
            prompt_parts.append(
                "Include documentation, instructions, and code examples from context when relevant."
            )
            prompt_parts.append("\n# STRICT RULES - MANDATORY:")
            prompt_parts.append(
                "1. Use information from documentation/context, even if it's not code"
            )
            prompt_parts.append(
                "2. If context contains installation/setup instructions, provide them step-by-step"
            )
            prompt_parts.append("3. If context contains code examples, include them")
            prompt_parts.append(
                "4. NEVER use: 'is likely', 'probably', 'might be', 'appears to', 'seems to'"
            )
            prompt_parts.append(
                "5. If no relevant information exists in context, write: 'No information found in context for [topic]'"
            )
            prompt_parts.append(
                "6. Provide clear, actionable steps based on the context provided"
            )
        elif query_type == QueryType.FILE_LOOKUP:
            prompt_parts.append(
                "You are explaining a SINGLE source code file."
            )
            prompt_parts.append("\n# STRICT GROUNDING RULES - MANDATORY:")
            prompt_parts.append(
                "1. Mention ONLY classes, enums, methods, fields, and functions that appear in the file."
            )
            prompt_parts.append(
                "2. Do NOT infer intent, UI behavior, or usage beyond what the code explicitly shows."
            )
            prompt_parts.append(
                "3. If something is referenced but not implemented in this file, write: "
                "'Not implemented in this file.'"
            )
            prompt_parts.append(
                "4. Prefer STRUCTURAL explanation over narrative (what exists, not why)."
            )
            prompt_parts.append(
                "5. Include SHORT, relevant code excerpts only when they help understanding."
            )
            prompt_parts.append(
                "6. Do NOT enforce any minimum line count."
            )
        elif query_type == QueryType.FLOW_ARCHITECTURE:
            # For code queries, require actual code
            prompt_parts.append(
                "Include extensive code examples from context when relevant."
            )
            prompt_parts.append("\n# STRICT RULES - MANDATORY:")
            prompt_parts.append(
                "1. Every component/class/function mentioned MUST have actual code shown"
            )
            prompt_parts.append(
                "2. NEVER use: 'is likely', 'probably', 'might be', 'appears to', 'seems to'"
            )
            prompt_parts.append(
                "3. If no code exists for something, write: 'No implementation found in context for [Name]'"
            )
            prompt_parts.append(
                "4. Do NOT describe what a component 'might do' or 'is likely involved in'"
            )
            prompt_parts.append(
                "5. ONLY describe functionality that has actual code in the context above"
            )
            prompt_parts.append(
                "6. Minimum 20 lines of actual code per component explanation"
            )
        elif query_type == QueryType.IMPACT_ANALYSIS:
            prompt_parts.append("\n# STRICT IMPACT ANALYSIS RULES:")
            prompt_parts.append(
                "1. Use the 'Graph Context' to identify callers, callees, and related PRs."
            )
            prompt_parts.append("2. Trace dependencies explicitly.")
            prompt_parts.append(
                "3. If a function is listed as 'Called By' X, then X depends on it."
            )
            prompt_parts.append(
                "4. If a file was modified by PR Y, mention that history."
            )
            prompt_parts.append("5. Generate a dependency diagram (Mermaid) first.")
        elif query_type == QueryType.TRACEABILITY:
            prompt_parts.append("\n# STRICT TRACEABILITY RULES:")
            prompt_parts.append(
                "1. Focus on the 'Who' (User) and 'How' (PR/Commit) aspects."
            )
            prompt_parts.append("2. Use graph edges: CREATED_BY, MODIFIES, CLOSES.")
            prompt_parts.append("3. Present a clear timeline of changes.")
        else:
            # For other queries, be flexible
            prompt_parts.append(
                "Include code examples, documentation, or relevant information from context when available."
            )
            prompt_parts.append("\n# STRICT RULES - MANDATORY:")
            prompt_parts.append(
                "1. Use information from context (code, documentation, or other content)"
            )
            prompt_parts.append(
                "2. NEVER use: 'is likely', 'probably', 'might be', 'appears to', 'seems to'"
            )
            prompt_parts.append(
                "3. If no relevant information exists in context, write: 'No information found in context for [topic]'"
            )
            prompt_parts.append(
                "4. Provide accurate information based only on what's in the context"
            )

        needs_diagram = any(
            kw in query.lower()
            for kw in [
                "architecture",
                "flow",
                "diagram",
                "how does",
                "service",
                "impact",
                "dependency",
            ]
        ) and query_type not in [
            QueryType.CODE_STRUCTURE,
            QueryType.QUESTION_GENERATION,
        ]

        if needs_diagram:
            prompt_parts.append(
                "\nMANDATORY: Include a mermaid flowchart diagram in your response."
            )
            prompt_parts.append(
                "After diagram, show ACTUAL CODE for each component from context above."
            )
            prompt_parts.append(
                "If no code exists for a component, state: 'Code not found in context'"
            )

        return "\n".join(prompt_parts)
    
    