#!/usr/bin/env python3
"""Agent Prompt Adapter for Self-Improvement based on Learning Profiles.

This module implements automatic adaptation of agent specifications based on:
1. Performance history from learning profiles
2. Identified strength/weakness patterns
3. Recommended skill combinations
4. Successful collaboration patterns

The adapted prompts include:
- Enhanced instructions addressing known weaknesses
- Embedded collaboration hints for recommended partners
- Skill-specific guidance based on successful combinations
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AdaptationResult:
    """Represents the result of adapting an agent's prompt."""

    agent_id: str
    original_prompt_hash: str
    adaptations_applied: list[str]
    new_sections_added: list[str]
    collaboration_hints: list[str]
    skill_enhancements: list[str]
    timestamp: str


# Configuration constants
ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
LEARNING_REPO = ROOT / "learning-repository"
AGENT_PROFILES = LEARNING_REPO / "agent-profiles"
COLLABORATION_PATTERNS = LEARNING_REPO / "collaboration-patterns.json"
SKILL_COMBINATIONS = LEARNING_REPO / "skill-combinations.json"
ADAPTED_AGENTS_DIR = ROOT / "adapted-agents"


def ensure_directories() -> None:
    """Create necessary directories for adapted agents."""
    ADAPTED_AGENTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    """Load JSON file with error handling.
    
    Args:
        path: Path to JSON file.
        
    Returns:
        Parsed JSON content or empty dict if file doesn't exist.
    """
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save data to JSON file.
    
    Args:
        path: Destination path.
        data: Data to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


def load_agent_profile(agent_id: str) -> dict:
    """Load an agent's learning profile.
    
    Args:
        agent_id: ID of the agent.
        
    Returns:
        Agent profile dictionary or empty dict if not found.
    """
    profile_path = AGENT_PROFILES / f"{agent_id}.json"
    return load_json(profile_path)


def load_original_agent_spec(agent_id: str) -> str:
    """Load the original agent specification markdown file.
    
    Args:
        agent_id: ID of the agent.
        
    Returns:
        Content of the agent spec file.
    """
    agent_file = AGENTS_DIR / f"{agent_id}.md"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent spec not found: {agent_file}")
    return agent_file.read_text(encoding="utf-8")


def compute_content_hash(content: str) -> str:
    """Compute a simple hash of content for tracking changes.
    
    Args:
        content: String content to hash.
        
    Returns:
        Hexadecimal hash string (first 16 chars).
    """
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_weakness_mitigation(weaknesses: dict[str, int]) -> str:
    """Generate mitigation strategies based on weakness patterns.
    
    Args:
        weaknesses: Dictionary of weakness patterns and their counts.
        
    Returns:
        Markdown section with mitigation strategies.
    """
    if not weaknesses:
        return ""
    
    mitigation_map = {
        "missing_requirements": (
            "## 🔍 Checklist de Requisitos\n\n"
            "Antes de finalizar sua resposta, verifique:\n"
            "- [ ] Todos os requisitos explícitos foram atendidos?\n"
            "- [ ] Cada termo obrigatório está presente na resposta?\n"
            "- [ ] Você pode citar explicitamente onde cada requisito foi abordado?\n"
        ),
        "weak_clarity": (
            "## 📝 Diretrizes de Clareza\n\n"
            "Para melhorar a clareza da sua resposta:\n"
            "- Use estrutura hierárquica clara (títulos, subtítulos)\n"
            "- Inclua exemplos concretos quando aplicável\n"
            "- Evite jargões sem explicação\n"
            "- Sumarize pontos-chave no início\n"
        ),
        "forbidden_violations": (
            "## ⚠️ Restrições Importantes\n\n"
            "Atenção especial para NÃO incluir:\n"
            "- Termos ou conceitos proibidos no contexto\n"
            "- Suposições não validadas\n"
            "- Recomendações genéricas sem fundamentação\n"
        ),
        "dimension_compliance": (
            "## 📊 Dimensões de Avaliação\n\n"
            "Sua resposta será avaliada em múltiplas dimensões. Certifique-se de:\n"
            "- Abordar cada dimensão explicitamente\n"
            "- Fornecer evidências concretas para cada ponto\n"
            "- Conectar recomendações às melhores práticas do domínio\n"
        ),
    }
    
    sections = []
    sorted_weaknesses = sorted(weaknesses.items(), key=lambda x: x[1], reverse=True)
    
    for pattern, count in sorted_weaknesses[:3]:  # Top 3 weaknesses
        base_pattern = pattern.split(":")[0]
        if base_pattern in mitigation_map:
            sections.append(mitigation_map[base_pattern])
    
    if not sections:
        # Generic mitigation for unknown patterns
        sections.append(
            "## 🎯 Áreas de Melhoria Identificadas\n\n"
            "Baseado no histórico de desempenho, foque em:\n"
            + "\n".join(f"- {pattern} (ocorreu {count} vezes)" 
                       for pattern, count in sorted_weaknesses[:3])
        )
    
    return "\n".join(sections)


def generate_collaboration_hints(collaborations: list[str], agent_id: str) -> list[str]:
    """Generate collaboration hints based on successful patterns.
    
    Args:
        collaborations: List of successful collaboration pairs.
        agent_id: ID of the current agent.
        
    Returns:
        List of collaboration hint strings.
    """
    hints = []
    
    for collab_pair in collaborations[:3]:  # Top 3 collaborations
        # Extract partner agent ID
        parts = collab_pair.split("+")
        partner = parts[1] if parts[0] == agent_id else parts[0]
        
        hints.append(
            f"💡 **Colaboração sugerida**: Para cenários complexos, considere coordenar "
            f"com `{partner}`. Esta combinação demonstrou alta eficácia em avaliações anteriores."
        )
    
    return hints


def generate_skill_enhancements(skill_combos: list[list[str]]) -> str:
    """Generate skill enhancement guidance based on successful combinations.
    
    Args:
        skill_combos: List of successful skill combinations.
        
    Returns:
        Markdown section with skill guidance.
    """
    if not skill_combos:
        return ""
    
    # Flatten and count skills
    skill_counts = {}
    for combo in skill_combos[:5]:  # Top 5 combinations
        for skill in combo:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    if not top_skills:
        return ""
    
    skills_section = (
        "## 🛠️ Skills Recomendadas para Este Agente\n\n"
        "Baseado em combinações de alto desempenho, integre estes conceitos:\n\n"
    )
    
    skill_descriptions = {
        "search-first": "Busca iterativa e validação contínua de informações",
        "observability-stack": "Monitoramento, tracing e debugging distribuído",
        "resilience-engineering": "Padrões de resiliência e tolerância a falhas",
        "security-review": "Análise de vulnerabilidades e revisão de segurança",
        "tdd-workflow": "Desenvolvimento guiado por testes",
        "migration-playbooks": "Estratégias de migração e modernização",
        "api-design": "Práticas de design de APIs RESTful e GraphQL",
        "error-message-design": "Design de mensagens de erro claras e acionáveis",
    }
    
    for skill, _ in top_skills:
        desc = skill_descriptions.get(skill, "Conceito avançado de engenharia de software")
        skills_section += f"- **{skill}**: {desc}\n"
    
    return skills_section


def adapt_agent_prompt(agent_id: str) -> AdaptationResult | None:
    """Adapt an agent's prompt based on its learning profile.
    
    Args:
        agent_id: ID of the agent to adapt.
        
    Returns:
        AdaptationResult or None if adaptation failed.
    """
    # Load profile
    profile = load_agent_profile(agent_id)
    if not profile:
        print(f"⚠️  No profile found for {agent_id}")
        return None
    
    # Load original spec
    try:
        original_content = load_original_agent_spec(agent_id)
    except FileNotFoundError as e:
        print(f"⚠️  {e}")
        return None
    
    original_hash = compute_content_hash(original_content)
    
    # Parse existing sections
    sections = parse_markdown_sections(original_content)
    
    # Generate adaptations
    adaptations_applied = []
    new_sections = []
    
    # 1. Add weakness mitigations
    weaknesses = profile.get("weakness_patterns", {})
    if weaknesses:
        mitigation_section = generate_weakness_mitigation(weaknesses)
        if mitigation_section:
            new_sections.append(("weakness_mitigation", mitigation_section))
            adaptations_applied.append(f"Added mitigation for {len(weaknesses)} weakness patterns")
    
    # 2. Add collaboration hints
    collaborations = profile.get("successful_collaborations", [])
    collaboration_hints = []
    if collaborations:
        collaboration_hints = generate_collaboration_hints(collaborations, agent_id)
        if collaboration_hints:
            adaptations_applied.append(f"Added {len(collaboration_hints)} collaboration hints")
    
    # 3. Add skill enhancements
    skill_combos = profile.get("recommended_skill_combinations", [])
    skill_section = ""
    if skill_combos:
        skill_section = generate_skill_enhancements(skill_combos)
        if skill_section:
            new_sections.append(("skill_enhancement", skill_section))
            adaptations_applied.append(f"Added {len(skill_combos)} skill recommendations")
    
    # Build adapted content
    adapted_content = build_adapted_content(
        original_content,
        sections,
        new_sections,
        collaboration_hints
    )
    
    # Save adapted spec
    adapted_file = ADAPTED_AGENTS_DIR / f"{agent_id}.md"
    adapted_file.write_text(adapted_content, encoding="utf-8")
    
    # Save adaptation metadata
    adaptation_metadata = {
        "agent_id": agent_id,
        "original_hash": original_hash,
        "adapted_at": datetime.now(timezone.utc).isoformat(),
        "adaptations_count": len(adaptations_applied),
        "new_sections_count": len(new_sections),
    }
    save_json(ADAPTED_AGENTS_DIR / f"{agent_id}.adaptation.json", adaptation_metadata)
    
    return AdaptationResult(
        agent_id=agent_id,
        original_prompt_hash=original_hash,
        adaptations_applied=adaptations_applied,
        new_sections_added=[name for name, _ in new_sections],
        collaboration_hints=[h.split(":")[0] for h in collaboration_hints],
        skill_enhancements=list(set(s for combo in skill_combos for s in combo)),
        timestamp=datetime.now(timezone.utc).isoformat()
    )


def parse_markdown_sections(content: str) -> dict[str, tuple[int, int]]:
    """Parse markdown content into sections.
    
    Args:
        content: Markdown content to parse.
        
    Returns:
        Dictionary mapping section titles to (start_line, end_line).
    """
    sections = {}
    lines = content.split("\n")
    current_section = "header"
    start_line = 0
    
    for i, line in enumerate(lines):
        if line.startswith("# "):
            if current_section != "header":
                sections[current_section] = (start_line, i)
            current_section = line[2:].strip()
            start_line = i
    
    sections[current_section] = (start_line, len(lines))
    return sections


def build_adapted_content(
    original: str,
    sections: dict[str, tuple[int, int]],
    new_sections: list[tuple[str, str]],
    collaboration_hints: list[str]
) -> str:
    """Build the adapted agent content.
    
    Args:
        original: Original content.
        sections: Parsed sections.
        new_sections: New sections to add.
        collaboration_hints: Collaboration hints to embed.
        
    Returns:
        Adapted content string.
    """
    lines = original.split("\n")
    
    # Find insertion point (before last section)
    section_list = sorted(sections.items(), key=lambda x: x[1][0])
    if len(section_list) >= 2:
        insert_section = section_list[-2][0]
        insert_line = sections[insert_section][1]
    else:
        insert_line = len(lines)
    
    # Build adaptation block
    adaptation_block = ["\n", "---", "", "## 🔄 Adaptações Baseadas em Aprendizado", ""]
    adaptation_block.append(f"*Estas diretrizes foram geradas automaticamente baseado no histórico de desempenho.*\n")
    
    # Add collaboration hints as callout
    if collaboration_hints:
        adaptation_block.append("### 🤝 Colaborações Recomendadas\n")
        adaptation_block.extend(collaboration_hints)
        adaptation_block.append("")
    
    # Add new sections
    for _, section_content in new_sections:
        adaptation_block.append(section_content)
    
    # Insert adaptation block
    adapted_lines = lines[:insert_line] + adaptation_block + lines[insert_line:]
    
    return "\n".join(adapted_lines)


def adapt_all_agents() -> list[AdaptationResult]:
    """Adapt all agents that have learning profiles.
    
    Returns:
        List of AdaptationResult objects.
    """
    ensure_directories()
    
    results = []
    
    # Find all agent profiles
    for profile_path in AGENT_PROFILES.glob("*.json"):
        agent_id = profile_path.stem
        result = adapt_agent_prompt(agent_id)
        if result:
            results.append(result)
    
    return results


def main() -> None:
    """Main entry point for the agent prompt adapter."""
    print("=" * 70)
    print("🔄 Agent Prompt Adapter - Auto-Improvement System")
    print("=" * 70)
    print()
    
    results = adapt_all_agents()
    
    if not results:
        print("⚠️  No agents were adapted. Ensure learning profiles exist.")
        print("   Run: python scripts/orchestrate_feedback_loop.py first")
        return
    
    print(f"✅ Successfully adapted {len(results)} agent(s):\n")
    
    for result in results:
        print(f"📄 {result.agent_id}")
        print(f"   Adaptations: {len(result.adaptations_applied)}")
        print(f"   New sections: {', '.join(result.new_sections_added)}")
        if result.collaboration_hints:
            print(f"   Collaboration hints: {len(result.collaboration_hints)}")
        if result.skill_enhancements:
            print(f"   Skill enhancements: {', '.join(result.skill_enhancements[:3])}")
        print()
    
    print("=" * 70)
    print(f"💾 Adapted agents saved to: {ADAPTED_AGENTS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
