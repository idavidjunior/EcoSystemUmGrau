"""Gera notas .md para o Obsidian a partir do knowledge_graph.json"""
import json, os, re, sys
from datetime import datetime

LER_DIR = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada'),
                       'Desktop', 'Codigos', 'EcoSystemUmGrau', 'ler-runtime')
OUTPUT_DIR = os.path.join(os.environ.get('USERPROFILE', 'C:\\Users\\Playtec-bancada'),
                          'Desktop', 'Codigos', 'EcoSystemUmGrau', 'conhecimento', 'notas')

GRAPH_FILE = os.path.join(LER_DIR, 'knowledge', 'knowledge_graph.json')

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\u00C0-\u024F\u00E0-\u024F\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text.strip().lower())[:60]

def frontmatter(tags, aliases=None, date=None):
    fm = ['---']
    if tags: fm.append(f'tags: [{", ".join(tags)}]')
    if aliases: fm.append(f'aliases: [{", ".join(aliases)}]')
    if date: fm.append(f'date: {date}')
    fm.append('---')
    return '\n'.join(fm)

def write_note(subdir, filename, content):
    d = os.path.join(OUTPUT_DIR, subdir)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def do_generate():
    print(f'Lendo {GRAPH_FILE}...')
    with open(GRAPH_FILE, encoding='utf-8') as f:
        g = json.load(f)

    total = 0
    last_updated = g.get('last_updated', datetime.now().isoformat())[:10]

    # Patterns
    for p in g.get('patterns', []):
        title = (p.get('title', '') or '').strip()
        if not title: continue
        slug = slugify(title)
        if not slug: continue
        tags = ['padrao', slugify(p.get('source', ''))]
        body = f'**Fonte:** {p.get("source", "")}\n\n'
        body += f'{p.get("description", p.get("action", ""))}\n'
        write_note('padroes', f'{slug}.md', f'{frontmatter(tags, [title], last_updated)}\n\n# {title}\n\n{body}')
        total += 1

    # Decisions
    for d in g.get('decisions', []):
        title = (d.get('decision', '') or '').strip()
        if not title: continue
        slug = slugify(title[:80])
        if not slug: continue
        tags = ['decisao', slugify(d.get('source', ''))]
        body = f'**Fonte:** {d.get("source", "")}\n\n'
        body += f'{d.get("rationale", "")}\n'
        write_note('decisoes', f'{slug}.md', f'{frontmatter(tags, [title[:60]], last_updated)}\n\n# {title}\n\n{body}')
        total += 1

    # Bug fixes
    for b in g.get('bug_fixes', []):
        title = b.get('issue', '') or b.get('root_cause', 'Bug fix')[:60]
        if not title.strip(' -\n\t\r') or title.strip() == '-----------':
            continue
        slug = slugify(title[:80])
        if not slug: continue
        tags = ['bug', slugify(b.get('source', ''))]
        body = f'**Projeto:** {b.get("source", "")}\n\n'
        body += f'## Causa Raiz\n{b.get("root_cause", "")}\n\n'
        body += f'## Correcao\n{b.get("fix", "")}\n'
        write_note('bugs', f'{slug}.md', f'{frontmatter(tags, [title[:60]], last_updated)}\n\n# Bug: {title}\n\n{body}')
        total += 1

    # Cognitive patterns
    for c in g.get('cognitive_patterns', []):
        title = c.get('title', 'Cognitive pattern')
        slug = slugify(title)
        tags = ['cognitivo', c.get('domain', 'general')]
        body = f'**Dominio:** {c.get("domain", "")}\n\n'
        body += f'{c.get("body", "")}\n'
        write_note('cognitivo', f'{slug}.md', f'{frontmatter(tags, [title], last_updated)}\n\n# {title}\n\n{body}')
        total += 1

    # Heuristics
    for h in g.get('heuristics', []):
        title = h.get('title', 'Heuristic')
        slug = slugify(title)
        tags = ['heuristica', slugify(h.get('domain', ''))]
        body = f'**Dominio:** {h.get("domain", "")} | **Fonte:** {h.get("source", "")}\n\n'
        body += f'{h.get("description", "")}\n'
        write_note('heuristicas', f'{slug}.md', f'{frontmatter(tags, [title], last_updated)}\n\n# {title}\n\n{body}')
        total += 1

    # Frameworks
    for f in g.get('frameworks', []):
        name = f.get('name', 'Framework')
        slug = slugify(name)
        tags = ['framework']
        body = f'{f.get("description", "")}\n\n'
        body += f'{f.get("body", "")}\n'
        write_note('frameworks', f'{slug}.md', f'{frontmatter(tags, [name], last_updated)}\n\n# {name}\n\n{body}')
        total += 1

    # Mission learnings
    for m in g.get('mission_learnings', []):
        goal = m.get('goal_objective', 'Mission')[:80]
        slug = slugify(goal)
        ts = m.get('timestamp', '')[:10]
        tags_list = m.get('tags', [])
        if isinstance(tags_list, list):
            tags = ['missao'] + [slugify(t) for t in tags_list[:3]]
        else:
            tags = ['missao']
        body = f'**Status:** {m.get("status", "")}\n\n'
        body += f'**Objetivo:** {goal}\n\n'
        files = m.get('files_modified', [])
        if files:
            if isinstance(files, list):
                body += '**Arquivos:** ' + ', '.join(files[:10]) + '\n'
            else:
                body += f'**Arquivos:** {files}\n'
        write_note('missoes', f'{slug}.md', f'{frontmatter(tags, [goal[:60]], ts)}\n\n# {goal}\n\n{body}')
        total += 1

    print(f'{total} notas geradas em {OUTPUT_DIR}')
    return total

if __name__ == '__main__':
    do_generate()
