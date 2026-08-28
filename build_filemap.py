import json
import os
import re
from datetime import datetime
from pathlib import Path

# Load memories
with open('conhecimento/memoria/memories.json', 'r', encoding='utf-8') as f:
    memories = json.load(f)

# Load actual files
files = os.listdir('conhecimento/aprendizados')
md_files = [f for f in files if f.endswith('.md')]

# Build file index: {date_slug: filepath}
file_index = {}
for f in md_files:
    # Extract date from filename: YYYY-MM-DD-...
    match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)\.md$', f)
    if match:
        date_str = match.group(1)
        slug = match.group(2)
        if date_str not in file_index:
            file_index[date_str] = []
        file_index[date_str].append({'slug': slug, 'filename': f})

print(f'Memories: {len(memories)}, MD files: {len(md_files)}')

# Build mapping: memory_id -> filepath
id_to_file = {}

for m in memories:
    mid = m['id']
    created = m.get('created_at', '')
    task = m.get('task', '')
    
    if not created:
        continue
    
    try:
        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d')
    except:
        continue
    
    if date_str in file_index:
        # Try to match by title similarity
        task_slug = task.lower().replace(' ', '-').replace(':', '').replace('/', '-')[:60]
        task_slug = re.sub(r'[^a-z0-9\-]', '', task_slug)
        
        candidates = file_index[date_str]
        best_match = None
        best_score = 0
        
        for c in candidates:
            # Simple word overlap score
            task_words = set(task_slug.split('-'))
            file_words = set(c['slug'].split('-'))
            overlap = len(task_words & file_words)
            if overlap > best_score:
                best_score = overlap
                best_match = c
        
        if best_match and best_score >= 2:  # At least 2 words in common
            id_to_file[mid] = f"conhecimento/aprendizados/{best_match['filename']}"
        elif len(candidates) == 1:
            # Only one file for that day, use it
            id_to_file[mid] = f"conhecimento/aprendizados/{candidates[0]['filename']}"

print(f'Mapped: {len(id_to_file)} / {len(memories)}')

# Save mapping
with open('conhecimento/memoria/id_to_file.json', 'w', encoding='utf-8') as f:
    json.dump(id_to_file, f, ensure_ascii=False, indent=2)

print('Saved to conhecimento/memoria/id_to_file.json')

# Show samples
for mid, fpath in list(id_to_file.items())[:10]:
    print(f'  id={mid} -> {fpath}')