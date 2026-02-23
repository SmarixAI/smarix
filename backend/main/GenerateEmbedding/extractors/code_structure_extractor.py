import re
from typing import Dict, Any, Optional

# ─────────────────────────────────────────────
# PATTERNS: language → function / class / docstring
# ─────────────────────────────────────────────
PATTERNS = {

    # ── Python ────────────────────────────────
    "python": {
        "function": re.compile(r"^\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"^\s*class\s+([a-zA-Z_]\w*)\s*[:\(]", re.MULTILINE),
        "docstring": re.compile(r'^\s*[\'\"]{3}', re.MULTILINE),
    },

    # ── JavaScript / TypeScript ───────────────
    "javascript": {
        "function": re.compile(
            r"(?:function\s+([a-zA-Z_]\w*)\s*\("
            r"|(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s+)?(?:function|\()"
            r"|([a-zA-Z_]\w*)\s*:\s*(?:async\s+)?function"
            r"|(?:async\s+)?([a-zA-Z_]\w*)\s*\([^)]*\)\s*(?::\s*\w+)?\s*=>)",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },
    "typescript": {
        "function": re.compile(
            r"(?:function\s+([a-zA-Z_]\w*)\s*\(?:"
            r"|(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s+)?(?:function|\()"
            r"|([a-zA-Z_]\w*)\s*:\s*(?:async\s+)?function"
            r"|(?:export\s+)?(?:async\s+)?(?:function\s+)?([a-zA-Z_]\w*)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|]+)?\s*\{)",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },

    # ── Java / Kotlin ─────────────────────────
    "java": {
        "function": re.compile(
            r"(?:public|private|protected|static|final|synchronized|\s)+"
            r"[\w\<\>\[\]]+\s+([a-zA-Z_]\w*)\s*\(",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },
    "kotlin": {
        "function": re.compile(r"^\s*(?:suspend\s+)?fun\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"^\s*(?:data\s+|sealed\s+|abstract\s+|open\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },

    # ── C / C++ ───────────────────────────────
    "c": {
        "function": re.compile(
            r"^[\w\*\s]+\s+([a-zA-Z_]\w*)\s*\([^;]*\)\s*\{",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:struct|union)\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*|///", re.MULTILINE),
    },
    "cpp": {
        "function": re.compile(
            r"^[\w\*\s\:\<\>]+\s+([a-zA-Z_]\w*)\s*\([^;]*\)\s*(?:const\s*)?\{",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:class|struct)\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*|///", re.MULTILINE),
    },

    # ── C# ────────────────────────────────────
    "csharp": {
        "function": re.compile(
            r"(?:public|private|protected|internal|static|virtual|override|async|\s)+"
            r"[\w\<\>\[\]]+\s+([a-zA-Z_]\w*)\s*\(",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:public\s+)?(?:abstract\s+)?(?:partial\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"///", re.MULTILINE),
    },

    # ── Go ────────────────────────────────────
    "go": {
        "function": re.compile(r"^func\s+(?:\([^)]+\)\s+)?([a-zA-Z_]\w*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"^type\s+([a-zA-Z_]\w*)\s+struct", re.MULTILINE),
        "docstring": re.compile(r"^//\s*[A-Z]", re.MULTILINE),  # Go convention
    },

    # ── Rust ──────────────────────────────────
    "rust": {
        "function": re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([a-zA-Z_]\w*)\s*[\(<]", re.MULTILINE),
        "class":    re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait|impl)\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"///|/\*\*", re.MULTILINE),
    },

    # ── Ruby ──────────────────────────────────
    "ruby": {
        "function": re.compile(r"^\s*def\s+(?:self\.)?([a-zA-Z_]\w*)", re.MULTILINE),
        "class":    re.compile(r"^\s*class\s+([A-Z][a-zA-Z_]*)", re.MULTILINE),
        "docstring": re.compile(r"^\s*#", re.MULTILINE),
    },

    # ── PHP ───────────────────────────────────
    "php": {
        "function": re.compile(r"^\s*(?:public|private|protected|static|\s)*function\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"^\s*(?:abstract\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },

    # ── Swift ─────────────────────────────────
    "swift": {
        "function": re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|open\s+)?(?:mutating\s+)?func\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"^\s*(?:public\s+)?(?:final\s+)?(?:class|struct|enum|protocol|actor)\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"///|/\*\*", re.MULTILINE),
    },

    # ── Scala ─────────────────────────────────
    "scala": {
        "function": re.compile(r"^\s*(?:def)\s+([a-zA-Z_]\w*)\s*[\(\[]", re.MULTILINE),
        "class":    re.compile(r"^\s*(?:case\s+)?(?:class|object|trait)\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"/\*\*", re.MULTILINE),
    },

    # ── Shell / Bash ──────────────────────────
    "bash": {
        "function": re.compile(r"^(?:function\s+)?([a-zA-Z_]\w*)\s*\(\s*\)\s*\{", re.MULTILINE),
        "class":    re.compile(r"(?!)", re.MULTILINE),  # No classes in bash
        "docstring": re.compile(r"^#", re.MULTILINE),
    },
    "sh": {
        "function": re.compile(r"^(?:function\s+)?([a-zA-Z_]\w*)\s*\(\s*\)\s*\{", re.MULTILINE),
        "class":    re.compile(r"(?!)", re.MULTILINE),
        "docstring": re.compile(r"^#", re.MULTILINE),
    },

    # ── Dart / Flutter ────────────────────────
    "dart": {
        "function": re.compile(
            r"(?:(?:Future|void|String|int|bool|double|List|Map|dynamic|\w+)\s+)"
            r"([a-zA-Z_]\w*)\s*\([^;]*\)\s*(?:async\s*)?\{",
            re.MULTILINE
        ),
        "class":    re.compile(r"^\s*(?:abstract\s+)?class\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"///|/\*\*", re.MULTILINE),
    },

    # ── R ─────────────────────────────────────
    "r": {
        "function": re.compile(r"([a-zA-Z_]\w*)\s*<-\s*function\s*\(", re.MULTILINE),
        "class":    re.compile(r"setClass\s*\(\s*['\"]([a-zA-Z_]\w*)", re.MULTILINE),
        "docstring": re.compile(r"^#'", re.MULTILINE),
    },

    # ── Lua ───────────────────────────────────
    "lua": {
        "function": re.compile(r"^(?:local\s+)?function\s+([a-zA-Z_][\w\.]*)\s*\(", re.MULTILINE),
        "class":    re.compile(r"([a-zA-Z_]\w*)\s*=\s*\{\}", re.MULTILINE),
        "docstring": re.compile(r"^---", re.MULTILINE),
    },

    # ── Elixir ────────────────────────────────
    "elixir": {
        "function": re.compile(r"^\s*(?:def|defp)\s+([a-zA-Z_]\w*)\s*[\(\n]", re.MULTILINE),
        "class":    re.compile(r"^\s*defmodule\s+([\w\.]+)", re.MULTILINE),
        "docstring": re.compile(r'@(?:doc|moduledoc)\s+"""', re.MULTILINE),
    },

    # ── Haskell ───────────────────────────────
    "haskell": {
        "function": re.compile(r"^([a-z][a-zA-Z0-9_']*)\s+::", re.MULTILINE),
        "class":    re.compile(r"^(?:data|newtype|class)\s+([A-Z]\w*)", re.MULTILINE),
        "docstring": re.compile(r"^-- \|", re.MULTILINE),
    },

    # ── Perl ──────────────────────────────────
    "perl": {
        "function": re.compile(r"^\s*sub\s+([a-zA-Z_]\w*)", re.MULTILINE),
        "class":    re.compile(r"package\s+([\w:]+)", re.MULTILINE),
        "docstring": re.compile(r"^=(?:head|pod)", re.MULTILINE),
    },

    # ── YAML / JSON / TOML / Config ───────────
    "yaml": {
        "function": re.compile(r"(?!)", re.MULTILINE),
        "class":    re.compile(r"(?!)", re.MULTILINE),
        "docstring": re.compile(r"^#", re.MULTILINE),
    },
    "json": {
        "function": re.compile(r"(?!)", re.MULTILINE),
        "class":    re.compile(r"(?!)", re.MULTILINE),
        "docstring": re.compile(r"(?!)", re.MULTILINE),
    },
    "toml": {
        "function": re.compile(r"(?!)", re.MULTILINE),
        "class":    re.compile(r"^\[([a-zA-Z_][\w\.]*)\]", re.MULTILINE),
        "docstring": re.compile(r"^#", re.MULTILINE),
    },

    # ── SQL ───────────────────────────────────
    "sql": {
        "function": re.compile(
            r"(?:CREATE|ALTER)\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+([a-zA-Z_]\w*)",
            re.MULTILINE | re.IGNORECASE
        ),
        "class":    re.compile(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_]\w*)",
            re.MULTILINE | re.IGNORECASE
        ),
        "docstring": re.compile(r"^--", re.MULTILINE),
    },

    # ── Terraform / HCL ───────────────────────
    "hcl": {
        "function": re.compile(r"(?!)", re.MULTILINE),
        "class":    re.compile(r'^resource\s+"[\w_]+"\s+"([^"]+)"', re.MULTILINE),
        "docstring": re.compile(r"^#", re.MULTILINE),
    },
    "tf": {
        "function": re.compile(r"(?!)", re.MULTILINE),
        "class":    re.compile(r'^resource\s+"[\w_]+"\s+"([^"]+)"', re.MULTILINE),
        "docstring": re.compile(r"^#", re.MULTILINE),
    },
}

# ─────────────────────────────────────────────
# ALIASES — map extensions to pattern keys
# ─────────────────────────────────────────────
ALIASES = {
    "py":   "python",
    "js":   "javascript",
    "jsx":  "javascript",
    "ts":   "typescript",
    "tsx":  "typescript",
    "mjs":  "javascript",
    "cjs":  "javascript",
    "cs":   "csharp",
    "cc":   "cpp",
    "cxx":  "cpp",
    "hpp":  "cpp",
    "h":    "c",
    "rb":   "ruby",
    "kt":   "kotlin",
    "kts":  "kotlin",
    "rs":   "rust",
    "ex":   "elixir",
    "exs":  "elixir",
    "hs":   "haskell",
    "pl":   "perl",
    "pm":   "perl",
    "yml":  "yaml",
    "sh":   "bash",
    "zsh":  "bash",
    "fish": "bash",
}


def extract_code_structure(content: str, language: Optional[str]) -> Dict[str, Any]:
    """
    Given a code chunk's text and language/extension,
    extracts: code_chunk_type, function_name, class_name, has_docstring.
    """
    result = {
        "code_chunk_type": "other",
        "function_name":   None,
        "class_name":      None,
        "has_docstring":   False,
    }

    if not content or not language:
        return result

    lang = language.lower().strip()
    lang = ALIASES.get(lang, lang)           # normalize extension → language key
    patterns = PATTERNS.get(lang)

    if not patterns:
        # Unknown language — generic docstring check only
        result["has_docstring"] = bool(re.search(r'("""|\'\'\'|/\*\*|///)', content))
        return result

    # ── Docstring ─────────────────────────────
    result["has_docstring"] = bool(patterns["docstring"].search(content))

    # ── Class / Struct / Module ───────────────
    class_match = patterns["class"].search(content)
    if class_match:
        result["code_chunk_type"] = "class"
        result["class_name"] = next((g for g in class_match.groups() if g), None)

    # ── Function / Method ─────────────────────
    func_match = patterns["function"].search(content)
    if func_match:
        func_name = next((g for g in func_match.groups() if g), None)
        if func_name:
            result["function_name"] = func_name
            if result["code_chunk_type"] != "class":
                result["code_chunk_type"] = "function"
            # if class also matched → method inside class,
            # keep code_chunk_type = "class" but preserve function_name

    # ── Module-level fallback ─────────────────
    if result["code_chunk_type"] == "other" and content.strip():
        result["code_chunk_type"] = "module"

    return result
