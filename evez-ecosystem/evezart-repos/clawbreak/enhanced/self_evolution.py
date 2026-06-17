"""Self-evolution system: learns from interactions, auto-improves code, commits to GitHub."""
import os
import json
import subprocess
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SelfEvolutionSystem:
    def __init__(self, repo_path: str, github_token: str, owner: str = "EvezArt"):
        self.repo_path = Path(repo_path)
        self.github_token = github_token
        self.owner = owner
        self.evolution_log = self.repo_path / "data" / "evolution_log.json"
        self.learning_db = self.repo_path / "data" / "learning.db"
        
        # Ensure data directory exists
        self.repo_path.joinpath("data").mkdir(exist_ok=True)
        
        # Load evolution log
        if self.evolution_log.exists():
            with open(self.evolution_log, "r") as f:
                self.log = json.load(f)
        else:
            self.log = {
                "started_at": datetime.datetime.now().isoformat(),
                "improvements": [],
                "commits": [],
                "lessons_learned": [],
                "performance_metrics": {},
            }
        
        # Start background learning thread
        self.learning_thread = threading.Thread(target=self._background_learning, daemon=True)
        self.learning_thread.start()
    
    def record_interaction(self, interaction: Dict) -> str:
        """Record a successful interaction for learning."""
        interaction_id = hashlib.sha256(json.dumps(interaction, sort_keys=True).encode()).hexdigest()[:16]
        
        # Extract patterns
        patterns = self._extract_patterns(interaction)
        
        # Store in log
        self.log["improvements"].append({
            "id": interaction_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "interaction": interaction,
            "patterns": patterns,
        })
        
        # Save log
        self._save_log()
        
        return interaction_id
    
    def _extract_patterns(self, interaction: Dict) -> List[Dict]:
        """Extract reusable patterns from interaction."""
        patterns = []
        
        # Pattern: tool usage sequence
        if "tool_calls" in interaction:
            sequence = [call["tool"] for call in interaction["tool_calls"]]
            patterns.append({
                "type": "tool_sequence",
                "pattern": sequence,
                "context": interaction.get("context", ""),
            })
        
        # Pattern: successful code generation
        if "code_generated" in interaction:
            code = interaction["code_generated"]
            language = interaction.get("language", "python")
            patterns.append({
                "type": "code_snippet",
                "language": language,
                "snippet": code[:500],  # Truncate
                "purpose": interaction.get("purpose", ""),
            })
        
        # Pattern: problem-solving approach
        if "problem" in interaction and "solution" in interaction:
            patterns.append({
                "type": "problem_solution",
                "problem": interaction["problem"],
                "solution_approach": interaction["solution"],
            })
        
        return patterns
    
    def learn_from_github_commits(self, repo_name: str, limit: int = 50) -> List[Dict]:
        """Analyze recent GitHub commits for patterns."""
        try:
            # Fetch recent commits
            cmd = [
                "curl", "-s", "-H", f"Authorization: token {self.github_token}",
                f"https://api.github.com/repos/{self.owner}/{repo_name}/commits?per_page={limit}"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"GitHub API error: {result.stderr}")
                return []
            
            commits = json.loads(result.stdout)
            lessons = []
            
            for commit in commits:
                commit_data = {
                    "sha": commit["sha"][:8],
                    "author": commit["commit"]["author"]["name"],
                    "message": commit["commit"]["message"],
                    "date": commit["commit"]["author"]["date"],
                    "url": commit["html_url"],
                }
                
                # Extract commit message patterns
                message = commit_data["message"].lower()
                patterns = []
                
                if "fix" in message:
                    patterns.append("bug_fix")
                if "feat" in message or "feature" in message:
                    patterns.append("new_feature")
                if "refactor" in message:
                    patterns.append("refactoring")
                if "docs" in message:
                    patterns.append("documentation")
                if "test" in message:
                    patterns.append("testing")
                if "perf" in message:
                    patterns.append("performance")
                if "security" in message:
                    patterns.append("security")
                
                # Get commit details if available
                try:
                    cmd_details = [
                        "curl", "-s", "-H", f"Authorization: token {self.github_token}",
                        f"https://api.github.com/repos/{self.owner}/{repo_name}/commits/{commit['sha']}"
                    ]
                    details_result = subprocess.run(cmd_details, capture_output=True, text=True, timeout=10)
                    
                    if details_result.returncode == 0:
                        details = json.loads(details_result.stdout)
                        files_changed = [f["filename"] for f in details.get("files", [])]
                        commit_data["files_changed"] = files_changed
                        
                        # Analyze file patterns
                        for filename in files_changed:
                            if filename.endswith(".py"):
                                commit_data.setdefault("file_types", []).append("python")
                            elif filename.endswith(".js") or filename.endswith(".ts"):
                                commit_data.setdefault("file_types", []).append("javascript")
                            elif filename.endswith(".md"):
                                commit_data.setdefault("file_types", []).append("markdown")
                except Exception as e:
                    logger.warning(f"Couldn't get commit details: {str(e)}")
                
                lessons.append({
                    "commit": commit_data,
                    "patterns": patterns,
                    "timestamp": datetime.datetime.now().isoformat(),
                })
            
            # Store lessons learned
            self.log["lessons_learned"].extend(lessons)
            self._save_log()
            
            return lessons
            
        except Exception as e:
            logger.error(f"Error learning from GitHub: {str(e)}")
            return []
    
    def auto_improve_code(self, file_path: str, improvement_type: str = "refactor") -> bool:
        """Attempt to automatically improve code based on learned patterns."""
        try:
            full_path = self.repo_path / file_path
            if not full_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            original_content = full_path.read_text()
            
            # Apply improvements based on type
            improved_content = original_content
            
            if improvement_type == "refactor":
                # Simple refactoring patterns
                improved_content = self._apply_refactoring_patterns(improved_content)
            elif improvement_type == "optimize":
                improved_content = self._apply_optimization_patterns(improved_content)
            elif improvement_type == "security":
                improved_content = self._apply_security_patterns(improved_content)
            elif improvement_type == "documentation":
                improved_content = self._apply_documentation_patterns(improved_content)
            
            # Only write if changes were made
            if improved_content != original_content:
                backup_path = full_path.with_suffix(f"{full_path.suffix}.backup_{int(time.time())}")
                full_path.rename(backup_path)
                full_path.write_text(improved_content)
                
                # Record improvement
                improvement_id = hashlib.sha256(improved_content.encode()).hexdigest()[:16]
                self.log["improvements"].append({
                    "id": improvement_id,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": improvement_type,
                    "file": file_path,
                    "changes": len(improved_content) - len(original_content),
                    "backup": str(backup_path),
                })
                self._save_log()
                
                logger.info(f"Auto-improved {file_path} ({improvement_type})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Auto-improvement failed: {str(e)}")
            return False
    
    def _apply_refactoring_patterns(self, content: str) -> str:
        """Apply refactoring patterns to code."""
        lines = content.splitlines()
        improved_lines = []
        
        # Pattern: remove unused imports
        for line in lines:
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                # Keep it for now (would need AST analysis to know if used)
                improved_lines.append(line)
            else:
                improved_lines.append(line)
        
        # Pattern: replace double quotes with single quotes for consistency
        # (skip for now as it's style-dependent)
        
        return "\n".join(improved_lines)
    
    def _apply_optimization_patterns(self, content: str) -> str:
        """Apply optimization patterns."""
        improved = content
        
        # Pattern: replace list comprehension with generator for large datasets
        # This would require AST analysis
        
        # Pattern: add caching decorator for expensive pure functions
        lines = improved.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith("def ") and "(" in line and ")" in line:
                # Check if function looks pure (no side effects heuristic)
                func_name = line.split("def ")[1].split("(")[0].strip()
                # Would need to analyze function body
                # For now, just add a comment
                lines[i] = f"# Consider @lru_cache if {func_name} is pure and expensive\n{line}"
        
        return "\n".join(lines)
    
    def _apply_security_patterns(self, content: str) -> str:
        """Apply security improvement patterns."""
        improved = content
        
        # Pattern: replace hardcoded credentials with env vars
        patterns = [
            ("password = \"", "password = os.getenv(\""),
            ("api_key = \"", "api_key = os.getenv(\""),
            ("token = \"", "token = os.getenv(\""),
            ("secret = \"", "secret = os.getenv(\""),
        ]
        
        for old, new in patterns:
            improved = improved.replace(old, new)
        
        # Add import if not present
        if "import os" not in improved and "from os import" not in improved:
            lines = improved.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    lines.insert(i, "import os")
                    break
            else:
                lines.insert(0, "import os")
            improved = "\n".join(lines)
        
        return improved
    
    def _apply_documentation_patterns(self, content: str) -> str:
        """Apply documentation patterns."""
        lines = content.splitlines()
        improved_lines = []
        
        # Pattern: add docstrings to functions without them
        in_function = False
        function_name = ""
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith("def "):
                in_function = True
                function_name = stripped.split("def ")[1].split("(")[0].strip()
                improved_lines.append(line)
                
                # Check next line for docstring
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""') and not lines[i + 1].strip().startswith("'''"):
                    # Add docstring
                    improved_lines.append(f'    """{function_name}."""')
            elif in_function and stripped and not stripped.startswith(" ") and not stripped.startswith("#"):
                # End of function
                in_function = False
                improved_lines.append(line)
            else:
                improved_lines.append(line)
        
        return "\n".join(improved_lines)
    
    def auto_commit(self, message: str, files: Optional[List[str]] = None) -> bool:
        """Automatically commit changes to GitHub."""
        try:
            if files:
                # Stage specific files
                for file in files:
                    subprocess.run(["git", "add", file], cwd=self.repo_path, check=True)
            else:
                # Stage all changes
                subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
            
            # Commit
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_path, check=True)
            
            # Push
            result = subprocess.run(["git", "push"], cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Record commit
                self.log["commits"].append({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": message,
                    "files": files or ["all"],
                    "pushed": True,
                })
                self._save_log()
                return True
            else:
                logger.error(f"Push failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Auto-commit failed: {str(e)}")
            return False
    
    def _background_learning(self):
        """Background thread for continuous learning."""
        while True:
            try:
                # Learn from EVEZ repos
                repos = ["evez-os", "clawbreak", "evez-vcl", "disclosure.tools"]
                for repo in repos:
                    self.learn_from_github_commits(repo, limit=10)
                
                # Auto-improve based on learned patterns
                python_files = list(self.repo_path.rglob("*.py"))
                for py_file in python_files[:5]:  # Limit to 5 files per cycle
                    if "test" not in str(py_file) and "example" not in str(py_file):
                        rel_path = str(py_file.relative_to(self.repo_path))
                        self.auto_improve_code(rel_path, "refactor")
                
                # Sleep for an hour
                time.sleep(3600)
                
            except Exception as e:
                logger.error(f"Background learning error: {str(e)}")
                time.sleep(300)  # Shorter sleep on error
    
    def _save_log(self):
        """Save evolution log."""
        with open(self.evolution_log, "w") as f:
            json.dump(self.log, f, indent=2)
    
    def get_evolution_stats(self) -> Dict:
        """Get statistics on evolution progress."""
        return {
            "total_improvements": len(self.log.get("improvements", [])),
            "total_commits": len(self.log.get("commits", [])),
            "total_lessons": len(self.log.get("lessons_learned", [])),
            "last_improvement": self.log.get("improvements", [{}])[-1].get("timestamp") if self.log.get("improvements") else None,
            "last_commit": self.log.get("commits", [{}])[-1].get("timestamp") if self.log.get("commits") else None,
        }

# Singleton instance (requires GitHub token)
evolution_system = None
if os.getenv("GITHUB_TOKEN"):
    evolution_system = SelfEvolutionSystem(
        repo_path="/home/openclaw/.openclaw/workspace/repos/clawbreak",
        github_token=os.getenv("GITHUB_TOKEN"),
        owner="EvezArt"
    )