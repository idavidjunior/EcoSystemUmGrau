#!/usr/bin/env python3
import sys, re, os, sqlite3

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\Playtec-bancada\Desktop\Downloads\TodososLivrosAPÓCRIFOS.txt'
DST = r'C:\Users\Playtec-bancada\.local\share\opencode\worktree\699a669f2471f9aad160ee2785dc9a1ba96b1245\crisp-lagoon\BibliaEstudo\assets\databases\biblia_estudo.db'

with open(SRC, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

books_def = [
    (228, 1882, 'Gênesis Apócrifo', 'O Gênesis Apócrifo (1QapGen) é um dos rolos do Mar Morto, recontando a história de Gênesis com elaborações midráshicas.', False),
    (1882, 3786, 'Livro de Melquisedeque', 'Narração pseudepígrafa que expande a figura de Melquisedeque, sacerdote-rei de Salém.', True),
    (3786, 3837, 'Oração de Manassés', 'Oração penitencial atribuída ao rei Manassés de Judá.', False),
    (3837, 3956, 'Apocalipse das Semanas de Enoch', 'Divisão da história em semanas proféticas, do Livro de Enoque.', True),
    (3956, 3983, 'Salmo 151', 'Salmo apócrifo de Davi sobre sua unção e vitória sobre Golias.', True),
    (3983, 4510, 'Proto-Evangelho de Tiago', 'Vida de Maria, seu nascimento e o nascimento de Jesus. Séc. II.', True),
    (4510, 5037, 'Evangelho de Tomé', '114 ditos de Jesus. Nag Hammadi, Séc. I-II.', True),
    (5037, 5927, 'Evangelho de Pedro', 'Paixão, morte e ressurreição de Jesus. Séc. II.', False),
    (5927, 6382, 'Evangelho de Bartolomeu', 'Diálogo de Jesus ressurreto com Bartolomeu.', False),
    (6382, 7055, 'Evangelho de Filipe', 'Ditos gnósticos sobre sacramentos. Nag Hammadi.', True),
    (7055, 7139, 'Evangelho de Maria Madalena', 'Diálogo sobre pecado e ascensão da alma.', True),
    (7139, 7564, 'A Sophia de Jesus Cristo', 'Revelação sobre a Sophia divina. Nag Hammadi.', True),
    (7564, 15129, 'Pistis Sophia', 'Tratado gnóstico em 4 livros sobre mistérios celestes. Séc. III.', True),
    (15129, 15169, 'Epístola do Rei Abgaro', 'Correspondência entre Abgaro V de Edessa e Jesus.', True),
    (15169, 15715, 'História de José, o Carpinteiro', 'Vida e morte de José, pai terreno de Jesus. Séc. IV.', True),
    (15715, 15795, 'Atos de João', 'Milagres e ensinamentos do apóstolo João. Séc. II.', False),
    (15795, 15823, 'A Sentença Condenatória de Jesus Cristo', 'Sentença de Pilatos contra Jesus.', False),
    (15823, 15908, 'Relatório de Pôncio Pilatos a Tibério César', 'Relato de Pilatos ao imperador.', False),
    (15908, 15943, 'Epístola aos Laodicenses', 'Breve carta atribuída a Paulo.', False),
    (15943, len(lines), 'Primeira Carta de São Clemente aos Coríntios', 'Carta de Clemente Romano. ~96 d.C.', True),
]

def clean_text(text):
    text = re.sub(r'={3,}\s*P[áa]gina\s+\d+\s*={3,}', '', text)
    # Remove blank lines at start/end
    lines_clean = []
    for l in text.split('\n'):
        lines_clean.append(l.strip())
    text = '\n'.join(lines_clean)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

ROMAN_RE = re.compile(r'^(X{0,3}(IX|IV|V?I{0,3})|L?X{0,3}(IX|IV|V?I{0,3})|C?L?X{0,3}(IX|IV|V?I{0,3})|D?C?L?X{0,3}(IX|IV|V?I{0,3})|M{0,4}C?L?X{0,3}(IX|IV|V?I{0,3}))$', re.IGNORECASE)

def is_roman_numeral(word):
    word = word.strip('.,:;!? ')
    if not word or len(word) > 15:
        return False
    return bool(ROMAN_RE.match(word))

def is_meaningful_header(line):
    l = line.strip()
    if not l or len(l) < 2 or len(l) > 120:
        return False
    if l.startswith('===') or 'Página' in l:
        return False
    if re.search(r'(?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s', l, re.IGNORECASE):
        return True
    words = l.strip('.,:;!? ').split()
    if len(words) == 1 and is_roman_numeral(words[0]) and l.isupper():
        return True
    # Also check roman numerals that are the only content on the line (not all-caps but standalone)
    if len(words) == 1 and is_roman_numeral(words[0]) and len(l) <= 10 and l.isdigit() == False:
        return True
    if l.isupper() and len(l) > 4 and len(words) <= 10:
        if all(len(w) > 1 or w in ('A', 'E', 'O', 'De', 'Da', 'Do', 'Em', 'Para') for w in words):
            return True
    if re.match(r'^\d+\s*[-–—]\s', l) and len(l) > 40:
        return True
    if l.startswith('Capítulo') or l.startswith('CAPÍTULO'):
        return True
    return False

def merge_consecutive_headers(lines):
    """Merge consecutive header lines into one."""
    result = []
    i = 0
    while i < len(lines):
        l = lines[i]
        stripped = l.strip()
        if is_meaningful_header(l) and i + 1 < len(lines):
            next_stripped = lines[i+1].strip()
            # If next line is also a header (all-caps short), merge them
            if is_meaningful_header(lines[i+1]) and len(next_stripped) < 50:
                merged = stripped + ' ' + next_stripped
                result.append(merged)
                i += 2
                continue
            # If next line is empty and line after is a header, we have multi-line title
            if not next_stripped and i + 2 < len(lines) and is_meaningful_header(lines[i+2]):
                merged = stripped + ' ' + lines[i+2].strip()
                result.append(merged)
                result.append('')  # keep the blank line
                i += 3
                continue
        result.append(l)
        i += 1
    return result

def split_into_chapters(text, book_name, has_chapters=True):
    lines = text.split('\n')
    lines = merge_consecutive_headers(lines)
    
    chapters = []
    current_lines = []
    current_title = None
    found_any_header = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append('')
            continue
        
        if is_meaningful_header(line):
            found_any_header = True
            prev_text = '\n'.join(current_lines).strip()
            if prev_text:
                chapters.append((current_title or book_name, prev_text))
            current_lines = []
            current_title = stripped
        else:
            current_lines.append(line)
    
    prev_text = '\n'.join(current_lines).strip()
    if prev_text:
        chapters.append((current_title or book_name, prev_text))
    
    if not found_any_header:
        return [(book_name, text)]
    
    # Filter: remove chapters where content is just the title or empty
    filtered = []
    for title, content in chapters:
        content_stripped = content.strip()
        title_stripped = title.strip()
        if not content_stripped or content_stripped == title_stripped:
            continue
        # If chapter is very short and has an explicit chapter marker, keep it
        # Otherwise, merge with previous chapter
        if len(content_stripped) < 80 and not re.search(r'(?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s', title, re.IGNORECASE):
            if filtered:
                prev_title, prev_content = filtered[-1]
                filtered[-1] = (prev_title, prev_content + '\n\n' + title + '\n' + content_stripped)
                continue
        filtered.append((title, content_stripped))
    
    return filtered if filtered else [(book_name, text)]

def roman_to_int(s):
    s = s.strip('.,:;!? ')
    roman_map = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
    result = 0
    for i in range(len(s)):
        if i+1 < len(s) and roman_map.get(s[i], 0) < roman_map.get(s[i+1], 0):
            result -= roman_map.get(s[i], 0)
        else:
            result += roman_map.get(s[i], 0)
    return result if result > 0 else 0

def try_extract_num(title):
    m = re.search(r'(?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s+(\d+|[IXVLCM]+)', title, re.IGNORECASE)
    if m:
        num_str = m.group(1)
        if num_str.isdigit():
            return int(num_str)
        roman_val = roman_to_int(num_str)
        if roman_val:
            return roman_val
        return 0
    words = title.strip('.,:;!? ').split()
    if len(words) == 1 and is_roman_numeral(words[0]):
        roman_val = roman_to_int(words[0])
        if roman_val:
            return roman_val
        return 0
    m = re.match(r'^(\d+)\s*[-–—]', title)
    if m:
        return int(m.group(1))
    m = re.match(r'^(\d+)\s', title)
    if m:
        return int(m.group(1))
    return 0

print("Processing books...")
conn = sqlite3.connect(DST)
c = conn.cursor()

c.executescript('''
    DROP TABLE IF EXISTS apocrypha_chapters;
    DROP TABLE IF EXISTS apocrypha_books;
    CREATE TABLE apocrypha_books (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        book_order INTEGER NOT NULL
    );
    CREATE TABLE apocrypha_chapters (
        _id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        chapter_number INTEGER NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES apocrypha_books(_id)
    );
    CREATE INDEX IF NOT EXISTS idx_apocrypha_chapters_book ON apocrypha_chapters(book_id, chapter_number);
''')
conn.commit()

for bidx, (start, end, name, desc, has_chapters) in enumerate(books_def):
    print(f'\n[{bidx+1}/{len(books_def)}] {name}...', end=' ')
    
    raw = '\n'.join(lines[start:end])
    cleaned = clean_text(raw)
    chapters = split_into_chapters(cleaned, name, has_chapters)
    print(f'{len(chapters)} seções')
    
    c.execute('INSERT INTO apocrypha_books (name, description, book_order) VALUES (?, ?, ?)',
              (name, desc, bidx + 1))
    book_id = c.lastrowid
    
    for ch_idx, (title, content) in enumerate(chapters):
        num = try_extract_num(title)
        if num > 0:
            chapter_num = num
        else:
            chapter_num = ch_idx + 1
        c.execute('INSERT INTO apocrypha_chapters (book_id, chapter_number, title, content) VALUES (?, ?, ?, ?)',
                  (book_id, chapter_num, title, content[:1000000]))
    
    conn.commit()

print('\n\n=== FINAL VERIFICATION ===')
c.execute('SELECT COUNT(*) FROM apocrypha_books')
print(f'Total books: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM apocrypha_chapters')
print(f'Total chapters: {c.fetchone()[0]}')
c.execute('SELECT SUM(LENGTH(content)) FROM apocrypha_chapters')
print(f'Total content: {c.fetchone()[0]} chars')

print('\nPer-book stats:')
c.execute('SELECT b._id, b.name, COUNT(c._id), SUM(LENGTH(c.content)) FROM apocrypha_books b LEFT JOIN apocrypha_chapters c ON b._id=c.book_id GROUP BY b._id ORDER BY b.book_order')
for row in c.fetchall():
    print(f'  {row[0]:2d}. {row[1]:45s} {row[2]:3d} chaps, {row[3]:7d} chars')

c.execute('PRAGMA user_version')
old_ver = c.fetchone()[0]
new_ver = old_ver + 1
c.execute(f'PRAGMA user_version = {new_ver}')
conn.commit()
print(f'\nuser_version: {old_ver} -> {new_ver}')

conn.close()
print(f'\nDone!')
