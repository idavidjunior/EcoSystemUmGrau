import os
import json
import re
import sys
import hashlib
import subprocess
from datetime import datetime
from collections import Counter


SIMILARITY_THRESHOLD = 0.55  # Jaccard threshold to consider two entries mergeable


def _tokenize(text):
    """Split text into lowercase word tokens for similarity comparison.
    Normalizes non-alphanumeric chars to spaces so 'test_action' -> ['test', 'action']."""
    text = re.sub(r'[^a-z0-9\s]', ' ', str(text).lower())
    return set(re.findall(r'\b[a-z0-9]{3,}\b', text))


def _jaccard_sim(a, b):
    """Jaccard similarity between two token sets."""
    tokens_a = _tokenize(str(a))
    tokens_b = _tokenize(str(b))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _merge_patterns(existing, new):
    """Merge two pattern entries, keeping the best of both."""
    merged = dict(existing)
    for key in new:
        if key == "extracted_at":
            merged[key] = new[key]  # keep newest
        elif key == "source":
            merged[key] = f"{existing.get(key, '')}+{new.get(key, '')}"
        elif key == "description":
            existing_desc = existing.get(key, "")
            new_desc = new.get(key, "")
            if new_desc and new_desc not in existing_desc:
                merged[key] = existing_desc + "; " + new_desc if existing_desc else new_desc
        else:
            # For other fields, prefer the new value if existing is empty
            if not existing.get(key):
                merged[key] = new[key]
    merged["merged_count"] = existing.get("merged_count", 1) + 1
    merged["merged_at"] = datetime.now().isoformat()
    return merged


def _merge_decisions(existing, new):
    """Merge two decision entries, combining rationales."""
    merged = dict(existing)
    for key in new:
        if key == "extracted_at":
            merged[key] = new[key]
        elif key == "rationale":
            existing_r = existing.get(key, "")
            new_r = new.get(key, "")
            if new_r and new_r != existing_r:
                merged[key] = f"{existing_r} // {new_r}" if existing_r else new_r
        elif not existing.get(key):
            merged[key] = new[key]
    merged["merged_count"] = existing.get("merged_count", 1) + 1
    merged["merged_at"] = datetime.now().isoformat()
    return merged


def _merge_bug_fixes(existing, new):
    """Merge two bug fix entries, keeping longest descriptions."""
    merged = dict(existing)
    for key in new:
        if key == "extracted_at":
            merged[key] = new[key]
        elif key in ("root_cause", "fix", "issue"):
            existing_v = existing.get(key, "")
            new_v = new.get(key, "")
            if len(new_v) > len(existing_v):
                merged[key] = new_v
        elif not existing.get(key):
            merged[key] = new[key]
    merged["merged_count"] = existing.get("merged_count", 1) + 1
    merged["merged_at"] = datetime.now().isoformat()
    return merged


def _merge_cognitive(existing, new):
    """Merge two cognitive pattern entries."""
    merged = dict(existing)
    for key in new:
        if key == "extracted_at":
            merged[key] = new[key]
        elif key in ("body", "description"):
            existing_v = existing.get(key, "")
            new_v = new.get(key, "")
            if new_v and new_v not in existing_v:
                merged[key] = existing_v + "\n\n" + new_v if existing_v else new_v
        elif not existing.get(key):
            merged[key] = new[key]
    merged["merged_count"] = existing.get("merged_count", 1) + 1
    merged["merged_at"] = datetime.now().isoformat()
    return merged


class KnowledgeConsolidator:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.knowledge_dir = os.path.join(base_dir, "knowledge")
        self.memory_dir = os.path.join(base_dir, "memory")
        self.skills_dir = os.path.join(
            os.environ.get("USERPROFILE", ""),
            ".claude", "skills"
        )
        os.makedirs(self.knowledge_dir, exist_ok=True)
        self.graph_path = os.path.join(self.knowledge_dir, "knowledge_graph.json")
        self.graph = self._load_graph()

    def _load_graph(self):
        default = {
            "version": 2,
            "last_updated": None,
            "projects": {},
            "patterns": [],
            "decisions": [],
            "bug_fixes": [],
            "cognitive_patterns": [],
            "heuristics": [],
            "frameworks": [],
            "tool_knowledge": {},
            "skill_references": [],
            "mission_learnings": [],
        }
        if os.path.exists(self.graph_path):
            try:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    g = json.load(f)
                return self._upgrade_schema(g, default)
            except Exception:
                pass
        return dict(default)

    @staticmethod
    def _upgrade_schema(g, default):
        """Migrate old schema versions to latest in-place."""
        if not g or not isinstance(g, dict):
            return dict(default)
        ver = g.get("version", 1)
        if ver >= 2:
            return g
        # Upgrade from v1 to v2: add missing sections
        for key in default:
            if key not in g:
                g[key] = default[key]
        g["version"] = 2
        return g

    def _save_graph(self):
        self.graph["last_updated"] = datetime.now().isoformat()
        tmp = self.graph_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.graph, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.graph_path)
        except Exception as e:
            print(f"[KnowledgeConsolidator] Erro ao salvar grafo: {e}")

    def _hash_file(self, path):
        try:
            h = hashlib.md5()
            with open(path, "rb") as f:
                h.update(f.read())
            return h.hexdigest()
        except Exception:
            return None

    def _read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    # ─── Extraction ─────────────────────────────────────────────────

    def seed_from_skills(self):
        skills_dir = self.skills_dir
        if not os.path.isdir(skills_dir):
            return
        for skill_name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
            alt_path = os.path.join(skills_dir, skill_name, "skill.md")
            path = skill_path if os.path.exists(skill_path) else alt_path
            if not os.path.exists(path):
                continue
            content = self._read_file(path)
            if not content:
                continue
            if skill_name not in self.graph["projects"]:
                self.graph["projects"][skill_name] = {}
            ref = {
                "skill": skill_name,
                "path": path,
                "hash": self._hash_file(path),
                "last_extracted": datetime.now().isoformat(),
            }
            # Extract key sections from the skill markdown
            patterns = self._extract_patterns_from_md(content, skill_name)
            decisions = self._extract_decisions_from_md(content, skill_name)
            bugs = self._extract_bug_fixes_from_md(content, skill_name)

            existing = [r for r in self.graph["skill_references"]
                        if r["skill"] == skill_name]
            if existing:
                for e in existing:
                    e["hash"] = ref["hash"]
                    e["last_extracted"] = ref["last_extracted"]
            else:
                self.graph["skill_references"].append(ref)

            for p in patterns:
                if p not in self.graph["patterns"]:
                    self.graph["patterns"].append(p)
            for d in decisions:
                if d not in self.graph["decisions"]:
                    self.graph["decisions"].append(d)
            for b in bugs:
                if b not in self.graph["bug_fixes"]:
                    self.graph["bug_fixes"].append(b)

    def _extract_patterns_from_md(self, content, source):
        patterns = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Pattern: markdown headings + known code blocks
            if stripped.startswith("### ") or stripped.startswith("## "):
                title = stripped.lstrip("#").strip()
                if any(kw in title.lower() for kw in
                       ["pattern", "approach", "technique", "strategy",
                        "design", "pipeline", "workflow", "idiom"]):
                    patterns.append({
                        "source": source,
                        "title": title,
                        "line": i + 1,
                        "extracted_at": datetime.now().isoformat(),
                    })
        return patterns

    def _extract_decisions_from_md(self, content, source):
        decisions = []
        # Look for decision-like patterns
        for match in re.finditer(
            r"(?:Decisão|Decision|Key Design|Motivo|Why|Razão)\s*[:\-].*?(?:\n|$)",
            content, re.IGNORECASE
        ):
            line_num = content[:match.start()].count("\n") + 1
            decisions.append({
                "source": source,
                "decision": match.group().strip()[:200],
                "line": line_num,
                "extracted_at": datetime.now().isoformat(),
            })
        # Also extract "KEY_DECISION" or numbered decisions
        for match in re.finditer(
            r"^\d+\.\s+(.+)",
            content, re.MULTILINE
        ):
            text = match.group(1).strip()
            if any(kw in text.lower() for kw in
                   ["use", "prefer", "never", "always", "must", "should",
                    "avoid", "recommend", "requir"]):
                line_num = content[:match.start()].count("\n") + 1
                decisions.append({
                    "source": source,
                    "decision": text[:200],
                    "line": line_num,
                    "extracted_at": datetime.now().isoformat(),
                })
        return decisions

    def _extract_bug_fixes_from_md(self, content, source):
        fixes = []
        # Known Issues & Fixes tables
        in_table = False
        for match in re.finditer(
            r"\|.*\|.*\|.*\|",
            content
        ):
            text = match.group()
            if "Issue" in text and "Root Cause" in text:
                in_table = True
                continue
            if in_table and text.count("|") >= 3:
                parts = [p.strip() for p in text.split("|")[1:-1]]
                if len(parts) >= 3:
                    line_num = content[:match.start()].count("\n") + 1
                    fixes.append({
                        "source": source,
                        "issue": parts[0][:100],
                        "root_cause": parts[1][:200],
                        "fix": parts[2][:200],
                        "line": line_num,
                        "extracted_at": datetime.now().isoformat(),
                    })
            else:
                in_table = False
        # Also look for numbered fix descriptions
        for match in re.finditer(
            r"(?:Fix|Bug|Corrigido|Issue|Erro)\s*[:\-]\s*(.+?)(?:\n|$)",
            content, re.IGNORECASE
        ):
            text = match.group(1).strip()
            if len(text) > 20:
                line_num = content[:match.start()].count("\n") + 1
                fixes.append({
                    "source": source,
                    "issue": text[:100],
                    "root_cause": "",
                    "fix": "",
                    "line": line_num,
                    "extracted_at": datetime.now().isoformat(),
                })
        return fixes

    def seed_from_ler_memory(self):
        memory_dir = self.memory_dir
        if not os.path.isdir(memory_dir):
            return
        # Learned rules
        rules_path = os.path.join(memory_dir, "learned_rules.json")
        if os.path.exists(rules_path):
            try:
                with open(rules_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                self.graph["tool_knowledge"]["learned_rules"] = rules
            except Exception:
                pass
        # Successful patterns
        patterns_path = os.path.join(memory_dir, "successful_patterns.json")
        if os.path.exists(patterns_path):
            try:
                with open(patterns_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p in data.get("patterns", []):
                        entry = {
                            "source": "ler_memory",
                            "action": p.get("action"),
                            "description": p.get("description", "")[:150],
                            "duration": p.get("duration"),
                            "timestamp": p.get("timestamp"),
                        }
                        if entry not in self.graph["patterns"]:
                            self.graph["patterns"].append(entry)
            except Exception:
                pass
        # Failed patterns
        failed_path = os.path.join(memory_dir, "failed_patterns.json")
        if os.path.exists(failed_path):
            try:
                with open(failed_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for p in data.get("patterns", []):
                        entry = {
                            "source": "ler_memory",
                            "action": p.get("action"),
                            "description": p.get("description", "")[:150],
                        }
                        if entry not in self.graph["patterns"]:
                            self.graph["patterns"].append(entry)
            except Exception:
                pass
        # Tool statistics
        tools_path = os.path.join(memory_dir, "tool_statistics.json")
        if os.path.exists(tools_path):
            try:
                with open(tools_path, "r", encoding="utf-8") as f:
                    stats = json.load(f)
                self.graph["tool_knowledge"]["tool_statistics"] = stats
            except Exception:
                pass

    def seed_from_git_log(self, repo_path=None):
        if repo_path is None:
            repo_path = os.getcwd()
        try:
            proc = subprocess.run(
                "git log --oneline -50 --format='%h|%s|%ci'",
                shell=True, capture_output=True, text=True, timeout=15,
                cwd=repo_path,
            )
            if proc.returncode != 0:
                return
            for line in proc.stdout.strip().split("\n"):
                parts = line.split("|")
                if len(parts) >= 2:
                    self.graph["mission_learnings"].append({
                        "source": f"git:{repo_path}",
                        "commit": parts[0],
                        "message": parts[1][:150],
                        "timestamp": parts[2] if len(parts) > 2 else "",
                    })
        except Exception:
            pass

    # ─── Consolidation ──────────────────────────────────────────────

    def consolidate(self):
        self.seed_from_skills()
        self.seed_from_ler_memory()
        self._smart_merge_all()
        self._save_graph()
        all_keys = {
            "patterns": len(self.graph["patterns"]),
            "decisions": len(self.graph["decisions"]),
            "bug_fixes": len(self.graph["bug_fixes"]),
            "cognitive_patterns": len(self.graph["cognitive_patterns"]),
            "heuristics": len(self.graph["heuristics"]),
            "frameworks": len(self.graph["frameworks"]),
            "projects": len(self.graph["projects"]),
            "skills": len(self.graph["skill_references"]),
            "missions": len(self.graph["mission_learnings"]),
        }
        return all_keys

    def _smart_merge_all(self):
        """Smart merging that detects similar entries and merges instead of just deduplicating."""
        # Patterns
        self.graph["patterns"] = self._smart_merge_list(
            self.graph["patterns"], _merge_patterns,
            ["title", "action", "description"],
        )
        # Decisions
        self.graph["decisions"] = self._smart_merge_list(
            self.graph["decisions"], _merge_decisions,
            ["decision"],
        )
        # Bug fixes
        self.graph["bug_fixes"] = self._smart_merge_list(
            self.graph["bug_fixes"], _merge_bug_fixes,
            ["issue"],
        )
        # Cognitive patterns
        self.graph["cognitive_patterns"] = self._smart_merge_list(
            self.graph["cognitive_patterns"], _merge_cognitive,
            ["title", "domain"],
        )
        # Heuristics
        self.graph["heuristics"] = self._smart_merge_list(
            self.graph["heuristics"], _merge_cognitive,
            ["title", "description"],
        )
        # Frameworks
        self.graph["frameworks"] = self._smart_merge_list(
            self.graph["frameworks"], _merge_cognitive,
            ["name", "description"],
        )

    def _smart_merge_list(self, items, merge_func, compare_keys):
        """Merge similar items in a list using Jaccard similarity on compare_keys."""
        if not items:
            return []
        merged = []
        merged_indices = set()
        for i, item in enumerate(items):
            if i in merged_indices:
                continue
            current = dict(item)
            for j in range(i + 1, len(items)):
                if j in merged_indices:
                    continue
                other = items[j]
                # Compute similarity on compare keys
                sims = []
                for key in compare_keys:
                    a = current.get(key, "")
                    b = other.get(key, "")
                    if a and b:
                        sims.append(_jaccard_sim(a, b))
                avg_sim = sum(sims) / len(sims) if sims else 0.0
                if avg_sim >= SIMILARITY_THRESHOLD:
                    current = merge_func(current, other)
                    merged_indices.add(j)
            merged.append(current)
        return merged

    # ─── Auto-Learning ─────────────────────────────────────────────

    def auto_learn(self, mission_report):
        if not mission_report:
            return
        status = mission_report.get("status", "unknown")
        learning = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "iterations": mission_report.get("iterations", 0),
            "steps_completed": mission_report.get("steps_completed", 0),
            "steps_total": mission_report.get("steps_total", 0),
            "learning_stats": mission_report.get("learning", {}),
            "goal_objective": mission_report.get("goal_objective", ""),
        }
        self.graph["mission_learnings"].append(learning)

        if status == "completed":
            goal = mission_report.get("goal_objective", "")
            pattern_entry = {
                "source": "auto_learn",
                "action": "mission_completed",
                "description": goal[:200],
                "iterations": mission_report.get("iterations", 0),
                "timestamp": datetime.now().isoformat(),
            }
            self.graph["patterns"].append(pattern_entry)
        elif status == "failed":
            goal = mission_report.get("goal_objective", "")
            failed_entry = {
                "source": "auto_learn",
                "action": "mission_failed",
                "description": goal[:200],
                "iterations": mission_report.get("iterations", 0),
                "timestamp": datetime.now().isoformat(),
            }
            self.graph["patterns"].append(failed_entry)

        self._smart_merge_all()
        self._save_graph()

    def consolidate_from_session(self, learnings):
        """
        Called at end of every AI session to persist learnings into the knowledge base.

        Accepts a dict with:
            patterns: list of {"title", "action", "description", "source", "domain"}
            decisions: list of {"decision", "rationale", "source"}
            bug_fixes: list of {"issue", "root_cause", "fix", "source"}
            cognitive_patterns: list of {"title", "domain", "body"}
            heuristics: list of {"title", "description", "domain"}
            frameworks: list of {"name", "description", "body"}
            session_summary: str (free text summary of what happened)
            files_modified: list of file paths
            tags: list of tags/keywords
        """
        if not learnings:
            return

        ts = datetime.now().isoformat()

        # Add patterns
        for p in learnings.get("patterns", []):
            entry = {
                "source": p.get("source", "session"),
                "title": p.get("title", ""),
                "action": p.get("action", ""),
                "description": p.get("description", ""),
                "domain": p.get("domain", "general"),
                "extracted_at": ts,
            }
            self.graph["patterns"].append(entry)

        # Add decisions
        for d in learnings.get("decisions", []):
            entry = {
                "source": d.get("source", "session"),
                "decision": d.get("decision", ""),
                "rationale": d.get("rationale", ""),
                "extracted_at": ts,
            }
            self.graph["decisions"].append(entry)

        # Add bug fixes
        for b in learnings.get("bug_fixes", []):
            entry = {
                "source": b.get("source", "session"),
                "issue": b.get("issue", ""),
                "root_cause": b.get("root_cause", ""),
                "fix": b.get("fix", ""),
                "extracted_at": ts,
            }
            self.graph["bug_fixes"].append(entry)

        # Add cognitive patterns
        for c in learnings.get("cognitive_patterns", []):
            entry = {
                "source": c.get("source", "session"),
                "title": c.get("title", ""),
                "domain": c.get("domain", "general"),
                "body": c.get("body", ""),
                "extracted_at": ts,
            }
            self.graph["cognitive_patterns"].append(entry)

        # Add heuristics
        for h in learnings.get("heuristics", []):
            entry = {
                "source": h.get("source", "session"),
                "title": h.get("title", ""),
                "description": h.get("description", ""),
                "domain": h.get("domain", "general"),
                "extracted_at": ts,
            }
            self.graph["heuristics"].append(entry)

        # Add frameworks
        for fw in learnings.get("frameworks", []):
            entry = {
                "source": fw.get("source", "session"),
                "name": fw.get("name", ""),
                "description": fw.get("description", ""),
                "body": fw.get("body", ""),
                "extracted_at": ts,
            }
            self.graph["frameworks"].append(entry)

        # Session summary
        summary = learnings.get("session_summary")
        if summary:
            self.graph["mission_learnings"].append({
                "timestamp": ts,
                "status": "session_learning",
                "goal_objective": summary[:500],
                "tags": learnings.get("tags", []),
                "files_modified": learnings.get("files_modified", []),
            })

        self._smart_merge_all()
        self._save_graph()

    def extract_from_text(self, text, source="text_extraction"):
        """
        Extract potential patterns, decisions, and heuristics from raw text.
        Uses pattern matching to find structured knowledge in free text.
        """
        if not text:
            return
        ts = datetime.now().isoformat()

        # Extract numbered rules/heuristics: "1. ..."
        for match in re.finditer(r'(?:^|\n)\s*(\d+)[.)]\s+(.{30,300})(?:\n|$)', text):
            content = match.group(2).strip()
            if any(kw in content.lower() for kw in
                   ["always", "never", "must", "should", "avoid", "prefer",
                    "use", "recommend", "require", "remember"]):
                self.graph["heuristics"].append({
                    "source": source,
                    "title": content[:60],
                    "description": content[:200],
                    "domain": "general",
                    "extracted_at": ts,
                })

        # Extract "key insight" / "lesson learned" blocks
        for match in re.finditer(
            r'(?:Key Insight|Lesson|Insight|Aprendizado|Licao|Observacao|Nota)\s*[:\-]\s*(.{30,500})',
            text, re.IGNORECASE
        ):
            content = match.group(1).strip()
            self.graph["cognitive_patterns"].append({
                "source": source,
                "title": content[:60],
                "domain": "general",
                "body": content[:500],
                "extracted_at": ts,
            })

        # Extract "framework" patterns
        for match in re.finditer(
            r'(?:Framework|Metodologia|Approach|Padrao|Pattern)\s*[:\-]\s*(.{30,300})',
            text, re.IGNORECASE
        ):
            content = match.group(1).strip()
            self.graph["frameworks"].append({
                "source": source,
                "name": content[:60],
                "description": content[:300],
                "body": content[:300],
                "extracted_at": ts,
            })

        self._smart_merge_all()
        self._save_graph()

    # ─── Skill Auto-Update ──────────────────────────────────────────

    def update_skill_file(self, skill_name, new_entries):
        skills_dir = self.skills_dir
        skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
        alt_path = os.path.join(skills_dir, skill_name, "skill.md")
        path = skill_path if os.path.exists(skill_path) else alt_path
        if not os.path.exists(path):
            return
        content = self._read_file(path)
        if content is None:
            return
        new_section = "\n".join(new_entries)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        header = f"\n## Auto-Learned ({timestamp})\n\n"
        if "## Auto-Learned" in content:
            existing_section = re.search(
                r"## Auto-Learned.*?(?=\n## |\Z)", content, re.DOTALL
            )
            if existing_section:
                before = content[:existing_section.start()]
                after = content[existing_section.end():]
                content = before + f"## Auto-Learned ({timestamp})\n\n{new_section}\n" + after
        else:
            content += header + new_section + "\n"
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp, path)
            self.graph["skill_references"].append({
                "skill": skill_name,
                "action": "auto_update",
                "entries": len(new_entries),
                "timestamp": timestamp,
            })
            self._save_graph()
        except Exception as e:
            print(f"[KnowledgeConsolidator] Erro ao atualizar skill {skill_name}: {e}")

    # ─── Markdown Export ──────────────────────────────────────────────

    def export_to_markdown(self, output_path=None):
        """Export knowledge graph as CONHECIMENTO.md (full portable format)."""
        g = self.graph
        if output_path is None:
            output_path = os.path.join(self.base_dir, "CONHECIMENTO.md")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        lines = [f"# Base de Conhecimento — Exportacao Completa\n"]
        lines.append(f"**Exportado em:** {datetime.now().isoformat()}")
        lines.append(f"**Projetos:** {len(g.get('projects', {}))}")
        lines.append(f"**Padroes Tecnicos:** {len(g.get('patterns', []))}")
        lines.append(f"**Decisoes:** {len(g.get('decisions', []))}")
        lines.append(f"**Bug Fixes:** {len(g.get('bug_fixes', []))}")
        lines.append(f"**Padroes Cognitivos:** {len(g.get('cognitive_patterns', []))}")
        lines.append(f"**Heuristicas:** {len(g.get('heuristics', []))}")
        lines.append(f"**Frameworks:** {len(g.get('frameworks', []))}")
        lines.append(f"**Missoes Aprendidas:** {len(g.get('mission_learnings', []))}\n")
        lines.append("---\n")
        lines.append("## Como Usar Esta Base de Conhecimento\n")
        lines.append("Esta base contem **conhecimento cognitivo e tecnico** acumulado entre projetos.")
        lines.append("Ela e organizada em 3 niveis:\n")
        lines.append("1. **Conhecimento Tecnico** — Padroes de codigo, pipelines de build, decisoes arquiteturais, bug fixes")
        lines.append("2. **Conhecimento Cognitivo** — Heuristicas de debugging, frameworks de raciocinio, estrategias validadas")
        lines.append("3. **Meta-Conhecimento** — Como a propria base e estruturada e auto-melhorada\n")
        lines.append("---\n")

        # Decisions
        if g.get("decisions"):
            lines.append("## Decisoes Arquiteturais\n")
            for d in g["decisions"]:
                src = d.get("source", "?")
                dec = d.get("decision", "")
                rat = d.get("rationale", "")
                if rat:
                    lines.append(f"### {dec[:120]}")
                    lines.append(f"**Fonte:** {src}")
                    lines.append(f"{rat[:500]}\n")
                else:
                    lines.append(f"- **{dec[:120]}** (fonte: {src})")
            lines.append("")

        # Patterns
        if g.get("patterns"):
            lines.append("## Padroes Tecnicos\n")
            lines.append("| # | Fonte | Titulo |")
            lines.append("|---|-------|--------|")
            for i, p in enumerate(g["patterns"], 1):
                src = p.get("source", "?")
                title = p.get("title", "") or p.get("action", "")
                lines.append(f"| {i} | {src} | {title[:120]} |")
            lines.append("")

        # Bug fixes
        if g.get("bug_fixes"):
            lines.append("## Bug Fixes e Corrigidos\n")
            for b in g["bug_fixes"]:
                src = b.get("source", "?")
                issue = b.get("issue", "")
                rc = b.get("root_cause", "")
                fix = b.get("fix", "")
                lines.append(f"### {issue[:120]}")
                lines.append(f"**Fonte:** {src}")
                if rc:
                    lines.append(f"**Causa Raiz:** {rc[:300]}")
                if fix:
                    lines.append(f"**Correcao:** {fix[:300]}")
                lines.append("")

        # Cognitive patterns
        if g.get("cognitive_patterns"):
            lines.append("## Padroes Cognitivos\n")
            for c in g["cognitive_patterns"]:
                domain = c.get("domain", "general")
                title = c.get("title", "")
                body = c.get("body", "")
                lines.append(f"### {title}")
                lines.append(f"**Dominio:** {domain}")
                lines.append(f"**Fonte:** {c.get('source', '?')}")
                if body:
                    lines.append(f"\n{body[:500]}\n")

        # Heuristics
        if g.get("heuristics"):
            lines.append("## Heuristicas\n")
            lines.append("| # | Dominio | Titulo | Descricao |")
            lines.append("|---|--------|--------|-----------|")
            for i, h in enumerate(g["heuristics"], 1):
                d = h.get("domain", "general")
                t = h.get("title", "")
                desc = h.get("description", "")[:180]
                lines.append(f"| {i} | {d} | {t} | {desc} |")
            lines.append("")

        # Frameworks
        if g.get("frameworks"):
            lines.append("## Frameworks\n")
            for fw in g["frameworks"]:
                name = fw.get("name", "")
                src = fw.get("source", "?")
                desc = fw.get("description", "")
                lines.append(f"### {name}")
                lines.append(f"**Fonte:** {src}")
                if desc:
                    lines.append(f"\n{desc[:400]}\n")

        # Meta
        lines.append("---\n")
        lines.append("## Meta-Informacao\n")
        lines.append(f"**Versao do grafo:** {g.get('version', 2)}")
        lines.append(f"**Ultima atualizacao:** {g.get('last_updated', 'N/A')}")
        lines.append("**Proposito:** Base de conhecimento universal e auto-melhoravel para engenharia de software")
        lines.append("\n*Fim da exportacao. Este arquivo MARKDOWN pode ser fornecido como contexto para QUALQUER IA.*")

        text = "\n".join(lines) + "\n"
        tmp = output_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, output_path)
        except Exception as e:
            print(f"[KnowledgeConsolidator] Erro ao exportar markdown: {e}")

    # ─── OpenCode Integration ─────────────────────────────────────────

    def register_learning_file(self, md_path):
        """Parse a markdown entry from conhecimento/aprendizados/ and consolidate it."""
        import re as _re
        path = str(md_path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception:
            return
        lines = text.splitlines()
        if not lines:
            return

        title = lines[0].lstrip("# ").strip()
        meta = {}
        # suporta frontmatter YAML (---\ntipo: decisao\n...) e formato markdown
        # (**tipo:** valor) — aprendizados modernos usam YAML.
        in_yaml = False
        for line in lines:
            if line.strip() == "---":
                in_yaml = not in_yaml
                continue
            m = _re.match(r"^\*\*(\w+):\*\*\s*(.+)", line)
            if m:
                meta[m.group(1).lower()] = m.group(2).strip()
                continue
            if in_yaml:
                ym = _re.match(r"^([\w\s]+):\s*(.*)", line)
                if ym:
                    key = ym.group(1).strip().lower().replace(" ", "-")
                    meta[key] = ym.group(2).strip()
        # titulo real: primeiro H1 (# ...) fora do frontmatter YAML
        for line in lines:
            if line.startswith("# ") and not line.startswith("##"):
                title = line.lstrip("# ").strip()
                break

        # mapeia campos YAML para os esperados
        if "categoria" not in meta and "tipo" in meta:
            meta["categoria"] = meta["tipo"]
        if "contexto" not in meta:
            meta["contexto"] = meta.get("decisao", meta.get("impacto", ""))

        cat = meta.get("categoria", "geral")
        context = meta.get("contexto", "")
        source = meta.get("agentes envolvidos", "opencode")

        # Tags semanticas: extrai conceitos do titulo + contexto + corpo
        # (RAKE leve, local/deterministico) e combina com categoria.
        tags_semanticas = []
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
            from semantic_tags import extrair_tags
            tags_semanticas = extrair_tags(f"{title} {context} {text[:300]}", max_tags=6)
        except Exception:
            tags_semanticas = []

        learning = {
            "session_summary": f"{title} — {context}",
            "tags": [cat, "opencode"] + tags_semanticas,
            "patterns": [],
            "decisions": [],
            "bug_fixes": [],
            "cognitive_patterns": [],
            "heuristics": [],
            "frameworks": [],
        }

        ts = datetime.now().isoformat()

        if cat in ("decisao", "decisão"):
            learning["decisions"].append({
                "source": source,
                "decision": title,
                "rationale": text,
                "extracted_at": ts,
            })
        elif cat == "padrao":
            learning["patterns"].append({
                "source": source,
                "title": title,
                "action": context,
                "description": text[:300],
                "domain": "general",
                "extracted_at": ts,
            })
        elif cat == "bug":
            learning["bug_fixes"].append({
                "source": source,
                "issue": title,
                "root_cause": context,
                "fix": text[:500],
                "extracted_at": ts,
            })
        elif cat == "config":
            learning["patterns"].append({
                "source": source,
                "title": f"Config: {title}",
                "action": context,
                "description": text[:300],
                "domain": "config",
                "extracted_at": ts,
            })
        elif cat == "risco":
            learning["heuristics"].append({
                "source": source,
                "title": f"Risk: {title}",
                "description": text[:300],
                "domain": "risk",
                "extracted_at": ts,
            })
        else:
            learning["cognitive_patterns"].append({
                "source": source,
                "title": title,
                "domain": "general",
                "body": text[:500],
                "extracted_at": ts,
            })

        self.consolidate_from_session(learning)
        self._save_graph()
        self.export_to_markdown()

    # ─── Report ─────────────────────────────────────────────────────

    def generate_report(self):
        self._save_graph()
        g = self.graph
        lines = []
        lines.append("=" * 60)
        lines.append("KNOWLEDGE CONSOLIDATOR - RELATORIO")
        lines.append("=" * 60)
        lines.append(f"Ultima atualizacao: {g.get('last_updated', 'N/A')}")
        lines.append(f"Projetos/Skills:    {len(g['projects'])}")
        lines.append(f"Padroes tecnicos:   {len(g['patterns'])}")
        lines.append(f"Decisoes arquiteturais: {len(g['decisions'])}")
        lines.append(f"Bug Fixes:          {len(g['bug_fixes'])}")
        lines.append(f"Padroes cognitivos: {len(g['cognitive_patterns'])}")
        lines.append(f"Heuristicas:        {len(g['heuristics'])}")
        lines.append(f"Frameworks:         {len(g['frameworks'])}")
        lines.append(f"Missoes aprendidas: {len(g['mission_learnings'])}")
        lines.append(f"Skills referenciados: {len(g['skill_references'])}")
        lines.append("-" * 60)
        if g["cognitive_patterns"]:
            lines.append("PADROES COGNITIVOS:")
            for c in g["cognitive_patterns"][-3:]:
                lines.append(f"  [{c.get('domain','?')}] {c.get('title','')[:80]}")
        if g["heuristics"]:
            lines.append("HEURISTICAS:")
            for h in g["heuristics"][-3:]:
                lines.append(f"  [{h.get('domain','?')}] {h.get('title','')[:80]}")
        if g["frameworks"]:
            lines.append("FRAMEWORKS:")
            for fw in g["frameworks"][-3:]:
                lines.append(f"  [{fw.get('source','?')}] {fw.get('name','')[:80]}")
        if g["patterns"]:
            lines.append("ULTIMOS PADROES TECNICOS:")
            for p in g["patterns"][-3:]:
                src = p.get("source", "?")
                action = p.get("action", p.get("title", "?"))
                lines.append(f"  [{src}] {action[:80]}")
        if g["bug_fixes"]:
            lines.append("ULTIMOS BUG FIXES:")
            for b in g["bug_fixes"][-3:]:
                lines.append(f"  [{b.get('source','?')}] {b.get('issue','')[:80]}")
        lines.append("=" * 60)
        return "\n".join(lines)


def consolidate(base_dir):
    kc = KnowledgeConsolidator(base_dir)
    stats = kc.consolidate()
    report = kc.generate_report()
    print(report)
    return stats


def consolidate_from_session(base_dir, learnings):
    """Convenience function: end-of-session consolidation."""
    kc = KnowledgeConsolidator(base_dir)
    kc.consolidate_from_session(learnings)
    return kc.graph


def register_learning(md_path):
    """Convenience function: register a single markdown learning entry."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kc = KnowledgeConsolidator(base_dir)
    kc.register_learning_file(md_path)
    return kc.graph


def export_markdown(output_path=None):
    """Convenience function: export knowledge graph to CONHECIMENTO.md."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kc = KnowledgeConsolidator(base_dir)
    kc.export_to_markdown(output_path)
    return kc.graph
