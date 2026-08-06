"""Fix corrupted JSON in widget HTML by finding and fixing malformed node/edge data."""
from pathlib import Path
import re

content = Path(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html').read_text(encoding='utf-8')

# Find the corrupt section - around the duplicated session word
bad_pos = content.find('sessionsession')
if bad_pos >= 0:
    context = content[bad_pos-80:bad_pos+80]
    print(f'CORRUPT TAG FOUND at byte {bad_pos}:')
    print(f'  Context: ...{context}...')
    print()

# Search for ALL malformed patterns: tags with duplicate segments
import re
dups = list(re.finditer(r'"tags":\s*\[.*?\]', content))
print(f'Total "tags" arrays found: {len(dups)}')

# Find ones with formatting issues
bad_tags = []
for m in dups:
    tag_text = m.group(0)
    if 'sessionsession' in tag_text or ']]' in tag_text:
        bad_tags.append((m.start(), tag_text[:150]))
        
print(f'\nBad tags found: {len(bad_tags)}')
for pos, text in bad_tags:
    print(f'  Byte {pos}: {text}...')

# Also check title fields for unescaped characters
bad_titles = list(re.finditer(r'"title":\s*"[^"]*?\n[^"]*?"', content))
print(f'\nTitle lines with newlines: {len(bad_titles)}')
for m in bad_titles[:5]:
    print(f'  Byte {m.start()}: {m.group(0)[:100]}')

# Look for patterns that would break JSON
# Unescaped backslashes, quotes, newlines within strings  
print()
print('Checking for JSON-breaking patterns in the raw data...')
# Find the data blocks
nodes_start = content.find('const nodes = new vis.DataSet([')
edges_start = content.find('const edges = new vis.DataSet([')

# Check for raw newlines inside title fields (would break JSON)
if nodes_start >= 0:
    nodes_end = content.find(']);', nodes_start) + 2
    nodes_block = content[nodes_start+38:nodes_end]  # skip prefix
    
    # Count unescaped tabs or newlines inside quotes
    quote_regions = list(re.finditer(r'"[^"]*"', nodes_block))
    bad_quotes = [m for m in quote_regions if '\n' in m.group(0) or '\r' in m.group(0)]
    print(f'Nodes with raw newlines in quotes: {len(bad_quotes)}')
    for m in bad_quotes[:5]:
        sample = m.group(0)
        print(f'  Len {len(sample)}: {sample[:80]}...')