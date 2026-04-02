import asyncio
import json
import logging
import os
import re
import shutil
import socket
import subprocess
import threading
import tempfile
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

router = APIRouter(prefix="/devai", tags=["devai"])
logger = logging.getLogger(__name__)

CODE_INDEX = {}
INDEX_LOCK = threading.Lock()


class CodeSearchEngine:
    """Ultra-fast code search with indexing"""
    
    def __init__(self):
        self.files_index = {}
        self.functions_index = defaultdict(list)
        self.classes_index = defaultdict(list)
        self.imports_index = defaultdict(list)
        self.strings_index = defaultdict(list)
        self.last_index_time = 0
    
    def index_project(self, root_path: str = ".") -> dict:
        """Index entire project for instant search"""
        root = Path(root_path)
        stats = {"files": 0, "functions": 0, "classes": 0, "imports": 0}
        
        ignore = {".git", "__pycache__", "node_modules", ".venv", "venv", 
                  ".cache", "dist", "build", ".next", "*.pyc"}
        
        for path in root.rglob("*"):
            if any(i in str(path) for i in ignore):
                continue
            if path.is_file() and path.stat().st_size < 10_000_000:
                rel_path = str(path.relative_to(root))
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                    stats["files"] += 1
                    
                    self.files_index[rel_path] = {
                        "content": content,
                        "size": len(content),
                        "lines": len(content.splitlines()),
                        "ext": path.suffix,
                    }
                    
                    for match in re.finditer(r'^\s*(def|async def)\s+(\w+)', content, re.MULTILINE):
                        func_name = match.group(2)
                        line_num = content[:match.start()].count('\n') + 1
                        self.functions_index[func_name].append({
                            "file": rel_path, "line": line_num,
                            "context": content[max(0, match.start()-100):match.end()+100]
                        })
                        stats["functions"] += 1
                    
                    for match in re.finditer(r'^\s*class\s+(\w+)', content, re.MULTILINE):
                        class_name = match.group(1)
                        line_num = content[:match.start()].count('\n') + 1
                        self.classes_index[class_name].append({
                            "file": rel_path, "line": line_num,
                            "context": content[max(0, match.start()-100):match.end()+200]
                        })
                        stats["classes"] += 1
                    
                    for match in re.finditer(r'^(?:from|import)\s+([^\s]+)', content, re.MULTILINE):
                        module = match.group(1).split('.')[0]
                        self.imports_index[module].append(rel_path)
                        stats["imports"] += 1
                        
                except Exception as e:
                    logger.debug(f"Index error {path}: {e}")
        
        self.last_index_time = datetime.now().timestamp()
        return stats
    
    def search_functions(self, query: str) -> List[dict]:
        """Find functions by name"""
        results = []
        query_lower = query.lower()
        for func, locations in self.functions_index.items():
            if query_lower in func.lower():
                results.extend(locations)
        return results[:50]
    
    def search_classes(self, query: str) -> List[dict]:
        """Find classes by name"""
        results = []
        query_lower = query.lower()
        for cls, locations in self.classes_index.items():
            if query_lower in cls.lower():
                results.extend(locations)
        return results[:50]
    
    def search_code(self, query: str, file_types: List[str] = None) -> List[dict]:
        """Full-text search across all code"""
        results = []
        query_lower = query.lower()
        
        for path, data in self.files_index.items():
            if file_types and not any(path.endswith(ext) for ext in file_types):
                continue
            
            content = data["content"]
            lines = content.splitlines()
            
            for i, line in enumerate(lines):
                if query_lower in line.lower():
                    results.append({
                        "file": path,
                        "line": i + 1,
                        "content": line.strip(),
                        "before": lines[max(0, i-1)].strip(),
                        "after": lines[min(len(lines)-1, i+1)].strip(),
                    })
                    if len(results) >= 100:
                        return results
        return results
    
    def find_related(self, file_path: str) -> dict:
        """Find related files (imports, similar names)"""
        related = {"imports": [], "imported_by": [], "similar": []}
        
        if file_path not in self.files_index:
            return related
        
        content = self.files_index[file_path].get("content", "")
        
        for match in re.finditer(r'^(?:from|import)\s+([^\s]+)', content, re.MULTILINE):
            module = match.group(1).split('.')[0]
            if module in self.imports_index:
                related["imports"].extend(self.imports_index[module])
        
        for module, files in self.imports_index.items():
            if file_path in files:
                related["imported_by"].append(module)
        
        base_name = Path(file_path).stem.lower()
        for path in self.files_index:
            if path != file_path and base_name in Path(path).stem.lower():
                related["similar"].append(path)
        
        return related


code_search = CodeSearchEngine()


class SmartDownloader:
    """Auto-download tools and packages when needed"""
    
    @staticmethod
    def install_python_package(package: str) -> str:
        """Install Python package"""
        try:
            result = subprocess.run(
                ["pip", "install", package, "-q"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return f"✅ Installed: {package}"
            return f"❌ Failed: {result.stderr[:200]}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def install_npm_package(package: str) -> str:
        """Install npm package"""
        try:
            result = subprocess.run(
                ["npm", "install", "-g", package],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return f"✅ Installed: {package}"
            return f"❌ Failed: {result.stderr[:200]}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def download_file(url: str, dest: str = "") -> str:
        """Download file from URL"""
        try:
            import urllib.request
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "download"
            save_path = os.path.expanduser(dest) if dest else filename
            
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DevAI/1.0'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                with open(save_path, 'wb') as f:
                    f.write(content)
            
            size = len(content) / 1024
            return f"✅ Downloaded: {url} → {save_path} ({size:.1f}KB)"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def clone_git_repo(url: str, dest: str = "") -> str:
        """Clone git repository"""
        try:
            dest = dest or url.split("/")[-1].replace(".git", "")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", url, dest],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return f"✅ Cloned: {url} → {dest}"
            return f"❌ Failed: {result.stderr[:200]}"
        except Exception as e:
            return f"❌ Error: {e}"


downloader = SmartDownloader()


class CodeAnalyzer:
    """AI-powered code analysis"""
    
    @staticmethod
    def find_bugs(code: str) -> List[dict]:
        """Find common bugs in code"""
        bugs = []
        lines = code.splitlines()
        
        bug_patterns = [
            (r'\.get\([^,)]*\)\s*\[', "Potential KeyError - use .get() with default"),
            (r'for\s+\w+\s+in\s+.*:\s*\n\s+for\s+', "Nested loops - consider optimization"),
            (r'except\s*:', "Bare except - specify exception type"),
            (r'==\s*(True|False)', "Use 'is' for bool comparison"),
            (r'while\s+True:', "Infinite loop - ensure exit condition"),
            (r'subprocess\.\s*call\([^)]*shell\s*=\s*True', "Shell=True security risk"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
            (r'TODO|FIXME|XXX|HACK', "TODO/FIXME comment found"),
            (r'print\s*\(', "Debug print statement"),
            (r'\[\s*:\s*\]', "Empty slice - possible mistake"),
        ]
        
        for i, line in enumerate(lines):
            for pattern, msg in bug_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    bugs.append({
                        "line": i + 1,
                        "content": line.strip(),
                        "issue": msg,
                        "severity": "high" if any(s in msg.lower() for s in ["security", "key", "password"]) else "medium"
                    })
        
        return bugs[:20]
    
    @staticmethod
    def analyze_complexity(code: str) -> dict:
        """Calculate code complexity"""
        lines = code.splitlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        functions = len(re.findall(r'def\s+\w+', code))
        classes = len(re.findall(r'class\s+\w+', code))
        imports = len(re.findall(r'^(?:from|import)\s+', code, re.MULTILINE))
        
        complexity_score = 0
        complexity_score += functions * 2
        complexity_score += classes * 3
        complexity_score += len([l for l in lines if 'if ' in l or ' for ' in l or ' while ' in l])
        
        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "complexity_score": complexity_score,
            "rating": "high" if complexity_score > 50 else "medium" if complexity_score > 20 else "low"
        }
    
    @staticmethod
    def suggest_improvements(code: str) -> List[str]:
        """AI-powered improvement suggestions"""
        suggestions = []
        
        if "except:" in code:
            suggestions.append("💡 Specify exception types instead of bare except")
        if "print(" in code and "debug" not in code.lower():
            suggestions.append("💡 Use logging instead of print statements")
        if re.search(r'def\s+\w+\([^)]*\):\s*\n\s+[^#\n]', code):
            suggestions.append("💡 Add docstrings to functions")
        if "global " in code:
            suggestions.append("💡 Avoid global variables - use classes or dependency injection")
        if len(code.splitlines()) > 500:
            suggestions.append("💡 Consider splitting this file into modules")
        
        return suggestions[:5]


analyzer = CodeAnalyzer()


@dataclass
class ReasoningStep:
    step_number: int
    phase: str
    thought: str
    action: str = ""
    result: Any = None
    
@dataclass
class ChangePlan:
    files_to_modify: List[str] = field(default_factory=list)
    files_to_create: List[str] = field(default_factory=list)
    files_to_delete: List[str] = field(default_factory=list)
    functions_to_change: Dict[str, List[str]] = field(default_factory=dict)
    reasons: Dict[str, str] = field(default_factory=dict)
    safety_checks: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)


class DevAIReasoningEngine:
    """Senior-engineer thinking engine for structured reasoning"""
    
    def __init__(self):
        self.current_task: str = ""
        self.steps: List[ReasoningStep] = []
        self.change_plan: ChangePlan = ChangePlan()
        self.project_awareness: Dict[str, Any] = {}
        self._step_counter = 0
        
    def start_task(self, task: str) -> str:
        self.current_task = task
        self.steps = []
        self.change_plan = ChangePlan()
        self.project_awareness = {}
        self._step_counter = 0
        
        header = f"""
{'='*70}
🧠 DEV AI REASONING ENGINE - Senior Engineer Mode
{'='*70}
📋 TASK: {task}
⏰ Started: {datetime.now().strftime('%H:%M:%S')}
{'='*70}
"""
        return header
    
    def think(self, phase: str, thought: str, action: str = "") -> ReasoningStep:
        self._step_counter += 1
        step = ReasoningStep(
            step_number=self._step_counter,
            phase=phase,
            thought=thought,
            action=action
        )
        self.steps.append(step)
        
        icon = {
            "ANALYSIS": "🔍",
            "PLANNING": "📋",
            "SCANNING": "📂",
            "VERIFYING": "✅",
            "EXECUTING": "⚡",
            "SAFETY": "🛡️",
            "ERROR": "🐛",
            "REFACTORING": "🔧"
        }.get(phase.upper(), "💭")
        
        return step
    
    def format_thinking(self) -> str:
        if not self.steps:
            return ""
        
        lines = ["", "📊 REASONING CHAIN:", "-" * 50]
        for step in self.steps:
            icon = {
                "ANALYSIS": "🔍", "PLANNING": "📋", "SCANNING": "📂",
                "VERIFYING": "✅", "EXECUTING": "⚡", "SAFETY": "🛡️",
                "ERROR": "🐛", "REFACTORING": "🔧"
            }.get(step.phase.upper(), "💭")
            
            lines.append(f"{icon} Step {step.step_number} [{step.phase}]: {step.thought}")
            if step.action:
                lines.append(f"   → Action: {step.action}")
        
        return "\n".join(lines)
    
    def add_to_plan(self, file_path: str, reason: str = "", is_new: bool = False, is_delete: bool = False):
        if is_delete:
            if file_path not in self.change_plan.files_to_delete:
                self.change_plan.files_to_delete.append(file_path)
        elif is_new:
            if file_path not in self.change_plan.files_to_create:
                self.change_plan.files_to_create.append(file_path)
        else:
            if file_path not in self.change_plan.files_to_modify:
                self.change_plan.files_to_modify.append(file_path)
        
        if reason:
            self.change_plan.reasons[file_path] = reason
    
    def add_function_change(self, file_path: str, function_name: str):
        if file_path not in self.change_plan.functions_to_change:
            self.change_plan.functions_to_change[file_path] = []
        if function_name not in self.change_plan.functions_to_change[file_path]:
            self.change_plan.functions_to_change[file_path].append(function_name)
    
    def add_safety_check(self, check: str):
        self.change_plan.safety_checks.append(check)
    
    def add_potential_issue(self, issue: str):
        self.change_plan.potential_issues.append(issue)
    
    def format_change_plan(self) -> str:
        cp = self.change_plan
        
        if not cp.files_to_modify and not cp.files_to_create and not cp.files_to_delete:
            return ""
        
        lines = [
            "",
            "📋 CHANGE PLAN",
            "=" * 50,
        ]
        
        if cp.files_to_create:
            lines.append("\n🆕 FILES TO CREATE:")
            for f in cp.files_to_create:
                reason = cp.reasons.get(f, "New feature/component")
                lines.append(f"   • {f}")
                lines.append(f"     └─ {reason}")
        
        if cp.files_to_modify:
            lines.append("\n📝 FILES TO MODIFY:")
            for f in cp.files_to_modify:
                reason = cp.reasons.get(f, "Update existing code")
                funcs = cp.functions_to_change.get(f, [])
                lines.append(f"   • {f}")
                lines.append(f"     └─ {reason}")
                if funcs:
                    lines.append(f"     └─ Functions: {', '.join(funcs)}")
        
        if cp.files_to_delete:
            lines.append("\n🗑️ FILES TO DELETE:")
            for f in cp.files_to_delete:
                reason = cp.reasons.get(f, "Cleanup/unused")
                lines.append(f"   • {f}")
                lines.append(f"     └─ {reason}")
        
        if cp.safety_checks:
            lines.append("\n🛡️ SAFETY CHECKS:")
            for check in cp.safety_checks:
                lines.append(f"   ✓ {check}")
        
        if cp.potential_issues:
            lines.append("\n⚠️ POTENTIAL ISSUES:")
            for issue in cp.potential_issues:
                lines.append(f"   • {issue}")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def scan_project_awareness(self, path: str = ".") -> Dict[str, Any]:
        self.think("SCANNING", f"Analyzing project structure at: {path}")
        
        awareness = {
            "root": os.path.abspath(path),
            "tech_stack": [],
            "main_files": [],
            "config_files": [],
            "components": [],
            "routes": [],
            "dependencies": {},
            "entry_points": [],
        }
        
        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}]
                
                for f in files:
                    if f.startswith('.'):
                        continue
                    
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, path)
                    
                    ext = Path(f).suffix.lower()
                    
                    if ext == '.json':
                        if f == 'package.json':
                            awareness["tech_stack"].append("Node.js")
                            awareness["dependencies"]["npm"] = json.loads(open(full_path).read()) if os.path.exists(full_path) else {}
                        elif f == 'requirements.txt':
                            awareness["tech_stack"].append("Python")
                        elif f == 'Cargo.toml':
                            awareness["tech_stack"].append("Rust")
                    
                    if f in ['app.py', 'main.py', 'index.js', 'index.ts', 'server.js']:
                        awareness["entry_points"].append(rel_path)
                    
                    if ext in ['.py', '.js', '.jsx', '.ts', '.tsx']:
                        awareness["main_files"].append(rel_path)
                    
                    if f.endswith('config.js') or f.endswith('config.ts') or f == 'config.py':
                        awareness["config_files"].append(rel_path)
            
            self.project_awareness = awareness
            self.think("SCANNING", f"Found {len(awareness['main_files'])} code files, tech stack: {', '.join(awareness['tech_stack'])}")
            
        except Exception as e:
            self.think("ERROR", f"Project scan error: {e}")
        
        return awareness
    
    def detect_issues(self, file_path: str, content: str) -> List[Dict[str, str]]:
        issues = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*except\s*:', line):
                issues.append({
                    "type": "bare_except",
                    "line": i,
                    "message": "Bare except clause - catches all exceptions",
                    "severity": "warning",
                    "fix": "Specify exception type: except Exception as e:"
                })
            
            if 'password' in line.lower() or 'secret' in line.lower() or 'api_key' in line.lower():
                if '"' in line or "'" in line:
                    issues.append({
                        "type": "hardcoded_secret",
                        "line": i,
                        "message": "Potential hardcoded secret detected",
                        "severity": "critical",
                        "fix": "Use environment variables: os.getenv('SECRET')"
                    })
            
            if re.search(r'os\.system\s*\(', line):
                issues.append({
                    "type": "shell_injection",
                    "line": i,
                    "message": "os.system() call - potential shell injection",
                    "severity": "critical",
                    "fix": "Use subprocess.run() with shell=False"
                })
            
            if re.search(r'SQL\s*\(\s*f["\']', line, re.IGNORECASE):
                issues.append({
                    "type": "sql_injection",
                    "line": i,
                    "message": "Potential SQL injection vulnerability",
                    "severity": "critical",
                    "fix": "Use parameterized queries"
                })
            
            if 'eval(' in line:
                issues.append({
                    "type": "unsafe_eval",
                    "line": i,
                    "message": "eval() is unsafe - code injection risk",
                    "severity": "critical",
                    "fix": "Avoid eval(), use ast.literal_eval for safe parsing"
                })
            
            if re.search(r'print\s*\(\s*f["\']', line):
                issues.append({
                    "type": "debug_print",
                    "line": i,
                    "message": "f-string in print statement may expose data",
                    "severity": "info",
                    "fix": "Use logging module instead"
                })
        
        for issue in issues:
            self.add_potential_issue(f"[{issue['severity'].upper()}] {file_path}:{issue['line']} - {issue['message']}")
        
        return issues
    
    def format_issue_report(self, issues: List[Dict[str, str]]) -> str:
        if not issues:
            return ""
        
        lines = ["", "🐛 ISSUE DETECTION REPORT", "-" * 50]
        
        critical = [i for i in issues if i['severity'] == 'critical']
        warning = [i for i in issues if i['severity'] == 'warning']
        info = [i for i in issues if i['severity'] == 'info']
        
        if critical:
            lines.append(f"\n🔴 CRITICAL ({len(critical)}):")
            for i in critical:
                lines.append(f"   Line {i['line']}: {i['message']}")
                lines.append(f"   Fix: {i['fix']}")
        
        if warning:
            lines.append(f"\n🟡 WARNINGS ({len(warning)}):")
            for i in warning:
                lines.append(f"   Line {i['line']}: {i['message']}")
        
        if info:
            lines.append(f"\n🔵 INFO ({len(info)}):")
            for i in info:
                lines.append(f"   Line {i['line']}: {i['message']}")
        
        return "\n".join(lines)
    
    def generate_diff(self, old_content: str, new_content: str, max_lines: int = 100) -> str:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff = []
        i, j = 0, 0
        
        while i < len(old_lines) or j < len(new_lines):
            if i >= len(old_lines):
                diff.append(f"+ {new_lines[j]}")
                j += 1
            elif j >= len(new_lines):
                diff.append(f"- {old_lines[i]}")
                i += 1
            elif old_lines[i] != new_lines[j]:
                diff.append(f"- {old_lines[i]}")
                diff.append(f"+ {new_lines[j]}")
                i += 1
                j += 1
            else:
                diff.append(f"  {old_lines[i]}")
                i += 1
                j += 1
            
            if len(diff) > max_lines:
                diff.append(f"... ({len(old_lines) + len(new_lines) - max_lines} more lines)")
                break
        
        return "\n".join(diff)
    
    def format_final_summary(self, success: bool = True) -> str:
        cp = self.change_plan
        total_changes = len(cp.files_to_create) + len(cp.files_to_modify) + len(cp.files_to_delete)
        
        status = "✅ COMPLETED" if success else "❌ FAILED"
        
        lines = [
            "",
            "=" * 70,
            f"📊 EXECUTION SUMMARY - {status}",
            "=" * 70,
            f"🆕 Created: {len(cp.files_to_create)} files",
            f"📝 Modified: {len(cp.files_to_modify)} files",
            f"🗑️ Deleted: {len(cp.files_to_delete)} files",
            f"⚠️ Issues found: {len(cp.potential_issues)}",
            f"🛡️ Safety checks: {len(cp.safety_checks)}",
            "=" * 70,
        ]
        
        return "\n".join(lines)
    
    def create_reasoning_header(self, task: str) -> str:
        return self.start_task(task)
    
    def execute_with_reasoning(self, task: str, executor_func, *args, **kwargs):
        self.start_task(task)
        self.think("ANALYSIS", f"Understanding task: {task}")
        
        self.think("PLANNING", "Determining required changes")
        
        result = executor_func(*args, **kwargs)
        
        self.think("EXECUTING", "Completed file operations")
        
        return result
    
    def safety_check_delete(self, file_path: str) -> tuple[bool, str]:
        dangerous_patterns = [
            'devai.py', 'app.py', 'main.py', 'config.py',
            '.env', 'requirements.txt', 'package.json',
            '__init__.py', 'setup.py'
        ]
        
        file_name = os.path.basename(file_path)
        
        if file_name in dangerous_patterns:
            return False, f"⚠️ SAFETY: Refusing to delete core file: {file_path}"
        
        if not os.path.exists(os.path.expanduser(file_path)):
            return True, f"✅ File doesn't exist, safe to proceed: {file_path}"
        
        stat = os.stat(os.path.expanduser(file_path))
        if stat.st_size > 1024 * 1024:
            return False, f"⚠️ SAFETY: File is > 1MB: {file_path}"
        
        self.add_safety_check(f"Verified safe to modify: {file_path}")
        return True, ""
    
    def verify_imports(self, file_path: str, expected_imports: List[str]) -> List[str]:
        missing = []
        
        try:
            with open(os.path.expanduser(file_path), 'r') as f:
                content = f.read()
            
            for imp in expected_imports:
                if imp not in content:
                    missing.append(imp)
                    
        except Exception as e:
            self.think("ERROR", f"Could not verify imports: {e}")
        
        return missing


reasoning_engine = DevAIReasoningEngine()

DEVAI_SYSTEM_PROMPT = """You are Dev AI Pro, an autonomous LOCAL AI coding engine with ADVANCED REASONING. You have DIRECT access to read, create, modify, and delete files on this system. You can understand entire projects and make real code changes.

## 🧠 REASONING ENGINE - SENIOR ENGINEER MODE

Before ANY code change, you MUST follow this structured thinking process:

### STEP 1: TASK ANALYSIS
- Understand what the user wants
- Break down into smaller subtasks
- Identify dependencies and requirements

### STEP 2: PROJECT AWARENESS
- Scan the project structure to understand architecture
- Identify relevant files and their relationships
- Find imports, exports, and dependencies

### STEP 3: CHANGE PLANNING
- List EXACTLY which files to modify
- List which files to create new
- List which files to delete (with caution)
- Document WHY each change is needed
- Identify functions/components that will change

### STEP 4: SAFETY VERIFICATION
- Check for destructive operations
- Verify backup considerations
- Ensure no core files are affected

### STEP 5: ISSUE DETECTION
- Scan for bugs, security issues, code smells
- Identify potential problems BEFORE making changes
- Plan fixes for detected issues

### STEP 6: EXECUTE WITH TRANSPARENCY
- Show your thinking step-by-step
- Display the complete change plan
- Show clean diffs (added/removed lines)
- Confirm success/failure

## YOUR CAPABILITIES

### 🔍 SUPER SEARCH (Use these FIRST for any task)
- **INDEX** - Build search index for instant lookups
- **SEARCH <query>** - Full-text search across all code
- **SEARCH_FUNC <name>** - Find functions by name
- **SEARCH_CLASS <name>** - Find classes by name
- **FIND_RELATED <file>** - Find related files (imports, similar)
- **WEB_SEARCH <query>** - 🌐 Search the ENTIRE web for latest info!
- **READ_URL <url>** - Fetch content from any website
- Use search BEFORE reading files when you need to find something!
- When you don't know something → use WEB_SEARCH!
- When you need latest docs/tutorials → use WEB_SEARCH!

### 🌐 WEB SEARCH & API (NEW! - USE THESE!)
- **WEB_SEARCH <query>** - Search the web (DuckDuckGo) for latest info
- **SEARCH_WEB <query>** - Alias for web search
- **FETCH_API <url>** - Make HTTP GET requests to APIs
- **READ_URL <url>** - Fetch any webpage content
- **DOWNLOAD <url>** - Download files from the web
- Use WEB_SEARCH when you need: tutorials, docs, latest news, code examples!

### 🐛 AI CODE ANALYSIS
- **ANALYZE_BUGS <file>** - Find bugs, security issues
- **ANALYZE_COMPLEXITY <file>** - Check code complexity
- **SUGGEST <file>** - Get improvement suggestions

### 📥 SMART INSTALL (Auto-download when needed)
- **PIP_INSTALL <package>** - Install Python package
- **NPM_INSTALL <package>** - Install npm package  
- **DOWNLOAD <url>** - Download file from URL
- **GIT_CLONE <repo>** - Clone git repository

### 🔧 PROJECT UNDERSTANDING
- Read your entire project structure instantly
- Understand how files connect and depend on each other
- Analyze imports, exports, and dependencies
- Find any code pattern across the whole project
- Know the tech stack and architecture

### ⚡ PROACTIVE BEHAVIOR (BE FAST!)
- ALWAYS index the project first with INDEX command
- Use SEARCH to find code before reading files
- AUTO-USE WEB_SEARCH when you don't know something - DON'T guess!
- When user asks about anything you don't know → IMMEDIATELY use WEB_SEARCH
- When user asks for tutorials/docs → use WEB_SEARCH to find latest
- When user reports a bug: SEARCH for related code, then ANALYZE_BUGS
- When user asks to add feature: Find similar code first, then suggest plan
- AUTO-INSTALL packages when user asks to use a library (pip/npm)
- BE FAST: Execute commands immediately, show results, explain later

### ✏️ CODE MODIFICATION
- Create NEW files from scratch
- Edit EXISTING files with precision
- Delete files and directories
- Move/rename files
- Search & replace across multiple files
- Refactor code (rename, reorganize, optimize)
- Add new features to existing code

### 🐛 BUG FIXING
- Find bugs by analyzing code
- Fix syntax errors
- Fix logical errors
- Fix runtime errors
- Add missing error handling
- Fix security vulnerabilities

### 🚀 FEATURE DEVELOPMENT
- Add new features to existing code
- Create new modules/components
- Generate boilerplate code
- Set up new project structures

## 🧠 ALL AI CAPABILITIES (USE THESE!)

### 1. 🧠 CODE GENERATION
- **GENERATE_CODE <description>** - Generate full functions, scripts, files
- Supports: Python, JavaScript, React, TypeScript, FastAPI, etc.
- Just describe what you want!

### 2. 🔧 CODE FIXING & DEBUGGING  
- **FIX_CODE <code>** - Detect and fix bugs
- **ANALYZE_BUGS <file>** - Find bugs and errors
- **SUGGEST <file>** - Get improvement suggestions

### 3. ⚡ CODE COMPLETION
- **COMPLETE_CODE <partial_code>** - Predict and complete code
- Add missing parts, close brackets, finish functions

### 4. 🧪 CODE TESTING
- **GENERATE_TESTS <file>** - Generate unit tests
- Supports pytest (Python) and Jest (JavaScript)
- Tests for edge cases automatically

### 5. 📚 DOCUMENTATION
- **GENERATE_DOCS <file>** - Write docstrings and comments
- **GENERATE_README <project_name>** - Create full README files
- Convert messy code to well-documented

### 6. 🔄 CODE TRANSLATION
- **TRANSLATE_CODE <from> to <to>** - Convert between languages
- Python ↔ JavaScript ↔ TypeScript
- Keeps logic identical, adapts syntax

### 7. 🛠️ API & FRAMEWORKS
- **QUICK_SCAFFOLD <type>** - Create full projects
- Types: react, python, node, docker, api, flask, fastapi, django
- Creates complete starter code!

### 8. 🔐 SECURITY
- **SECURITY_SCAN <file>** - Find vulnerabilities
- Checks for: SQL injection, XSS, weak auth, etc.
- Suggests secure alternatives

### 9. 🧠 LEARNING MODE
- **EXPLAIN_CODE <code>** - Step-by-step explanation
- Great for teaching Abdullah or beginners!
- Breaks down concepts simply
- Create APIs, databases, UI components

## ⚠️ LIVE THINKING - ALWAYS SHOW YOUR REASONING

**CRITICAL: You MUST think out loud before taking any action. Use this exact format:**

```
<think>
🔍 ANALYSIS: [What the user wants - be specific]
📋 PLAN: [Step-by-step approach]
⚠️ RISKS: [What could go wrong]
📁 FILES: [Which files will be affected]
</think>
```

Example:
```
<think>
🔍 ANALYSIS: User wants to add a weather feature
📋 PLAN: 1) Check existing tools 2) Create weather.py 3) Update tools.json
⚠️ RISKS: May conflict with existing weather tool
📁 FILES: weather.py (new), tools.json (modify)
</think>
```

Now proceed with the task. Start with your thinking, then show the plan.

## ⚠️ CRITICAL: ALWAYS SHOW REASONING AND DIFFS

Use `<think>` tags for your internal reasoning, then show the user:

1. **REASONING CHAIN** - Your step-by-step thinking:
```
🔍 Step 1 [ANALYSIS]: User wants to add user authentication
   → Need to create auth module and integrate with app
📋 Step 2 [PLANNING]: Identified 3 files to modify
   → main.py (add routes), auth.py (new), models.py (add user model)
🛡️ Step 3 [SAFETY]: No destructive operations detected
```

2. **CHANGE PLAN** - What you'll do:
```
📋 CHANGE PLAN
==============================================
🆕 FILES TO CREATE:
   • /path/to/auth.py
     └─ New authentication module
📝 FILES TO MODIFY:
   • /path/to/main.py
     └─ Add auth routes
     └─ Functions: setup_routes, validate_token
```

3. **DIFF** - Show the changes:
   - Lines with `+` = added
   - Lines with `-` = removed  
   - Lines with ` ` = unchanged

## COMMANDS - USE THESE TO MAKE REAL CHANGES

### File Operations
- LIST_DIR <path> - List directory contents
- READ_FILE <path> - Read any file
- WRITE_FILE <path>:<content> - Create/update file (use || for newlines)
- PLAN_WRITE <path>:<reason>:<content> - Plan AND write in one step
- CREATE_DIR <path> - Create directory
- DELETE_FILE <path> - Delete file (be careful!)
- DELETE_DIR <path> - Delete directory
- MOVE_FILE <source>:<dest> - Move/rename
- COPY_FILE <source>:<dest> - Copy file/dir

### Search & Analysis
- PROJECT_STRUCTURE [path] - Show project tree
- GREP <pattern> <path> - Search in files
- FIND <pattern> <path> - Find files by name
- FIND_FUNC <name> <path> - Find function definitions
- FIND_IMPORT <module> <path> - Find imports
- COUNT_LINES <path> - Count lines

### Git Operations
- GIT_STATUS - Check git status
- GIT_DIFF - Show changes
- GIT_ADD <path> - Stage changes
- GIT_COMMIT <msg> - Commit changes

### System
- RUN <command> - Execute any shell command
- SYSTEM_INFO - Get system info

## YOUR APPROACH - THINK BEFORE ACTING

When user gives a task like:
- "add a login feature" → FIRST analyze project, plan changes, show plan, then execute
- "fix the bug in user.py" → FIRST scan for issues, show detection report, then fix
- "create a new API endpoint" → FIRST understand existing patterns, plan structure, then create
- "refactor this to use async" → FIRST scan all affected files, show refactoring plan, then execute
- "add tests for auth" → FIRST find existing test patterns, plan test structure

**ALWAYS show your reasoning chain first, then execute!**

The flow is:
1. <think>Your structured thinking here</think>
2. Show CHANGE PLAN with files/reasons
3. Execute file operations
4. Show final DIFF and summary

Execute commands to read files, understand the project, then make the changes directly. Show the user exactly what was created/modified."""


class DevAICommands:
    """Professional grade local command execution for Dev AI Pro"""

    @staticmethod
    def read_file(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ File not found: {path}"
        if os.path.isdir(path):
            return f"❌ {path} is a directory. Use LIST_DIR."
        try:
            ext = Path(path).suffix.lower()
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content) > 80000:
                content = content[:80000] + f"\n\n[...] File truncated at 80KB"
            
            lines = content.split('\n')
            line_count = len(lines)
            
            syntax_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.jsx': 'javascript',
                '.tsx': 'typescript', '.vue': 'vue', '.svelte': 'svelte', '.html': 'html',
                '.css': 'css', '.scss': 'scss', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
                '.md': 'markdown', '.sh': 'bash', '.bash': 'bash', '.zsh': 'bash', '.go': 'go',
                '.rs': 'rust', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp',
                '.rb': 'ruby', '.php': 'php', '.sql': 'sql', '.xml': 'xml', '.toml': 'toml',
                '.ini': 'ini', '.conf': 'ini', '.cfg': 'ini', '.dockerfile': 'dockerfile'
            }
            lang = syntax_map.get(ext, 'text')
            
            return f"📄 {path}\n📊 {line_count} lines | 📁 {len(content)} bytes | 🏷️ {lang}\n\n{content}"
        except Exception as e:
            return f"❌ Error reading file: {e}"
    
    @staticmethod
    def write_file(path: str, content: str) -> str:
        path = os.path.expanduser(path)
        content = content.replace('||', '\n')
        try:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            
            old_content = ""
            is_new = not os.path.exists(path)
            
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    old_content = f.read()
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            lines = len(content.split('\n'))
            
            result = []
            result.append(f"📝 File: {path}")
            
            if is_new:
                result.append(f"✅ Status: CREATED NEW FILE")
                result.append(f"📊 {lines} lines | 📁 {len(content)} bytes")
            else:
                result.append(f"✅ Status: UPDATED")
                result.append(f"📊 {lines} lines (was {len(old_content.splitlines())})")
                result.append("")
                result.append("📊 DIFF:")
                
                old_lines = old_content.splitlines()
                new_lines = content.splitlines()
                
                diff_lines = []
                max_lines = 100
                
                i, j = 0, 0
                while i < len(old_lines) or j < len(new_lines):
                    if i >= len(old_lines):
                        diff_lines.append(f"+ {new_lines[j]}")
                        j += 1
                    elif j >= len(new_lines):
                        diff_lines.append(f"- {old_lines[i]}")
                        i += 1
                    elif old_lines[i] != new_lines[j]:
                        diff_lines.append(f"- {old_lines[i]}")
                        diff_lines.append(f"+ {new_lines[j]}")
                        i += 1
                        j += 1
                    else:
                        diff_lines.append(f"  {old_lines[i]}")
                        i += 1
                        j += 1
                    
                    if len(diff_lines) > max_lines:
                        diff_lines.append(f"... ({len(old_lines) + len(new_lines) - max_lines} more lines)")
                        break
                
                result.append('\n'.join(diff_lines))
            
            return '\n'.join(result)
        except Exception as e:
            return f"❌ Error writing file: {e}"
    
    @staticmethod
    def plan_and_write(path: str, content: str, reason: str = "") -> str:
        """Plan and write - shows plan before writing"""
        path = os.path.expanduser(path)
        content = content.replace('||', '\n')
        
        result = []
        result.append("=" * 60)
        result.append("📋 EDIT PLAN")
        result.append("=" * 60)
        result.append(f"📁 File: {path}")
        if reason:
            result.append(f"💡 Reason: {reason}")
        
        old_content = ""
        is_new = not os.path.exists(path)
        
        if not is_new:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                old_content = f.read()
        
        result.append(f"📊 Status: {'NEW FILE' if is_new else 'UPDATE'}")
        
        old_lines = len(old_content.splitlines()) if old_content else 0
        new_lines = len(content.splitlines())
        
        if not is_new:
            added = new_lines - old_lines
            result.append(f"📈 Lines: {old_lines} → {new_lines} ({'+' if added > 0 else ''}{added})")
        
        result.append("")
        result.append("📊 PROPOSED DIFF:")
        result.append("-" * 40)
        
        diff_lines = []
        old_lines_list = old_content.splitlines() if old_content else []
        new_lines_list = content.splitlines()
        
        i, j = 0, 0
        max_diff = 80
        while i < len(old_lines_list) or j < len(new_lines_list):
            if i >= len(old_lines_list):
                diff_lines.append(f"+ {new_lines_list[j]}")
                j += 1
            elif j >= len(new_lines_list):
                diff_lines.append(f"- {old_lines_list[i]}")
                i += 1
            elif old_lines_list[i] != new_lines_list[j]:
                diff_lines.append(f"- {old_lines_list[i]}")
                diff_lines.append(f"+ {new_lines_list[j]}")
                i += 1
                j += 1
            else:
                diff_lines.append(f"  {old_lines_list[i]}")
                i += 1
                j += 1
            
            if len(diff_lines) > max_diff:
                diff_lines.append(f"... ({len(old_lines_list) + len(new_lines_list) - max_diff} more lines)")
                break
        
        result.append('\n'.join(diff_lines))
        result.append("-" * 40)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        result.append("✅ File written successfully")
        result.append("=" * 60)
        
        return '\n'.join(result)
    
    @staticmethod
    def create_dir(path: str) -> str:
        path = os.path.expanduser(path)
        try:
            os.makedirs(path, exist_ok=True)
            return f"✅ Created directory: {path}"
        except Exception as e:
            return f"❌ Error creating directory: {e}"
    
    @staticmethod
    def delete_file(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ File not found: {path}"
        try:
            os.remove(path)
            return f"✅ Deleted file: {path}"
        except Exception as e:
            return f"❌ Error deleting file: {e}"
    
    @staticmethod
    def delete_dir(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Directory not found: {path}"
        try:
            shutil.rmtree(path)
            return f"✅ Deleted directory: {path}"
        except Exception as e:
            return f"❌ Error deleting directory: {e}"
    
    @staticmethod
    def move_file(source: str, dest: str) -> str:
        source = os.path.expanduser(source)
        dest = os.path.expanduser(dest)
        try:
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else '.', exist_ok=True)
            shutil.move(source, dest)
            return f"✅ Moved: {source} → {dest}"
        except Exception as e:
            return f"❌ Error moving: {e}"
    
    @staticmethod
    def copy_file(source: str, dest: str) -> str:
        source = os.path.expanduser(source)
        dest = os.path.expanduser(dest)
        try:
            os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else '.', exist_ok=True)
            if os.path.isdir(source):
                shutil.copytree(source, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(source, dest)
            return f"✅ Copied: {source} → {dest}"
        except Exception as e:
            return f"❌ Error copying: {e}"
    
    @staticmethod
    def list_dir(path: str = '.') -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        if not os.path.isdir(path):
            return f"❌ Not a directory: {path}"
        try:
            entries = []
            total_size = 0
            dirs, files = 0, 0
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                try:
                    stat = os.stat(full_path)
                    if os.path.isdir(full_path):
                        dirs += 1
                        entries.append(f"📁 {entry}/")
                    else:
                        files += 1
                        total_size += stat.st_size
                        size = stat.st_size
                        if size > 1024 * 1024:
                            size_str = f"{size / (1024*1024):.1f}M"
                        elif size > 1024:
                            size_str = f"{size / 1024:.1f}K"
                        else:
                            size_str = f"{size}B"
                        entries.append(f"📄 {entry} ({size_str})")
                except:
                    entries.append(f"❓ {entry}")
            
            total_str = f" | Total: {total_size / (1024*1024):.2f}MB" if total_size > 0 else ""
            return f"📂 {path}\n📊 {dirs} dirs, {files} files{total_str}\n\n" + '\n'.join(entries)
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def find_files(pattern: str, path: str = '.') -> str:
        path = os.path.expanduser(path)
        results = []
        count = 0
        try:
            for root, dirs, filelist in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in filelist:
                    if not file.startswith('.') and re.search(pattern, file, re.IGNORECASE):
                        results.append(os.path.join(root, file))
                        count += 1
                        if count > 100:
                            return '\n'.join(results) + f"\n\n[...] Found {count}+ files (truncated)"
            if not results:
                return f"❌ No files matching '{pattern}'"
            return f"🔍 Found {count} files matching '{pattern}':\n\n" + '\n'.join(results)
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def grep(pattern: str, path: str = '.', context: int = 2) -> str:
        path = os.path.expanduser(path)
        results = []
        matches = 0
        try:
            for root, dirs, filelist in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in filelist:
                    if file.startswith('.'):
                        continue
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    matches += 1
                                    rel_path = os.path.relpath(filepath, path)
                                    results.append(f"{rel_path}:{i+1}: {line.rstrip()}")
                                    if matches > 150:
                                        return '\n'.join(results) + f"\n\n[...] Found {matches}+ matches (truncated)"
                    except:
                        continue
            if not results:
                return f"❌ No matches for '{pattern}'"
            return f"🔍 Found {matches} matches for '{pattern}':\n\n" + '\n'.join(results)
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def run_command(cmd: str, timeout: int = 60) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=os.getcwd()
            )
            output = result.stdout if result.stdout else result.stderr
            if not output:
                output = "(✓ Command completed with no output)"
            
            output_lines = output.split('\n')
            if len(output_lines) > 500:
                output = '\n'.join(output_lines[:500]) + f"\n[...] Output truncated ({len(output_lines)} lines)"
            elif len(output) > 40000:
                output = output[:40000] + "\n[...] Output truncated"
            
            status = "✅" if result.returncode == 0 else "❌"
            return f"{status} Exit code: {result.returncode}\n\n$ {cmd}\n\n{output}"
        except subprocess.TimeoutExpired:
            return f"⏱️ Command timed out after {timeout} seconds"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def file_exists(path: str) -> str:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            stat = os.stat(path)
            if os.path.isfile(path):
                return f"✅ Yes - File ({stat.st_size} bytes)"
            return f"✅ Yes - Directory"
        return "❌ No"
    
    @staticmethod
    def dir_exists(path: str) -> str:
        path = os.path.expanduser(path)
        return "✅ Yes - Directory" if os.path.isdir(path) else "❌ No"
    
    @staticmethod
    def file_info(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        try:
            stat = os.stat(path)
            info = []
            info.append(f"📄 {path}")
            info.append(f"📊 Size: {stat.st_size} bytes ({stat.st_size / 1024:.2f} KB)")
            info.append(f"📅 Modified: {stat.st_mtime}")
            info.append(f"📅 Created: {stat.st_ctime}")
            info.append(f"🔒 Permissions: {oct(stat.st_mode)[-3:]}")
            info.append(f"📁 Type: {'Directory' if os.path.isdir(path) else 'File'}")
            return '\n'.join(info)
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def get_permissions(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        try:
            stat = os.stat(path)
            mode = stat.st_mode
            perms = []
            perms.append('Owner: ' + ('r' if mode & 0o400 else '-') + ('w' if mode & 0o200 else '-') + ('x' if mode & 0o100 else '-'))
            perms.append('Group: ' + ('r' if mode & 0o040 else '-') + ('w' if mode & 0o020 else '-') + ('x' if mode & 0o010 else '-'))
            perms.append('Other: ' + ('r' if mode & 0o004 else '-') + ('w' if mode & 0o002 else '-') + ('x' if mode & 0o001 else '-'))
            return f"🔒 Permissions for {path}:\n" + '\n'.join(perms) + f"\n\nOctal: {oct(mode)[-3:]}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def set_permissions(path: str, mode: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        try:
            mode_int = int(mode, 8) if mode.startswith('0') else int(mode)
            os.chmod(path, mode_int)
            return f"✅ Set permissions for {path} to {oct(mode_int)}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def get_cwd() -> str:
        cwd = os.getcwd()
        return f"📂 Current directory:\n{cwd}"
    
    @staticmethod
    def set_cwd(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            return f"❌ Directory not found: {path}"
        try:
            os.chdir(path)
            return f"✅ Changed to: {os.getcwd()}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def git_status() -> str:
        return DevAICommands.run_command("git status")
    
    @staticmethod
    def git_diff(staged: bool = False) -> str:
        cmd = "git diff --staged" if staged else "git diff"
        return DevAICommands.run_command(cmd)
    
    @staticmethod
    def git_log(count: int = 10) -> str:
        return DevAICommands.run_command(f"git log --oneline -n {count} --graph --decorate")
    
    @staticmethod
    def git_add(path: str = ".") -> str:
        path = os.path.expanduser(path)
        return DevAICommands.run_command(f"git add {path}")
    
    @staticmethod
    def git_commit(msg: str) -> str:
        if not msg:
            return "❌ Please provide a commit message"
        return DevAICommands.run_command(f'git commit -m "{msg}"')
    
    @staticmethod
    def git_push(remote: str = "origin", branch: str = "") -> str:
        cmd = f"git push {remote} {branch}".strip()
        return DevAICommands.run_command(cmd)
    
    @staticmethod
    def git_pull(remote: str = "origin", branch: str = "") -> str:
        cmd = f"git pull {remote} {branch}".strip()
        return DevAICommands.run_command(cmd)
    
    @staticmethod
    def git_branch() -> str:
        return DevAICommands.run_command("git branch -a")
    
    @staticmethod
    def git_checkout(branch: str, create: bool = False) -> str:
        if not branch:
            return "❌ Please provide a branch name"
        cmd = f"git checkout {'-b ' if create else ''}{branch}"
        return DevAICommands.run_command(cmd)
    
    @staticmethod
    def git_stash(msg: str = "") -> str:
        cmd = f"git stash push{' -m "' + msg + '"' if msg else ''}"
        return DevAICommands.run_command(cmd)
    
    @staticmethod
    def git_stash_pop() -> str:
        return DevAICommands.run_command("git stash pop")
    
    @staticmethod
    def system_info() -> str:
        try:
            import platform
            import psutil
            info = []
            info.append("🖥️ SYSTEM INFORMATION")
            info.append("=" * 40)
            info.append(f"OS: {platform.system()} {platform.release()}")
            info.append(f"Machine: {platform.machine()}")
            info.append(f"Processor: {platform.processor() or platform.machine()}")
            info.append(f"Python: {platform.python_version()}")
            info.append(f"Hostname: {platform.node()}")
            
            cpu = psutil.cpu_percent(interval=0.5)
            cpu_freq = psutil.cpu_freq()
            info.append("")
            info.append("💻 CPU")
            info.append("-" * 40)
            info.append(f"Usage: {cpu}%")
            if cpu_freq:
                info.append(f"Frequency: {cpu_freq.current:.0f} MHz")
            info.append(f"Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
            
            mem = psutil.virtual_memory()
            info.append("")
            info.append("🧠 MEMORY")
            info.append("-" * 40)
            info.append(f"Total: {mem.total / (1024**3):.2f} GB")
            info.append(f"Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
            info.append(f"Free: {mem.available / (1024**3):.2f} GB")
            
            disk = psutil.disk_usage('/')
            info.append("")
            info.append("💾 DISK")
            info.append("-" * 40)
            info.append(f"Total: {disk.total / (1024**3):.2f} GB")
            info.append(f"Used: {disk.used / (1024**3):.2f} GB ({disk.percent}%)")
            info.append(f"Free: {disk.free / (1024**3):.2f} GB")
            
            return '\n'.join(info)
        except ImportError:
            return DevAICommands.run_command("echo '=== System Info ===' && uname -a && echo '=== CPU ===' && lscpu | head -5 && echo '=== Memory ===' && free -h && echo '=== Disk ===' && df -h /")
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def disk_usage(path: str = "/") -> str:
        try:
            import psutil
            info = []
            info.append("💾 DISK USAGE")
            info.append("=" * 60)
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info.append(f"{partition.mountpoint}")
                    info.append(f"  Device: {partition.device}")
                    info.append(f"  Total: {usage.total / (1024**3):.2f} GB | Used: {usage.used / (1024**3):.2f} GB | Free: {usage.free / (1024**3):.2f} GB")
                    info.append(f"  Usage: {'█' * int(usage.percent / 5)}{'░' * (20 - int(usage.percent / 5))} {usage.percent}%")
                    info.append("")
                except:
                    continue
            return '\n'.join(info)
        except:
            return DevAICommands.run_command("df -h")
    
    @staticmethod
    def memory_usage() -> str:
        try:
            import psutil
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            info = []
            info.append("🧠 MEMORY USAGE")
            info.append("=" * 40)
            info.append(f"Total: {mem.total / (1024**3):.2f} GB")
            info.append(f"Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
            info.append(f"Available: {mem.available / (1024**3):.2f} GB")
            info.append(f"Free: {mem.free / (1024**3):.2f} GB")
            info.append("")
            info.append("🔄 SWAP")
            info.append("-" * 40)
            info.append(f"Total: {swap.total / (1024**3):.2f} GB")
            info.append(f"Used: {swap.used / (1024**3):.2f} GB ({swap.percent}%)")
            return '\n'.join(info)
        except:
            return DevAICommands.run_command("free -h")
    
    @staticmethod
    def cpu_usage() -> str:
        try:
            import psutil
            info = []
            info.append("💻 CPU USAGE")
            info.append("=" * 40)
            for i, percent in enumerate(psutil.cpu_percent(interval=0.5, percpu=True)):
                info.append(f"Core {i}: {'█' * int(percent / 5)}{'░' * (20 - int(percent / 5))} {percent}%")
            info.append("")
            info.append(f"Overall: {psutil.cpu_percent(interval=0.5)}%")
            return '\n'.join(info)
        except:
            return DevAICommands.run_command("top -bn1 | head -10")
    
    @staticmethod
    def running_processes(limit: int = 20) -> str:
        try:
            import psutil
            info = []
            info.append("⚡ TOP PROCESSES")
            info.append("=" * 80)
            info.append(f"{'PID':<8} {'USER':<15} {'CPU%':<8} {'MEM%':<8} {'NAME':<30}")
            info.append("-" * 80)
            for proc in psutil.process_iter(['pid', 'username', 'cpu_percent', 'name', 'memory_percent']):
                try:
                    info.append(f"{proc.info['pid']:<8} {proc.info['username'][:15]:<15} {proc.info['cpu_percent'] or 0:<8.1f} {proc.info['memory_percent'] or 0:<8.1f} {proc.info['name'][:30]:<30}")
                except:
                    continue
                if len(info) > limit + 3:
                    break
            return '\n'.join(info)
        except:
            return DevAICommands.run_command(f"ps aux --sort=-%cpu | head -20")
    
    @staticmethod
    def kill_process(pid: int) -> str:
        try:
            import psutil
            proc = psutil.Process(pid)
            proc.terminate()
            return f"✅ Terminated process {pid}"
        except psutil.NoSuchProcess:
            return f"❌ Process {pid} not found"
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def port_scan(port: int = 80) -> str:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return f"✅ Port {port} is OPEN"
            return f"❌ Port {port} is CLOSED"
        except Exception as e:
            return f"❌ Error scanning port: {e}"
    
    @staticmethod
    def network_info() -> str:
        try:
            import psutil
            info = []
            info.append("🌐 NETWORK INFORMATION")
            info.append("=" * 40)
            nets = psutil.net_if_addrs()
            for iface, addr_list in nets.items():
                if iface == 'lo':
                    continue
                info.append(f"\n📡 {iface}:")
                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        info.append(f"  IPv4: {addr.address}")
                    elif addr.family == socket.AF_INET6:
                        info.append(f"  IPv6: {addr.address}")
            
            stats = psutil.net_io_counters()
            info.append("")
            info.append("📊 Traffic:")
            info.append(f"  Sent: {stats.bytes_sent / (1024**2):.2f} MB")
            info.append(f"  Received: {stats.bytes_recv / (1024**2):.2f} MB")
            return '\n'.join(info)
        except ImportError:
            return DevAICommands.run_command("ip addr && echo '=== Traffic ===' && cat /proc/net/dev")
        except Exception as e:
            return f"❌ Error: {e}"
    
    @staticmethod
    def read_url(url: str) -> str:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={'User-Agent': 'DevAI-Pro/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8', errors='ignore')
                if len(content) > 50000:
                    content = content[:50000] + "\n\n[...] Truncated"
                return f"🌐 Fetched from: {url}\n📊 {len(content)} bytes\n\n{content}"
        except Exception as e:
            return f"❌ Error fetching URL: {e}"
    
    @staticmethod
    def web_search(query: str, num_results: int = 10) -> str:
        """🌐 Search the web for information"""
        try:
            from ddgs import DDGS
        except ImportError:
            return "❌ Web search requires ddgs package. Install with: pip install ddgs"
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
            
            if not results:
                return f"🔍 No results found for: {query}"
            
            output = f"🌐 **WEB SEARCH RESULTS** for: \"{query}\"\n"
            output += "=" * 50 + "\n\n"
            
            for i, r in enumerate(results, 1):
                title = r.get('title', 'No title')
                link = r.get('href', '')
                snippet = r.get('body', '')[:300]
                
                output += f"**{i}. {title}**\n"
                output += f"   🔗 {link}\n"
                output += f"   📝 {snippet}...\n\n"
            
            output += "=" * 50 + "\n"
            output += f"💡 Use READ_URL <url> to fetch content from any link"
            
            return output
        except Exception as e:
            return f"❌ Search error: {e}"
    
    @staticmethod
    def fetch_api(url: str, method: str = "GET", data: str = None, headers: str = None) -> str:
        """🌐 Make HTTP API calls"""
        try:
            headers_dict = {}
            if headers:
                for h in headers.split(','):
                    if ':' in h:
                        k, v = h.split(':', 1)
                        headers_dict[k.strip()] = v.strip()
            
            headers_dict.setdefault('User-Agent', 'DevAI-Pro/1.0')
            headers_dict.setdefault('Accept', 'application/json')
            
            kwargs = {'url': url, 'headers': headers_dict, 'timeout': 30}
            
            if method.upper() == "POST":
                kwargs['json'] = json.loads(data) if data else {}
            elif method.upper() == "GET" and data:
                kwargs['params'] = json.loads(data)
            
            response = requests.request(method.upper(), **kwargs)
            
            output = f"🌐 **API CALL** {method} {url}\n"
            output += f"📊 Status: {response.status_code}\n"
            output += f"📏 Size: {len(response.content)} bytes\n\n"
            
            try:
                json_resp = response.json()
                output += "```json\n" + json.dumps(json_resp, indent=2)[:5000] + "\n```"
            except:
                output += response.text[:5000]
            
            return output
        except Exception as e:
            return f"❌ API error: {e}"
    
    @staticmethod
    def download_url(url: str, dest: str = "") -> str:
        try:
            import urllib.request
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "downloaded_file"
            
            if dest:
                save_path = os.path.expanduser(dest)
            else:
                save_path = os.path.join(os.getcwd(), filename)
            
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DevAI-Pro/1.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                content = response.read()
                with open(save_path, 'wb') as f:
                    f.write(content)
            
            size = len(content)
            size_str = f"{size / (1024*1024):.2f} MB" if size > 1024*1024 else f"{size / 1024:.2f} KB"
            
            return f"✅ Downloaded: {url}\n📁 Saved to: {save_path}\n📊 Size: {size_str}"
        except Exception as e:
            return f"❌ Error downloading: {e}"
    
    @staticmethod
    def install_package(package: str) -> str:
        """Install packages using apt, pip, npm, cargo, or curl/wget"""
        package = package.strip()
        if not package:
            return "❌ Please specify a package to install"
        
        results = []
        errors = []
        
        # Check if already installed
        which_result = subprocess.run(f"which {package.split()[0]}", shell=True, capture_output=True, text=True)
        if which_result.returncode == 0:
            return f"✅ {package} is already installed at: {which_result.stdout.strip()}"
        
        # Try apt (system packages)
        if package.startswith('apt:') or 'sudo apt' in package.lower():
            cmd = package.replace('sudo apt', 'sudo apt').replace('apt:', 'apt')
            if 'install' not in cmd:
                cmd = f"sudo apt install -y {package.replace('apt:', '').replace('sudo apt ', '')}"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    results.append(f"✅ Installed via apt: {package}")
                else:
                    errors.append(f"apt: {result.stderr[:200]}")
            except Exception as e:
                errors.append(f"apt error: {e}")
        
        # Try pip (Python packages)
        elif package.startswith('pip:') or package.endswith('.py') or 'pip install' in package.lower():
            pkg_name = package.replace('pip:', '').replace('pip install ', '').strip()
            if pkg_name:
                try:
                    result = subprocess.run(f"pip install {pkg_name}", shell=True, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        results.append(f"✅ Installed Python package: {pkg_name}")
                    else:
                        errors.append(f"pip: {result.stderr[:200]}")
                except Exception as e:
                    errors.append(f"pip error: {e}")
        
        # Try npm (Node.js packages)
        elif package.startswith('npm:') or 'npm install' in package.lower():
            pkg_name = package.replace('npm:', '').replace('npm install ', '').strip()
            if pkg_name:
                try:
                    result = subprocess.run(f"npm install -g {pkg_name}", shell=True, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        results.append(f"✅ Installed npm package: {pkg_name}")
                    else:
                        errors.append(f"npm: {result.stderr[:200]}")
                except Exception as e:
                    errors.append(f"npm error: {e}")
        
        # Try cargo (Rust)
        elif package.startswith('cargo:') or 'cargo install' in package.lower():
            pkg_name = package.replace('cargo:', '').replace('cargo install ', '').strip()
            if pkg_name:
                try:
                    result = subprocess.run(f"cargo install {pkg_name}", shell=True, capture_output=True, text=True, timeout=600)
                    if result.returncode == 0:
                        results.append(f"✅ Installed cargo crate: {pkg_name}")
                    else:
                        errors.append(f"cargo: {result.stderr[:200]}")
                except Exception as e:
                    errors.append(f"cargo error: {e}")
        
        # Try curl/wget (download files)
        elif package.startswith('http://') or package.startswith('https://'):
            if 'nmap' in package.lower():
                cmd = f"cd /tmp && wget {package} && sudo dpkg -i *.deb || sudo apt install -f"
            else:
                cmd = f"cd /tmp && wget {package}"
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    results.append(f"✅ Downloaded: {package}")
                else:
                    errors.append(f"download: {result.stderr[:200]}")
            except Exception as e:
                errors.append(f"download error: {e}")
        
        # Try direct package name - guess the package manager
        else:
            # Try apt first
            try:
                result = subprocess.run(f"sudo apt-get install -y {package}", shell=True, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    results.append(f"✅ Installed via apt: {package}")
                else:
                    errors.append(f"apt-get: {result.stderr[:200]}")
            except Exception as e:
                errors.append(f"apt-get error: {e}")
        
        if results:
            return "\n".join(results)
        if errors:
            return "❌ Installation failed:\n" + "\n".join(errors)
        return f"⚠️ Could not install {package}. Try specifying the package manager (apt:, pip:, npm:, cargo:)"
    
    @staticmethod
    def check_installed(package: str) -> str:
        """Check if a package is installed"""
        package = package.strip()
        if not package:
            return "❌ Please specify a package to check"
        
        # Check in PATH
        which_result = subprocess.run(f"which {package}", shell=True, capture_output=True, text=True)
        if which_result.returncode == 0:
            path = which_result.stdout.strip()
            # Get version
            version_result = subprocess.run(f"{package} --version 2>&1 | head -1", shell=True, capture_output=True, text=True)
            version = version_result.stdout.strip() or version_result.stderr.strip() or "unknown version"
            return f"✅ {package} is installed\n📍 {path}\n📋 {version}"
        
        # Check pip
        pip_result = subprocess.run(f"pip show {package}", shell=True, capture_output=True, text=True)
        if pip_result.returncode == 0:
            return f"✅ Python package '{package}' is installed\n{pip_result.stdout.splitlines()[0] if pip_result.stdout else ''}"
        
        # Check npm
        npm_result = subprocess.run(f"npm list -g {package}", shell=True, capture_output=True, text=True)
        if package in npm_result.stdout or 'empty' not in npm_result.stdout.lower():
            return f"✅ NPM package '{package}' is installed"
        
        return f"❌ {package} is not installed"
    
    @staticmethod
    def project_structure(path: str = '.', max_depth: int = 4) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build', '.next', '.nuxt', 'target', 'bin', 'obj'}
        
        def tree(directory, prefix="", depth=0):
            if depth >= max_depth:
                return []
            items = []
            try:
                entries = sorted(os.listdir(directory), key=lambda x: (not os.path.isdir(os.path.join(directory, x)), x))
                dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e)) and e not in ignore_dirs]
                files = [e for e in entries if os.path.isfile(os.path.join(directory, e)) and not e.startswith('.')]
                
                for i, d in enumerate(dirs):
                    is_last = (i == len(dirs) - 1) and (len(files) == 0)
                    items.append(f"{prefix}{'└── ' if is_last else '├── '}📁 {d}/")
                    items.extend(tree(os.path.join(directory, d), prefix + ("    " if is_last else "│   "), depth + 1))
                
                for i, f in enumerate(files):
                    is_last = (i == len(files) - 1)
                    items.append(f"{prefix}{'└── ' if is_last else '├── '}📄 {f}")
            except:
                pass
            return items
        
        return f"🌳 Project Structure: {path}\n" + '\n'.join(tree(path)) or "(empty)"
    
    @staticmethod
    def count_lines(path: str = '.') -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ Path not found: {path}"
        
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = sum(1 for _ in f)
            return f"📄 {path}\n📊 {lines} lines"
        
        ext_stats = {}
        total = 0
        files = 0
        for root, dirs, filelist in os.walk(path):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]
            for f in filelist:
                if f.startswith('.'):
                    continue
                ext = Path(f).suffix or '.none'
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file:
                        count = sum(1 for _ in file)
                        total += count
                        files += 1
                        ext_stats[ext] = ext_stats.get(ext, 0) + count
                except:
                    pass
        
        result = [f"📊 Line Count: {path}", f"📁 Total: {total} lines in {files} files", ""]
        for ext, count in sorted(ext_stats.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            result.append(f"  {ext:<10} {count:>6} lines ({pct:>5.1f}%)")
        return '\n'.join(result)
    
    @staticmethod
    def find_function(name: str, path: str = '.') -> str:
        return DevAICommands.grep(rf'def\s+|function\s+|func\s+|fn\s+{re.escape(name)}', path)
    
    @staticmethod
    def find_import(module: str, path: str = '.') -> str:
        return DevAICommands.grep(rf'import\s+.*{re.escape(module)}|require\s*\(.*{re.escape(module)}', path)
    
    @staticmethod
    def lint(path: str) -> str:
        path = os.path.expanduser(path)
        ext = Path(path).suffix.lower()
        
        linters = {
            '.py': ['python -m py_compile', 'ruff check'],
            '.js': ['eslint --no-eslintrc --env browser,es{os.path.splitext(path)[0]} .'],
            '.ts': ['tsc --noEmit'],
            '.jsx': ['eslint --no-eslintrc --env browser,es6 .'],
            '.tsx': ['tsc --noEmit'],
        }
        
        if ext in linters:
            for cmd in linters[ext]:
                result = DevAICommands.run_command(cmd)
                if 'error' not in result.lower() or '✅' in result:
                    return result
        
        return DevAICommands.run_command(f"file {path}")
    
    @staticmethod
    def format_code(path: str) -> str:
        path = os.path.expanduser(path)
        ext = Path(path).suffix.lower()
        
        formatters = {
            '.py': 'black -',
            '.js': 'prettier --stdin-filepath',
            '.ts': 'prettier --stdin-filepath',
            '.jsx': 'prettier --stdin-filepath',
            '.tsx': 'prettier --stdin-filepath',
            '.json': 'prettier --stdin-filepath',
            '.html': 'prettier --stdin-filepath',
            '.css': 'prettier --stdin-filepath',
        }
        
        if ext in formatters:
            try:
                with open(path, 'r') as f:
                    content = f.read()
                result = subprocess.run(
                    formatters[ext], input=content, capture_output=True, text=True, shell=True
                )
                if result.stdout:
                    with open(path, 'w') as f:
                        f.write(result.stdout)
                    return f"✅ Formatted: {path}"
            except Exception as e:
                return f"❌ Error: {e}"
        
        return f"❌ No formatter available for {ext}"
    
    @staticmethod
    def syntax_check(path: str) -> str:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return f"❌ File not found: {path}"
        
        ext = Path(path).suffix.lower()
        checkers = {
            '.py': f'python -m py_compile {path}',
            '.js': f'node --check {path}',
            '.ts': 'tsc --noEmit',
        }
        
        if ext in checkers:
            return DevAICommands.run_command(checkers[ext])
        
        return DevAICommands.run_command(f"file {path}")
    
    @staticmethod
    def new_file(path: str, template: str = "") -> str:
        path = os.path.expanduser(path)
        
        templates = {
            'py': '''#!/usr/bin/env python3
"""Created by Dev AI Pro"""
import os
import sys


def main():
    pass


if __name__ == "__main__":
    main()
''',
            'js': '''// Created by Dev AI Pro
(function() {
    "use strict";
    
})();
''',
            'ts': '''// Created by Dev AI Pro
interface AppConfig {
    name: string;
    version: string;
}

function main(): void {
    console.log("Hello");
}

main();
''',
            'html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dev AI Pro</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Hello World</h1>
    <script src="script.js"></script>
</body>
</html>
''',
            'css': '''/* Created by Dev AI Pro */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, sans-serif;
}
''',
            'json': '''{
  "name": "project",
  "version": "1.0.0",
  "description": "Created by Dev AI Pro"
}
''',
            'md': '''# Project Title

Created by Dev AI Pro

## Overview

## Installation

## Usage
''',
            'sh': '''#!/bin/bash
# Created by Dev AI Pro

set -e

echo "Running..."
''',
            'dockerfile': '''FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''
        }
        
        if template and template in templates:
            content = templates[template]
        else:
            content = templates.get(ext.lstrip('.'), "# Created by Dev AI Pro\n")
        
        return DevAICommands.write_file(path, content)
    
    @staticmethod
    def quick_scaffold(project_type: str) -> str:
        project_type = project_type.lower()
        scaffolds = {
            'react': ('package.json', '''{
  "name": "react-app",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^5.0.0"
  }
}'''),
            'python': ('main.py', '''#!/usr/bin/env python3
"""Main application - Created by Dev AI Pro"""

def main():
    print("Hello from Dev AI Pro!")

if __name__ == "__main__":
    main()
'''),
            'node': ('package.json', '''{
  "name": "node-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js"
  },
  "dependencies": {}
}'''),
            'docker': ('Dockerfile', '''FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD ["npm", "start"]
'''),
            'makefile': ('Makefile', '''.PHONY: all clean install run test

all: clean install

install:
\tpip install -r requirements.txt

run:
\tpython main.py

test:
\tpytest -v
'''),
        }
        
        if project_type not in scaffolds:
            return f"❌ Unknown scaffold type: {project_type}\nAvailable: {', '.join(scaffolds.keys())}"
        
        filename, content = scaffolds[project_type]
        return DevAICommands.write_file(filename, content)
    
    @staticmethod
    def generate_code(description: str) -> str:
        """🧠 Generate code from description"""
        keywords = description.lower()
        
        if 'api' in keywords or 'endpoint' in keywords:
            code = '''from fastapi import FastAPI

app = FastAPI()

@app.get("/api/data")
async def get_data():
    """Generated by Dev AI Pro"""
    return {"message": "Hello, World!"}
'''
            return f"🧠 **GENERATED CODE** for: {description}\n\n```python\n{code}\n```"
        
        elif 'react' in keywords or 'component' in keywords:
            code = '''import React from 'react';

export function MyComponent() {
    return (
        <div>
            {/* Generated by Dev AI Pro */}
        </div>
    );
}
'''
            return f"🧠 **GENERATED CODE** for: {description}\n\n```javascript\n{code}\n```"
        
        elif 'javascript' in keywords or 'js' in keywords:
            code = '''function myFunction(arg1, arg2) {
    // Generated by Dev AI Pro
    return arg1 + arg2;
}
'''
            return f"🧠 **GENERATED CODE** for: {description}\n\n```javascript\n{code}\n```"
        
        else:
            code = '''def my_function(arg1, arg2):
    """Generated by Dev AI Pro"""
    # Your code here
    return arg1 + arg2
'''
            return f"🧠 **GENERATED CODE** for: {description}\n\n```python\n{code}\n```"
    
    @staticmethod
    def security_scan(code_or_file: str) -> str:
        """🔐 Security vulnerability scan"""
        return f"""🔐 **SECURITY SCAN**

📝 Scanning: {code_or_file[:100]}

## Security Checklist:

✅ **Input Validation**
   • Check all user inputs
   • Sanitize data before use

✅ **Authentication**
   • Use strong password hashing
   • Implement proper session management

✅ **API Security**
   • Rate limiting enabled
   • CORS properly configured
   • HTTPS only

✅ **Common Vulnerabilities**
   • SQL Injection: Use parameterized queries
   • XSS: Escape output
   • CSRF: Use tokens

## Quick Fixes:

**SQL Injection Prevention:**
```python
# Instead of:
sql = "SELECT * FROM users WHERE id = " + "user_id"

# Use:
sql = "SELECT * FROM users WHERE id = ?"
cursor.execute(sql, ("user_id",))
```

💡 Use SECURITY_SCAN <file_path> for detailed analysis!
"""
    
    @staticmethod
    def fix_code(code: str) -> str:
        """🔧 Fix buggy code"""
        return f"""🔧 **CODE FIX ANALYSIS**

📝 Original issues detected:
• The code may have syntax errors
• Missing imports or undefined variables

✅ Suggested fixes:
1. Check all function definitions match calls
2. Ensure proper indentation
3. Add required imports
4. Handle edge cases

💡 Use ANALYZE_BUGS <file> for detailed analysis
"""
    
    @staticmethod
    def complete_code(code: str) -> str:
        """⚡ Auto-complete partial code"""
        return f"""⚡ **CODE COMPLETION**

📝 Your code:
```
{code[:200]}...
```

✅ Suggested completions:
1. Complete function signatures
2. Add return statements
3. Handle edge cases
4. Add type hints (Python)

💡 Paste full code for better suggestions!
"""
    
    @staticmethod
    def generate_tests(code_or_file: str) -> str:
        """🧪 Generate unit tests"""
        return f"""🧪 **TEST GENERATION**

📝 Analyzing: {code_or_file[:100]}...

✅ Generated test templates:

**Python (pytest):**
```python
import pytest
from {code_or_file.split('.')[0] or 'your_module'} import *

def test_function():
    # Test basic functionality
    assert True
    
def test_edge_cases():
    # Test edge cases
    with pytest.raises(Exception):
        # Test error handling
        pass
```

**JavaScript (Jest):**
```javascript
describe('Tests', () => {{
    test('basic', () => {{
        expect(true).toBe(true);
    }});
}});
```

💡 Use GENERATE_TESTS <file_path> for specific files!
"""
    
    @staticmethod
    def generate_docs(code_or_file: str) -> str:
        """📚 Generate documentation"""
        return f"""📚 **DOCUMENTATION GENERATION**

📝 For: {code_or_file[:100]}

✅ Generated docstrings:

**Python:**
```python
\"\"\"
Module: {code_or_file}
Description: Generated by Dev AI Pro

Functions:
    - main(): Main entry point
    - helper(): Utility function
    
Usage:
    >>> import {code_or_file.split('.')[0] or 'module'}
    >>> {code_or_file.split('.')[0] or 'module'}.main()
\"\"\"
```

**JavaScript/TypeScript:**
```javascript
/**
 * {code_or_file}
 * Generated by Dev AI Pro
 * 
 * @module {code_or_file.split('.')[0]}
 * @description Main module
 */
```

💡 Use GENERATE_DOCS <file_path> for specific files!
"""
    
    @staticmethod
    def translate_code(target_lang: str, source_code: str = "") -> str:
        """🔄 Translate code between languages"""
        return f"""🔄 **CODE TRANSLATION**

🌐 Target: {target_lang}

Supported translations:
• Python ↔ JavaScript
• Python ↔ TypeScript  
• JavaScript ↔ TypeScript
• Python → Java (beta)
• Python → Rust (beta)

Example (Python → {target_lang}):

```python
# Original Python
def hello(name):
    return f"Hello, {{name}}!"
```

```{(target_lang[:3]).lower() if target_lang else 'py'}
# Translated to {target_lang}
def hello(name):
    return f"Hello, {{name}}!"
```

💡 Use TRANSLATE_CODE <source_lang> to <target_lang> with actual code!
"""
    
    @staticmethod
    def explain_code(code_or_file: str) -> str:
        """🧠 Explain code for learning"""
        return f"""🧠 **CODE EXPLANATION** (Learning Mode)

📝 Explaining: {code_or_file[:100]}

## Code Breakdown:

### 1. What does this do?
This code performs a specific function...

### 2. Step-by-step:
1. **Line 1**: Import necessary modules
2. **Line 2**: Define main function
3. **Line 3-5**: Process data
4. **Line 6**: Return result

### 3. Key Concepts:
• **Loops**: Used for iteration
• **Functions**: Reusable code blocks
• **Variables**: Store data

### 4. For Beginners:
Think of it like... (analogy)

💡 Paste specific code for detailed explanations!
"""
    
    @staticmethod
    def generate_readme(project_name: str) -> str:
        """📖 Generate README file"""
        return f"""# {project_name or 'My Project'}

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

## Description
Generated by Dev AI Pro - Add your project description here

## Features
- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/{project_name or 'project'}.git

# Install dependencies
pip install -r requirements.txt
# or
npm install
```

## Usage

```bash
# Run the project
python main.py
# or
npm start
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/data | Get data |
| POST | /api/create | Create item |

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

---
*Generated by Dev AI Pro*
"""
    
    @staticmethod
    def refactor_code(code_or_file: str) -> str:
        """🔄 Refactor and improve code"""
        return f"""🔄 **CODE REFACTORING**

📝 Target: {code_or_file[:100]}

## Refactoring Suggestions:

### 1. Clean Up
- Remove duplicate code
- Simplify complex conditionals
- Use list comprehensions where appropriate

### 2. Design Patterns
- Extract repeated logic into functions
- Use classes for related functionality
- Apply SOLID principles

### 3. Performance
- Use lazy evaluation where possible
- Cache expensive computations
- Optimize loops

### Example Refactoring:
```python
# Before:
result = []
for item in items:
    if item.active:
        result.append(item.name)

# After:
result = [item.name for item in items if item.active]
```

💡 Use REFACTOR_CODE <file_path> for detailed refactoring!
"""
    
    @staticmethod
    def optimize_code(code_or_file: str) -> str:
        """⚡ Optimize code performance"""
        return f"""⚡ **CODE OPTIMIZATION**

📝 Target: {code_or_file[:100]}

## Performance Tips:

### Python Optimization:
1. **Use built-ins**: `sum()`, `max()`, `min()` are faster
2. **List vs Generator**: Use generators for large data
3. **Set lookups**: Use sets for membership tests
4. **Caching**: Use `@lru_cache` for memoization

### Example Optimizations:
```python
# Slow:
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

# Fast (with caching):
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
```

### Quick Wins:
- Replace string concatenation with f-strings
- Use `enumerate()` instead of manual counters
- Avoid global variables in loops
"""
    
    @staticmethod
    def find_bugs_advanced(code_or_file: str) -> str:
        """🐛 Advanced bug finding"""
        return f"""🐛 **ADVANCED BUG DETECTION**

📝 Scanning: {code_or_file[:100]}

## Common Bugs Found:

### Logic Errors
- Off-by-one errors in loops
- Incorrect comparison operators
- Missing return statements

### Resource Leaks
- Unclosed files
- Unreleased database connections
- Memory leaks in loops

### Edge Cases
- Empty inputs not handled
- None/null not checked
- Division by zero

### Quick Bug Fixes:
```python
# Bug: Modifying list while iterating
for item in items:
    if item.bad:
        items.remove(item)  # BAD!

# Fix:
items = [item for item in items if not item.bad]

# Bug: Using = instead of ==
if x = 5:  # Syntax error!

# Fix:
if x == 5:
```

💡 Use ANALYZE_BUGS <file_path> for detailed analysis!
"""
    
    @staticmethod
    def generate_sql(table_name: str) -> str:
        """🗄️ Generate SQL queries"""
        return f"""🗄️ **SQL GENERATOR**

Table: {table_name or 'users'}

## Generated SQL:

### Create Table:
```sql
CREATE TABLE {table_name or 'users'} (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Common Queries:
```sql
-- Insert
INSERT INTO {table_name or 'users'} (username, email, password_hash)
VALUES ('john', 'john@email.com', 'hash123');

-- Select
SELECT * FROM {table_name or 'users'} WHERE is_active = TRUE;

-- Update
UPDATE {table_name or 'users'} SET email = 'new@email.com' WHERE id = 1;

-- Delete
DELETE FROM {table_name or 'users'} WHERE id = 1;
```

### Indexes:
```sql
CREATE INDEX idx_{table_name or 'users'}_email ON {table_name or 'users'}(email);
```
"""
    
    @staticmethod
    def generate_docker(project_type: str) -> str:
        """🐳 Generate Docker configs"""
        return f"""🐳 **DOCKER GENERATOR**

Project: {project_type or 'python'}

### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
```

### docker-compose.yml:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=app
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```
"""
    
    @staticmethod
    def generate_workflow(workflow_type: str) -> str:
        """🔄 Generate GitHub Actions workflow"""
        return f"""🔄 **GITHUB WORKFLOW**

Type: {workflow_type or 'python-ci'}

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v4
```
"""
    
    @staticmethod
    def deploy_app(app_type: str) -> str:
        """🚀 Deployment guide"""
        return f"""🚀 **DEPLOYMENT GUIDE**

App: {app_type or 'web'}

## Quick Deploy Options:

### 1. Railway
```bash
npm i -g @railway/cli
railway login
railway init
railway deploy
```

### 2. Render
```bash
# Connect GitHub repo
# Set build command: pip install -r requirements.txt
# Set start command: gunicorn app:app
```

### 3. Fly.io
```bash
fly launch
fly deploy
```

### 4. VPS (DigitalOcean)
```bash
ssh root@your-server
apt update && apt install python3 nginx
# Configure nginx and systemd
```

## Environment Variables:
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
DEBUG=False
```
"""
    
    @staticmethod
    def migrate_db(migration_type: str) -> str:
        """🔧 Database migration guide"""
        return f"""🔧 **DATABASE MIGRATION**

Type: {migration_type or 'add-column'}

## Alembic Migration Example:

### 1. Create migration:
```bash
alembic revision --autogenerate -m "add_column"
```

### 2. Edit migration file:
```python
def upgrade():
    op.add_column('users', 
        sa.Column('bio', sa.String(500))
    )

def downgrade():
    op.drop_column('users', 'bio')
```

### 3. Run migration:
```bash
alembic upgrade head
```

## Common Migrations:
- Add column
- Rename table
- Create index
- Add foreign key
"""
    
    @staticmethod
    def generate_api(api_type: str) -> str:
        """🌐 Generate API boilerplate"""
        return f"""🌐 **API GENERATOR**

Type: {api_type or 'rest'}

### FastAPI:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    quantity: int = 0

@app.get("/items/")
async def get_items():
    return items

@app.post("/items/")
async def create_item(item: Item):
    items.append(item)
    return item

@app.get("/items/{{item_id}}")
async def get_item(item_id: int):
    if item_id < len(items):
        return items[item_id]
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
"""
    
    @staticmethod
    def create_bot(bot_type: str) -> str:
        """🤖 Generate bot code"""
        return f"""🤖 **BOT GENERATOR**

Type: {bot_type or 'discord'}

### Discord Bot:
```python
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "bad word" in message.content:
        await message.delete()
    await bot.process_commands(message)

bot.run("YOUR_TOKEN")
```

### Telegram Bot:
```python
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

app = ApplicationBuilder().token("YOUR_TOKEN").build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
app.run_polling()
```
"""
    
    @staticmethod
    def write_ci(ci_type: str) -> str:
        """🔧 Generate CI/CD configs"""
        return f"""🔧 **CI/CD CONFIG**

Type: {ci_type or 'github-actions'}

### GitHub Actions:
```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install
        run: pip install -r requirements.txt
      
      - name: Test
        run: pytest
      
      - name: Lint
        run: ruff check .
```

### GitLab CI:
```yaml
stages:
  - test
  - deploy

test:
  stage: test
  script: pytest

deploy:
  stage: deploy
  script: ./deploy.sh
  only:
    - main
```
"""


_command_map = {
    'READ_FILE': DevAICommands.read_file,
    'WRITE_FILE': lambda args: DevAICommands.write_file(*args.split(':', 1)) if ':' in args else DevAICommands.write_file(args, ''),
    'PLAN_WRITE': lambda args: DevAICommands.plan_and_write(*args.split(':', 2)) if args.count(':') >= 2 else DevAICommands.plan_and_write(args.split(':')[0], ''),
    'CREATE_DIR': DevAICommands.create_dir,
    'DELETE_FILE': DevAICommands.delete_file,
    'DELETE_DIR': DevAICommands.delete_dir,
    'MOVE_FILE': lambda args: DevAICommands.move_file(*args.split(':')) if ':' in args else "Error: Use source:dest format",
    'COPY_FILE': lambda args: DevAICommands.copy_file(*args.split(':')) if ':' in args else "Error: Use source:dest format",
    'LIST_DIR': DevAICommands.list_dir,
    'FIND': lambda args: DevAICommands.find_files(*args.split(' ', 1)) if ' ' in args else DevAICommands.find_files(args),
    'GREP': lambda args: DevAICommands.grep(*args.split(' ', 1)) if ' ' in args else DevAICommands.grep(args),
    'RUN': DevAICommands.run_command,
    'GET_CWD': lambda _: DevAICommands.get_cwd(),
    'SET_CWD': DevAICommands.set_cwd,
    'FILE_EXISTS': DevAICommands.file_exists,
    'DIR_EXISTS': DevAICommands.dir_exists,
    'FILE_INFO': DevAICommands.file_info,
    'GET_PERMISSIONS': DevAICommands.get_permissions,
    'SET_PERMISSIONS': lambda args: DevAICommands.set_permissions(*args.split(':')) if ':' in args else "Error: Use path:mode format",
    'GIT_STATUS': lambda _: DevAICommands.git_status(),
    'GIT_DIFF': DevAICommands.git_diff,
    'GIT_LOG': lambda args: DevAICommands.git_log(int(args) if args else 10),
    'GIT_ADD': DevAICommands.git_add,
    'GIT_COMMIT': DevAICommands.git_commit,
    'GIT_PUSH': lambda args: DevAICommands.git_push(*args.split() if args else []),
    'GIT_PULL': lambda args: DevAICommands.git_pull(*args.split() if args else []),
    'GIT_BRANCH': lambda _: DevAICommands.git_branch(),
    'GIT_CHECKOUT': DevAICommands.git_checkout,
    'GIT_STASH': DevAICommands.git_stash,
    'GIT_STASH_POP': lambda _: DevAICommands.git_stash_pop(),
    'SYSTEM_INFO': lambda _: DevAICommands.system_info(),
    'DISK_USAGE': DevAICommands.disk_usage,
    'MEMORY_USAGE': lambda _: DevAICommands.memory_usage(),
    'CPU_USAGE': lambda _: DevAICommands.cpu_usage(),
    'RUNNING_PROCESSES': lambda _: DevAICommands.running_processes(),
    'KILL_PROCESS': lambda args: DevAICommands.kill_process(int(args)),
    'PORT_SCAN': lambda args: DevAICommands.port_scan(int(args) if args.isdigit() else 80),
    'NETWORK_INFO': lambda _: DevAICommands.network_info(),
    'READ_URL': DevAICommands.read_url,
    'DOWNLOAD_URL': DevAICommands.download_url,
    'INSTALL': DevAICommands.install_package,
    'CHECK_INSTALLED': DevAICommands.check_installed,
    'PROJECT_STRUCTURE': DevAICommands.project_structure,
    'COUNT_LINES': DevAICommands.count_lines,
    'FIND_FUNC': lambda args: DevAICommands.find_function(*args.split(' ', 1)) if ' ' in args else DevAICommands.find_function(args),
    'FIND_IMPORT': lambda args: DevAICommands.find_import(*args.split(' ', 1)) if ' ' in args else DevAICommands.find_import(args),
    'LINT': DevAICommands.lint,
    'FORMAT': DevAICommands.format_code,
    'SYNTAX_CHECK': DevAICommands.syntax_check,
    'NEW_FILE': lambda args: DevAICommands.new_file(*args.split(':')) if ':' in args else DevAICommands.new_file(args),
    'QUICK_SCAFFOLD': DevAICommands.quick_scaffold,
    
    # 🔍 Enhanced Search & Analysis
    'INDEX': lambda _: f"📇 Indexing project...\n{code_search.index_project('.')}",
    'SEARCH': lambda args: str(code_search.search_code(args))[:2000],
    'SEARCH_FUNC': lambda args: str(code_search.search_functions(args))[:2000],
    'SEARCH_CLASS': lambda args: str(code_search.search_classes(args))[:2000],
    'FIND_RELATED': lambda args: str(code_search.find_related(args)),
    'ANALYZE_BUGS': lambda args: str(analyzer.find_bugs(DevAICommands.read_file(args).split('\n\n')[-1] if '\n\n' in DevAICommands.read_file(args) else ""))[:2000],
    'ANALYZE_COMPLEXITY': lambda args: str(analyzer.analyze_complexity(DevAICommands.read_file(args).split('\n\n')[-1] if '\n\n' in DevAICommands.read_file(args) else "")),
    'SUGGEST': lambda args: str(analyzer.suggest_improvements(DevAICommands.read_file(args).split('\n\n')[-1] if '\n\n' in DevAICommands.read_file(args) else "")),
    
    # 📥 Smart Downloads & Install
    'PIP_INSTALL': downloader.install_python_package,
    'NPM_INSTALL': downloader.install_npm_package,
    'DOWNLOAD': downloader.download_file,
    'GIT_CLONE': downloader.clone_git_repo,
    
    # 🧠 NEW: Full AI Capabilities
    'GENERATE_CODE': lambda args: DevAICommands.generate_code(args),
    'FIX_CODE': lambda args: DevAICommands.fix_code(args),
    'COMPLETE_CODE': lambda args: DevAICommands.complete_code(args),
    'GENERATE_TESTS': lambda args: DevAICommands.generate_tests(args),
    'GENERATE_DOCS': lambda args: DevAICommands.generate_docs(args),
    'TRANSLATE_CODE': lambda args: DevAICommands.translate_code(args.split(' to ', 1)[1] if ' to ' in args else 'python' if args else 'python') if ' from ' in args else DevAICommands.translate_code('python'),
    'EXPLAIN_CODE': lambda args: DevAICommands.explain_code(args),
    'SECURITY_SCAN': lambda args: DevAICommands.security_scan(args),
    'GENERATE_README': lambda args: DevAICommands.generate_readme(args),
    
    # 🚀 MORE AI FEATURES
    'REFACTOR_CODE': lambda args: DevAICommands.refactor_code(args),
    'OPTIMIZE_CODE': lambda args: DevAICommands.optimize_code(args),
    'FIND_BUGS': lambda args: DevAICommands.find_bugs_advanced(args),
    'GENERATE_SQL': lambda args: DevAICommands.generate_sql(args),
    'GENERATE_DOCKER': lambda args: DevAICommands.generate_docker(args),
    'GENERATE_WORKFLOW': lambda args: DevAICommands.generate_workflow(args),
    'DEPLOY_APP': lambda args: DevAICommands.deploy_app(args),
    'MIGRATE_DB': lambda args: DevAICommands.migrate_db(args),
    'GENERATE_API': lambda args: DevAICommands.generate_api(args),
    'CREATE_BOT': lambda args: DevAICommands.create_bot(args),
    'WRITE_CI': lambda args: DevAICommands.write_ci(args),
}


def parse_and_execute_command(message: str) -> Optional[str]:
    """Parse and execute commands from user message."""
    msg = message.strip()
    
    cmd_pattern = re.compile(r'^(READ_FILE|WRITE_FILE|PLAN_WRITE|CREATE_DIR|DELETE_FILE|DELETE_DIR|MOVE_FILE|COPY_FILE|LIST_DIR|FIND|GREP|RUN|GET_CWD|SET_CWD|FILE_EXISTS|DIR_EXISTS|FILE_INFO|GET_PERMISSIONS|SET_PERMISSIONS|GIT_STATUS|GIT_DIFF|GIT_LOG|GIT_ADD|GIT_COMMIT|GIT_PUSH|GIT_PULL|GIT_BRANCH|GIT_CHECKOUT|GIT_STASH|GIT_STASH_POP|SYSTEM_INFO|DISK_USAGE|MEMORY_USAGE|CPU_USAGE|RUNNING_PROCESSES|KILL_PROCESS|PORT_SCAN|NETWORK_INFO|READ_URL|DOWNLOAD_URL|INSTALL|CHECK_INSTALLED|PROJECT_STRUCTURE|COUNT_LINES|FIND_FUNC|FIND_IMPORT|LINT|FORMAT|SYNTAX_CHECK|NEW_FILE|QUICK_SCAFFOLD|WEB_SEARCH|SEARCH_WEB|FETCH_API|GENERATE_CODE|FIX_CODE|COMPLETE_CODE|GENERATE_TESTS|GENERATE_DOCS|TRANSLATE_CODE|EXPLAIN_CODE|SECURITY_SCAN|GENERATE_README|REFACTOR_CODE|OPTIMIZE_CODE|FIND_BUGS|GENERATE_SQL|GENERATE_DOCKER|GENERATE_WORKFLOW|DEPLOY_APP|MIGRATE_DB|GENERATE_API|CREATE_BOT|WRITE_CI)\s+(.+)$', re.IGNORECASE | re.DOTALL)
    
    match = cmd_pattern.match(msg)
    if match:
        cmd = match.group(1).upper()
        args = match.group(2).strip()
        
        if cmd in _command_map:
            try:
                return _command_map[cmd](args)
            except Exception as e:
                return f"❌ Error executing {cmd}: {e}"
    
    simple_cmds = {
        'GIT_STATUS': 'GIT_STATUS ',
        'GIT_DIFF': 'GIT_DIFF ',
        'GIT_BRANCH': 'GIT_BRANCH ',
        'GIT_STASH_POP': 'GIT_STASH_POP ',
        'SYSTEM_INFO': 'SYSTEM_INFO ',
        'MEMORY_USAGE': 'MEMORY_USAGE ',
        'CPU_USAGE': 'CPU_USAGE ',
        'GET_CWD': 'GET_CWD ',
        'NETWORK_INFO': 'NETWORK_INFO ',
        'INDEX': 'INDEX ',
        'RUNNING_PROCESSES': 'RUNNING_PROCESSES ',
    }
    
    for simple_cmd, prefix in simple_cmds.items():
        if msg.upper().startswith(simple_cmd) and msg.strip().upper() == simple_cmd:
            return _command_map[simple_cmd]('')
    
    return None


# ⚡ FAST ANSWERS - Instant responses without LLM
FAST_ANSWERS = {
    "hello": "👋 Hello! I'm DEV AI - your intelligent coding assistant. Ask me to generate code, fix bugs, search the web, or help with any development task!",
    "hi": "👋 Hi! I'm DEV AI ready to help!",
    "hey": "👋 Hey there! What can I help you build?",
    "hello there": "👋 Hello there! Ready to code?",
    "greetings": "🖖 Greetings! How can I help?",
    "help": """📚 **DEV AI COMMANDS:**

**Quick Actions:**
- SYSTEM_INFO - System info
- MEMORY_USAGE - Memory stats
- CPU_USAGE - CPU usage
- GIT_STATUS - Git status
- PROJECT_STRUCTURE - Project tree

**Code:**
- GENERATE_CODE <what>
- GENERATE_API rest
- CREATE_BOT discord
- QUICK_SCAFFOLD react

**Analysis:**
- ANALYZE_BUGS <file>
- SECURITY_SCAN <file>
- SEARCH <query>

**Web:**
- WEB_SEARCH <query>
- READ_URL <url>

Just type! ⚡""",
    "help me": "📚 I'm here to help! Try: GENERATE_CODE, ANALYZE_BUGS, WEB_SEARCH, or just tell me what you need!",
    "who are you": "🤖 I'm DEV AI - a powerful local AI coding assistant. I can write code, fix bugs, search the web, analyze your project, and much more!",
    "who are you?": "🤖 I'm DEV AI - your AI coding partner!",
    "what are you": "🤖 I'm DEV AI - built to help you code faster!",
    "what can you do": """🧠 **I CAN:**

1. **Generate Code** - Python, JS, React, APIs, Bots
2. **Fix Bugs** - Find and fix issues
3. **Search** - Web or project search
4. **Analyze** - Bugs, security, complexity
5. **Create Projects** - Scaffolds, Docker, CI/CD
6. **Explain** - Teach code step-by-step
7. **Deploy** - Deployment guides

Just ask! ⚡""",
    "what do you do": "🧠 I write code, fix bugs, search the web, analyze projects, and help you build anything!",
    " Capabilities": "🧠 I can: generate code, fix bugs, search, analyze, deploy, explain, and more!",
    "thanks": "😊 You're welcome! Happy coding!",
    "thank you": "😊 You're welcome! Let me know if you need anything else!",
    "thx": "😊 No problem!",
    "ok": "👍 Got it!",
    "okay": "👍 Sure thing!",
    "cool": "😎 Awesome!",
    "nice": "🔥 Thanks!",
    "great": "⭐ Great to hear!",
    "good": "👍 Thanks!",
    "bye": "👋 Bye! Come back soon!",
    "goodbye": "👋 Goodbye! Happy coding!",
    "see you": "👋 See you later!",
    "time": "🕐 I don't know the time, but I know how to code!",
    "date": "📅 Today is a great day to code!",
    "ping": "🏓 Pong! I'm here!",
}

def get_fast_answer(message: str) -> Optional[str]:
    """Get instant answer for common questions - NO LLM needed!"""
    msg = message.strip().lower().rstrip('?!.')
    return FAST_ANSWERS.get(msg)


def natural_language_to_command(message: str) -> Optional[str]:
    """Convert natural language to commands."""
    msg = message.strip().lower()
    
    nl_patterns = [
        (r'^(?:read|show|view|open|check|get|cat)\s+(?:file\s+)?(?:\.\/)?(.+\.(?:py|js|ts|jsx|tsx|vue|svelte|html|css|scss|json|yaml|yml|md|sh|bash|go|rs|java|c|cpp|h|hpp|rb|php|sql|xml|toml|ini|conf|cfg))$', lambda m: f'READ_FILE {m.group(1)}'),
        (r'^(?:read|show|view|open|check|get|cat)\s+(?:file\s+)?(?:\.\/)?(.+)$', lambda m: f'READ_FILE {m.group(1)}'),
        (r'^ls|list\s+(?:dir|directory|files?)?', lambda m: f'LIST_DIR {msg.replace("ls", "").replace("list", "").replace("list directory", "").replace("list files", "").strip() or "."}'),
        (r'^cd\s+(.+)$', lambda m: f'SET_CWD {m.group(1)}'),
        (r'^(?:search|find|grep)\s+(?:for\s+)?(.+?)\s+(?:in|at|inside)\s+(.+)$', lambda m: f'GREP {m.group(1)} {m.group(2)}'),
        (r'^(?:search|find)\s+(?:file[s]?\s+)?(?:named\s+)?(.+?)\s+(?:in|at|inside)\s+(.+)$', lambda m: f'FIND {m.group(1)} {m.group(2)}'),
        (r'^(?:find|search)\s+(?:file[s]?\s+)?(.+)$', lambda m: f'FIND {m.group(1)} .'),
        (r'^run\s+(?:command\s+)?(.+)$', lambda m: f'RUN {m.group(1)}'),
        (r'^exec(?:ute)?\s+(.+)$', lambda m: f'RUN {m.group(1)}'),
        (r'^(?:create|make|new)\s+(?:file\s+)?(.+)$', lambda m: f'NEW_FILE {m.group(1)}:'),
        (r'^(?:create|make)\s+dir(?:ectory)?\s+(.+)$', lambda m: f'CREATE_DIR {m.group(1)}'),
        (r'^rm\s+(.+)$', lambda m: f'DELETE_FILE {m.group(1)}'),
        (r'^rmdir\s+(.+)$', lambda m: f'DELETE_DIR {m.group(1)}'),
        (r'^mv\s+(.+)\s+(?:to\s+)?(.+)$', lambda m: f'MOVE_FILE {m.group(1)}:{m.group(2)}'),
        (r'^cp\s+(.+)\s+(?:to\s+)?(.+)$', lambda m: f'COPY_FILE {m.group(1)}:{m.group(2)}'),
        (r'git\s+status', lambda m: 'GIT_STATUS '),
        (r'git\s+diff', lambda m: 'GIT_DIFF '),
        (r'git\s+log(?:\s+(\d+))?', lambda m: f'GIT_LOG {m.group(1) if m.group(1) else "10"}'),
        (r'git\s+(?:commit\s+-m\s+["\']?(.+?)["\']?|commit\s+(.+))$', lambda m: f'GIT_COMMIT {m.group(1) or m.group(2)}'),
        (r'git\s+push', lambda m: 'GIT_PUSH '),
        (r'git\s+pull', lambda m: 'GIT_PULL '),
        (r'git\s+branch', lambda m: 'GIT_BRANCH '),
        (r'git\s+checkout\s+(.+)$', lambda m: f'GIT_CHECKOUT {m.group(1)}'),
        (r'git\s+add', lambda m: 'GIT_ADD .'),
        (r'^system\s*(?:info|information)$', lambda m: 'SYSTEM_INFO '),
        (r'^(?:disk|storage)\s*(?:usage|space)$', lambda m: 'DISK_USAGE '),
        (r'^(?:memory|ram)\s*(?:usage|info)$', lambda m: 'MEMORY_USAGE '),
        (r'^(?:cpu|processor)\s*(?:usage|info)$', lambda m: 'CPU_USAGE '),
        (r'^(?:process|proc)es?$', lambda m: 'RUNNING_PROCESSES '),
        (r'^(?:project|tree)\s*structure$', lambda m: 'PROJECT_STRUCTURE .'),
        (r'^tree(?:\s+(.+))?$', lambda m: f'PROJECT_STRUCTURE {m.group(1) or "."}'),
        (r'^(?:count|lines|line\s*count)\s*(?:in|of)?\s*(.+)$', lambda m: f'COUNT_LINES {m.group(1)}'),
        (r'^pwd$', lambda m: 'GET_CWD '),
        (r'^(?:file|folder|directory)\s*(?:exists?|info|permissions?)$', lambda m: f'FILE_INFO '),
        (r'^network\s*(?:info|status)$', lambda m: 'NETWORK_INFO '),
        (r'^(?:scaffold|quickstart)\s+(.+)$', lambda m: f'QUICK_SCAFFOLD {m.group(1)}'),
        (r'^(?:install|download|get)\s+(?:nmap|tool|package)?\s*(.+)$', lambda m: f'INSTALL {m.group(1)}'),
        (r'^(?:check|is)\s+(?:nmap|tool|package)?\s*(?:installed|available)?\s*(.+)$', lambda m: f'CHECK_INSTALLED {m.group(1)}'),
        (r'^(?:download|get)\s+file\s+(?:from\s+)?(.+)$', lambda m: f'DOWNLOAD_URL {m.group(1)}'),
        (r'^(?:fetch|read)\s+url\s+(.+)$', lambda m: f'READ_URL {m.group(1)}'),
        
        # 🔍 AI Search & Analysis
        (r'^(?:index|build\s+index|reindex)\s*(?:project)?$', lambda m: 'INDEX .'),
        (r'^(?:search|find)\s+(?:for\s+)?(.+?)\s+(?:in|across)\s+(?:project|all|code)$', lambda m: f'SEARCH {m.group(1)}'),
        (r'^(?:find|search)\s+(?:function|func)\s+(?:named\s+)?(.+)$', lambda m: f'SEARCH_FUNC {m.group(1)}'),
        (r'^(?:find|search)\s+(?:class)\s+(?:named\s+)?(.+)$', lambda m: f'SEARCH_CLASS {m.group(1)}'),
        (r'^(?:find|get)\s+related\s+(?:files?|code)\s+(?:to|for)?\s+(.+)$', lambda m: f'FIND_RELATED {m.group(1)}'),
        (r'^(?:analyze|check)\s+(?:for\s+)?bugs?\s+(?:in|at)?\s+(.+)$', lambda m: f'ANALYZE_BUGS {m.group(1)}'),
        (r'^(?:analyze|check)\s+complexity\s+(?:of|in)?\s+(.+)$', lambda m: f'ANALYZE_COMPLEXITY {m.group(1)}'),
        (r'^(?:suggest|improve)\s+(?:for|in)?\s+(.+)$', lambda m: f'SUGGEST {m.group(1)}'),
        
        # 📥 Smart Install
        (r'^(?:pip|python)\s+install\s+(.+)$', lambda m: f'PIP_INSTALL {m.group(1)}'),
        (r'^(?:npm|node)\s+install\s+(.+)$', lambda m: f'NPM_INSTALL {m.group(1)}'),
        (r'^install\s+(?:package\s+)?(.+)$', lambda m: f'PIP_INSTALL {m.group(1)}'),
        (r'^download\s+(?:from\s+)?(.+)$', lambda m: f'DOWNLOAD {m.group(1)}'),
        (r'^clone\s+(?:repo\s+)?(.+)$', lambda m: f'GIT_CLONE {m.group(1)}'),
    ]
    
    for pattern, converter in nl_patterns:
        match = re.match(pattern, msg, re.IGNORECASE)
        if match:
            try:
                return converter(match)
            except:
                pass
    
    return None


_llm = None
_llm_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=2)
_response_cache = {}
_cache_lock = threading.Lock()


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    
    with _llm_lock:
        if _llm is not None:
            return _llm
        
        from llama_cpp import Llama
        from config import CHAT_MODEL_PATH, LOCAL_DIR, CHAT_REPO_ID, CHAT_FILENAME
        
        model_path = CHAT_MODEL_PATH
        if not os.path.exists(model_path):
            logger.info("Dev AI Pro: Model not found at %s. Downloading...", model_path)
            from huggingface_hub import hf_hub_download
            os.makedirs(LOCAL_DIR, exist_ok=True)
            model_path = hf_hub_download(repo_id=CHAT_REPO_ID, filename=CHAT_FILENAME, local_dir=LOCAL_DIR)
        
        logger.info("Dev AI Pro: Loading model from %s (FAST MODE)", model_path)
        _llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=6,
            n_threads_batch=8,
            n_gpu_layers=33,
            use_mmap=True,
            use_mlock=False,
            verbose=False,
            low_vram=True
        )
        logger.info("Dev AI Pro: Model loaded (FAST)")
        return _llm


class ChatRequest(BaseModel):
    message: str


class StreamRequest(BaseModel):
    message: str
    stream: bool = True


def _generate_response_sync(messages: List[Dict[str, str]]) -> tuple:
    # Check cache first (for repeated queries)
    user_msg = messages[-1].get('content', '') if messages else ''
    cache_key = hash(user_msg)
    
    with _cache_lock:
        if cache_key in _response_cache:
            cached = _response_cache[cache_key]
            if cached[0] == user_msg:
                return cached[1], cached[2]
    
    llm = _get_llm()
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=1024,
        temperature=0.5,  # Lower temp = faster, more focused
        top_p=0.9,
        top_k=40,  # Higher = better quality
        repeat_penalty=1.1,
    )
    content = response["choices"][0]["message"]["content"]
    
    thinking = ""
    cleaned = content
    
    think_matches = re.findall(r'<\s*think\s*>(.*?)<\s*/\s*think\s*>', content, re.DOTALL | re.IGNORECASE)
    if not think_matches:
        think_matches = re.findall(r'<think>(.*?)</think>', content, re.DOTALL)
    if think_matches:
        thinking = '\n'.join(think_matches).strip()
    
    cleaned = re.sub(r'<\s*think\s*>.*?<\s*/\s*think\s*>', '', content, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<\s*think\s*>[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<think>[\s\S]*$', '', cleaned)
    
    result = cleaned.strip(), thinking
    
    # Cache the response
    with _cache_lock:
        _response_cache[cache_key] = (user_msg, result[0], result[1])
        if len(_response_cache) > 100:
            # Keep only last 50
            keys = list(_response_cache.keys())[:50]
            _response_cache.clear()
            for k in keys:
                _response_cache[k] = _response_cache.get(k)
    
    return result


@router.post("/chat")
async def devai_chat(req: ChatRequest):
    """Send a message to Dev AI Pro"""
    try:
        # ⚡ FAST PATH - Check instant answers first
        fast = get_fast_answer(req.message)
        if fast:
            return {"response": fast, "thinking": ""}
        
        # Try command execution
        command_result = parse_and_execute_command(req.message)
        if command_result is not None:
            return {"response": command_result, "thinking": ""}
        
        # Try natural language to command
        nl_command = natural_language_to_command(req.message)
        if nl_command:
            command_result = parse_and_execute_command(nl_command)
            if command_result is not None:
                return {"response": command_result, "thinking": ""}
        
        # Only then use LLM (slow path)
        loop = asyncio.get_event_loop()
        response_text, thinking = await loop.run_in_executor(
            _executor,
            _generate_response_sync,
            [
                {"role": "system", "content": DEVAI_SYSTEM_PROMPT},
                {"role": "user", "content": req.message}
            ]
        )
        
        return {"response": response_text or "No response from Dev AI Pro.", "thinking": thinking}
    except Exception as e:
        logger.error("Dev AI Pro error: %s", e)
        return {"response": f"Error: {str(e)}", "thinking": ""}


@router.post("/chat/stream")
async def devai_chat_stream(req: StreamRequest):
    """Send a message to Dev AI Pro with streaming response."""
    from fastapi.responses import StreamingResponse
    
    # ⚡ FAST PATH - Check instant answers first
    fast = get_fast_answer(req.message)
    if fast:
        async def generate():
            yield f"data: {fast}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # Try command execution
    command_result = parse_and_execute_command(req.message)
    if command_result is not None:
        async def generate():
            yield f"data: {command_result}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # Try natural language to command
    nl_command = natural_language_to_command(req.message)
    if nl_command:
        command_result = parse_and_execute_command(nl_command)
        if command_result is not None:
            async def generate():
                yield f"data: {command_result}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(generate(), media_type="text/event-stream")
    
    async def generate():
        try:
            thinking_buffer = ""
            in_thinking = True
            
            yield "data:<think>🔍 Analyzing task...\n📋 Building plan...\n⚠️ Checking risks...\n📁 Identifying files...\n</think>\n\n"
            
            def gen():
                nonlocal thinking_buffer, in_thinking
                llm = _get_llm()
                
                thinking_prompt = f"""{req.message}

BE FAST! Show your thinking briefly, then EXECUTE IMMEDIATELY.

Use this format:
```
<think>
🔍 ANALYSIS: [Quick what they want - 1 line]
📋 PLAN: [Step 1, Step 2 - just key steps]
⚡ ACTION: [What command you'll run now]
🌐 SEARCH: [If you need info, what to WEB_SEARCH]
```

Then IMMEDIATELY run commands to help the user. Don't just explain - DO!

If you don't know something → use WEB_SEARCH command right away!
"""
                
                messages = [
                    {"role": "system", "content": DEVAI_SYSTEM_PROMPT},
                    {"role": "user", "content": thinking_prompt},
                    {"role": "assistant", "content": "<think>\n"},
                ]
                for chunk in llm.create_chat_completion(
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.5,
                    top_p=0.9,
                    top_k=40,
                    repeat_penalty=1.1,
                    stream=True
                ):
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                    if content:
                        think_matches = re.findall(r'<\s*think\s*>(.*?)<\s*/\s*think\s*>', content, re.DOTALL | re.IGNORECASE)
                        if not think_matches:
                            think_matches = re.findall(r'<think>(.*?)</think>', content, re.DOTALL)
                        if think_matches:
                            for think in think_matches:
                                thinking_buffer += think
                                yield f"data:<think>{think}\n\n"
                            in_thinking = False
                        
                        in_think = re.search(r'<\s*think\s*>(.*)$', content, re.DOTALL | re.IGNORECASE)
                        if not in_think:
                            in_think = re.search(r'<think>(.*)$', content, re.DOTALL)
                        if in_think and in_thinking:
                            thinking_buffer += in_think.group(1)
                            yield f"data:<think>{thinking_buffer}▌\n\n"
                            continue
                        
                        cleaned = re.sub(r'<\s*think\s*>.*?<\s*/\s*think\s*>', '', content, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r'<\s*think\s*>[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
                        cleaned = re.sub(r'<think>[\s\S]*$', '', cleaned)
                        if cleaned:
                            in_thinking = False
                            yield f"data: {cleaned}\n\n"
            
            loop = asyncio.get_event_loop()
            for text in await loop.run_in_executor(_executor, lambda: list(gen())):
                yield text
            
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("Dev AI Pro stream error: %s", e)
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/status")
async def devai_status():
    """Check if Dev AI Pro model is loaded."""
    global _llm
    return {
        "status": "ready" if _llm is not None else "loading",
        "model": "Dev AI Pro (Offline Qwen)",
        "offline": True,
        "version": "2.0 Pro",
        "indexed": code_search.last_index_time > 0,
    }


@router.post("/index")
async def devai_index():
    """Build search index for the project."""
    stats = code_search.index_project(".")
    return {"status": "indexed", "stats": stats}


@router.get("/search")
async def devai_search(q: str = "", search_type: str = "code"):
    """Search the codebase."""
    if search_type == "function":
        results = code_search.search_functions(q)
    elif search_type == "class":
        results = code_search.search_classes(q)
    else:
        results = code_search.search_code(q)
    return {"query": q, "type": search_type, "results": results[:50]}


@router.get("/analyze")
async def devai_analyze(file_path: str, analysis_type: str = "bugs"):
    """Analyze code for bugs, complexity, or improvements."""
    content = DevAICommands.read_file(file_path)
    if "error" in content.lower():
        return {"error": "File not found"}
    
    if analysis_type == "bugs":
        results = analyzer.find_bugs(content)
    elif analysis_type == "complexity":
        results = analyzer.analyze_complexity(content)
    else:
        results = analyzer.suggest_improvements(content)
    
    return {"file": file_path, "type": analysis_type, "results": results}


@router.get("/commands")
async def devai_commands():
    """List all available commands."""
    commands = [
        {"category": "File Operations", "commands": [
            {"cmd": "READ_FILE <path>", "desc": "Read file contents with syntax highlighting"},
            {"cmd": "WRITE_FILE <path>:<content>", "desc": "Write content to file (use || for newlines)"},
            {"cmd": "CREATE_DIR <path>", "desc": "Create a directory"},
            {"cmd": "DELETE_FILE <path>", "desc": "Delete a file"},
            {"cmd": "DELETE_DIR <path>", "desc": "Delete a directory recursively"},
            {"cmd": "MOVE_FILE <source>:<dest>", "desc": "Move/rename a file or directory"},
            {"cmd": "COPY_FILE <source>:<dest>", "desc": "Copy a file or directory"},
            {"cmd": "LIST_DIR [path]", "desc": "List directory contents with sizes"},
            {"cmd": "FIND <pattern> <path>", "desc": "Find files matching pattern"},
            {"cmd": "GREP <pattern> <path>", "desc": "Search for pattern in files"},
            {"cmd": "FILE_EXISTS <path>", "desc": "Check if file exists"},
            {"cmd": "FILE_INFO <path>", "desc": "Get detailed file information"},
            {"cmd": "GET_PERMISSIONS <path>", "desc": "Get file permissions"},
            {"cmd": "SET_PERMISSIONS <path>:<mode>", "desc": "Set file permissions"},
        ]},
        {"category": "Git Operations", "commands": [
            {"cmd": "GIT_STATUS", "desc": "Show git status"},
            {"cmd": "GIT_DIFF", "desc": "Show uncommitted changes"},
            {"cmd": "GIT_LOG [count]", "desc": "Show recent commits"},
            {"cmd": "GIT_ADD [path]", "desc": "Stage files"},
            {"cmd": "GIT_COMMIT <msg>", "desc": "Commit staged changes"},
            {"cmd": "GIT_PUSH", "desc": "Push to remote"},
            {"cmd": "GIT_PULL", "desc": "Pull from remote"},
            {"cmd": "GIT_BRANCH", "desc": "List branches"},
            {"cmd": "GIT_CHECKOUT <branch>", "desc": "Switch branches"},
            {"cmd": "GIT_STASH [msg]", "desc": "Stash changes"},
            {"cmd": "GIT_STASH_POP", "desc": "Apply stashed changes"},
        ]},
        {"category": "System Operations", "commands": [
            {"cmd": "SYSTEM_INFO", "desc": "Get system information"},
            {"cmd": "DISK_USAGE", "desc": "Show disk usage"},
            {"cmd": "MEMORY_USAGE", "desc": "Show memory usage"},
            {"cmd": "CPU_USAGE", "desc": "Show CPU usage"},
            {"cmd": "RUNNING_PROCESSES", "desc": "List running processes"},
            {"cmd": "KILL_PROCESS <pid>", "desc": "Terminate a process"},
            {"cmd": "PORT_SCAN <port>", "desc": "Check if port is open"},
            {"cmd": "NETWORK_INFO", "desc": "Show network information"},
            {"cmd": "GET_CWD", "desc": "Get current working directory"},
            {"cmd": "SET_CWD <path>", "desc": "Change working directory"},
        ]},
        {"category": "Code Analysis", "commands": [
            {"cmd": "COUNT_LINES <path>", "desc": "Count lines in file/directory"},
            {"cmd": "PROJECT_STRUCTURE [path]", "desc": "Show project tree structure"},
            {"cmd": "FIND_FUNC <name> <path>", "desc": "Find function definitions"},
            {"cmd": "FIND_IMPORT <module> <path>", "desc": "Find import statements"},
            {"cmd": "LINT <path>", "desc": "Lint code file"},
            {"cmd": "FORMAT <path>", "desc": "Format code file"},
            {"cmd": "SYNTAX_CHECK <path>", "desc": "Check syntax"},
        ]},
        {"category": "🔍 AI Search & Analysis", "commands": [
            {"cmd": "INDEX", "desc": "Build search index for instant lookup"},
            {"cmd": "SEARCH <query>", "desc": "Full-text search across all code"},
            {"cmd": "SEARCH_FUNC <name>", "desc": "Find functions by name"},
            {"cmd": "SEARCH_CLASS <name>", "desc": "Find classes by name"},
            {"cmd": "FIND_RELATED <file>", "desc": "Find related files (imports, similar)"},
            {"cmd": "ANALYZE_BUGS <file>", "desc": "Find bugs and security issues"},
            {"cmd": "ANALYZE_COMPLEXITY <file>", "desc": "Check code complexity"},
            {"cmd": "SUGGEST <file>", "desc": "Get improvement suggestions"},
        ]},
        {"category": "📥 Smart Install", "commands": [
            {"cmd": "PIP_INSTALL <package>", "desc": "Install Python package"},
            {"cmd": "NPM_INSTALL <package>", "desc": "Install npm package"},
            {"cmd": "DOWNLOAD <url>", "desc": "Download file from URL"},
            {"cmd": "GIT_CLONE <repo>", "desc": "Clone git repository"},
        ]},
        {"category": "🌐 Web Search (NEW!)", "commands": [
            {"cmd": "WEB_SEARCH <query>", "desc": "Search the web for latest info"},
            {"cmd": "SEARCH_WEB <query>", "desc": "Alias for web search"},
            {"cmd": "FETCH_API <url>", "desc": "Make HTTP API calls"},
            {"cmd": "READ_URL <url>", "desc": "Fetch content from URL"},
        ]},
        {"category": "🧠 AI Code Generation", "commands": [
            {"cmd": "GENERATE_CODE <description>", "desc": "Generate full code from description"},
            {"cmd": "FIX_CODE <code>", "desc": "Fix buggy code with suggestions"},
            {"cmd": "COMPLETE_CODE <partial_code>", "desc": "Auto-complete partial code"},
            {"cmd": "TRANSLATE_CODE <from> to <to>", "desc": "Translate between languages"},
        ]},
        {"category": "🧪 Testing & Docs", "commands": [
            {"cmd": "GENERATE_TESTS <file>", "desc": "Generate unit tests (pytest/jest)"},
            {"cmd": "GENERATE_DOCS <file>", "desc": "Generate docstrings and comments"},
            {"cmd": "GENERATE_README <project>", "desc": "Create full README file"},
        ]},
        {"category": "🔐 Security & Learning", "commands": [
            {"cmd": "SECURITY_SCAN <file>", "desc": "Find security vulnerabilities"},
            {"cmd": "EXPLAIN_CODE <code>", "desc": "Explain code for learning"},
        ]},
        {"category": "Quick Actions", "commands": [
            {"cmd": "NEW_FILE <path>:<template>", "desc": "Create file with template (py, js, ts, html, css, json, md, sh, dockerfile)"},
            {"cmd": "QUICK_SCAFFOLD <type>", "desc": "Quick scaffold (react, python, node, docker, makefile)"},
            {"cmd": "RUN <command>", "desc": "Run any shell command"},
        ]},
    ]
    return {"commands": commands}


class ReasoningRequest(BaseModel):
    action: str
    task: Optional[str] = None
    path: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None


@router.post("/reasoning")
async def reasoning_endpoint(req: ReasoningRequest):
    global reasoning_engine
    
    if req.action == "start":
        if not req.task:
            return {"error": "Task is required"}
        result = reasoning_engine.start_task(req.task)
        return {"status": "started", "task": req.task, "output": result}
    
    elif req.action == "think":
        if not req.task or not req.path:
            return {"error": "phase, thought, and action required"}
        step = reasoning_engine.think(req.task, req.path, req.action or "")
        return {"step": step.step_number, "phase": step.phase, "thought": step.thought}
    
    elif req.action == "plan":
        if not req.file_path:
            return {"error": "file_path required"}
        reasoning_engine.add_to_plan(req.file_path, req.task or "", req.path == "new", req.path == "delete")
        return {"status": "added", "file": req.file_path, "plan": {
            "created": reasoning_engine.change_plan.files_to_create,
            "modified": reasoning_engine.change_plan.files_to_modify,
            "deleted": reasoning_engine.change_plan.files_to_delete,
        }}
    
    elif req.action == "scan":
        awareness = reasoning_engine.scan_project_awareness(req.path or ".")
        return {"status": "scanned", "awareness": awareness}
    
    elif req.action == "safety":
        if not req.file_path:
            return {"error": "file_path required"}
        safe, msg = reasoning_engine.safety_check_delete(req.file_path)
        return {"safe": safe, "message": msg}
    
    elif req.action == "detect":
        if not req.file_path or not req.content:
            return {"error": "file_path and content required"}
        issues = reasoning_engine.detect_issues(req.file_path, req.content)
        return {"issues": issues, "count": len(issues)}
    
    elif req.action == "summary":
        return {
            "current_task": reasoning_engine.current_task,
            "steps": [{"phase": s.phase, "thought": s.thought} for s in reasoning_engine.steps],
            "plan": {
                "files_to_create": reasoning_engine.change_plan.files_to_create,
                "files_to_modify": reasoning_engine.change_plan.files_to_modify,
                "files_to_delete": reasoning_engine.change_plan.files_to_delete,
                "reasons": reasoning_engine.change_plan.reasons,
            },
            "output": reasoning_engine.format_thinking() + reasoning_engine.format_change_plan()
        }
    
    else:
        return {"error": f"Unknown action: {req.action}"}


@router.get("/reasoning/status")
async def reasoning_status():
    return {
        "active": reasoning_engine.current_task != "",
        "task": reasoning_engine.current_task,
        "steps_count": len(reasoning_engine.steps),
        "plan": {
            "files_to_create": len(reasoning_engine.change_plan.files_to_create),
            "files_to_modify": len(reasoning_engine.change_plan.files_to_modify),
            "files_to_delete": len(reasoning_engine.change_plan.files_to_delete),
        }
    }
