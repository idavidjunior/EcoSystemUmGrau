#!/usr/bin/env python3
import sys, re, os, sqlite3

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\Playtec-bancada\Desktop\Downloads\TodososLivrosAPÓCRIFOS.txt'
DST = r'C:\Users\Playtec-bancada\.local\share\opencode\worktree\699a669f2471f9aad160ee2785dc9a1ba96b1245\crisp-lagoon\BibliaEstudo\assets\databases\biblia_estudo.db'

with open(SRC, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

books_def = [
    (228, 1882, 'Gênesis Apócrifo', 'O Gênesis Apócrifo (1QapGen) é um dos rolos do Mar Morto, recontando a história de Gênesis com elaborações midráshicas.'),
    (1882, 3786, 'Livro de Melquisedeque', 'Narração pseudepígrafa que expande a figura de Melquisedeque, sacerdote-rei de Salém.'),
    (3786, 3837, 'Oração de Manassés', 'Oração penitencial atribuída ao rei Manassés de Judá.'),
    (3837, 3956, 'Apocalipse das Semanas de Enoch', 'Divisão da história em semanas proféticas, do Livro de Enoque.'),
    (3956, 3983, 'Salmo 151', 'Salmo apócrifo de Davi sobre sua unção e vitória sobre Golias.'),
    (3983, 4510, 'Proto-Evangelho de Tiago', 'Vida de Maria, seu nascimento e o nascimento de Jesus. Séc. II.'),
    (4510, 5037, 'Evangelho de Tomé', '114 ditos de Jesus. Nag Hammadi, Séc. I-II.'),
    (5037, 5927, 'Evangelho de Pedro', 'Paixão, morte e ressurreição de Jesus. Séc. II.'),
    (5927, 6382, 'Evangelho de Bartolomeu', 'Diálogo de Jesus ressurreto com Bartolomeu.'),
    (6382, 7055, 'Evangelho de Filipe', 'Ditos gnósticos sobre sacramentos. Nag Hammadi.'),
    (7055, 7139, 'Evangelho de Maria Madalena', 'Diálogo sobre pecado e ascensão da alma.'),
    (7139, 7564, 'A Sophia de Jesus Cristo', 'Revelação sobre a Sophia divina. Nag Hammadi.'),
    (7564, 15129, 'Pistis Sophia', 'Tratado gnóstico em 4 livros sobre mistérios celestes. Séc. III.'),
    (15129, 15169, 'Epístola do Rei Abgaro', 'Correspondência entre Abgaro V de Edessa e Jesus.'),
    (15169, 15715, 'História de José, o Carpinteiro', 'Vida e morte de José, pai terreno de Jesus. Séc. IV.'),
    (15715, 15795, 'Atos de João', 'Milagres e ensinamentos do apóstolo João. Séc. II.'),
    (15795, 15823, 'A Sentença Condenatória de Jesus Cristo', 'Sentença de Pilatos contra Jesus.'),
    (15823, 15908, 'Relatório de Pôncio Pilatos a Tibério César', 'Relato de Pilatos ao imperador.'),
    (15908, 15943, 'Epístola aos Laodicenses', 'Breve carta atribuída a Paulo.'),
    (15943, len(lines), 'Primeira Carta de São Clemente aos Coríntios', 'Carta de Clemente Romano. ~96 d.C.'),
]

def clean_text(text):
    text = re.sub(r'={3,}\s*P[áa]gina\s+\d+\s*={3,}', '', text)
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
    """Check if a line looks like a section/chapter header."""
    l = line.strip()
    if not l or len(l) < 2 or len(l) > 100:
        return False
    if l.startswith('===') or 'Página' in l:
        return False
    
    # Check for explicit chapter markers
    if re.search(r'(?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s', l, re.IGNORECASE):
        return True
    
    # Check for all-caps roman numerals standing alone
    words = l.strip('.,:;!? ').split()
    if len(words) == 1 and is_roman_numeral(words[0]) and l.isupper():
        return True
    
    # All-caps headers of 2-5 words (book titles, section headers)
    if l.isupper() and len(l) > 5 and len(words) <= 8:
        # Exclude lines that are clearly not headers
        if 'O EVANGELHO' in l or 'DE TOMÉ' in l or 'A NATIVIDADE' in l:
            return True
        if words[0][0].isupper():
            return True
    
    # Check for "Number -" patterns that are section markers
    if re.match(r'^\d+\s*[-–—]\s', l):
        return True
    
    return False

def split_into_chapters(text, book_name):
    """Split text into chapters using all available markers."""
    lines = text.split('\n')
    chapters = []
    current_lines = []
    current_title = 'Início'
    found_any_header = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append('')
            continue
        
        if is_meaningful_header(line):
            found_any_header = True
            # Save previous section
            prev_text = '\n'.join(current_lines).strip()
            if prev_text:
                chapters.append((current_title, prev_text))
            current_lines = []
            current_title = stripped
        
        current_lines.append(line)
    
    # Save last section
    prev_text = '\n'.join(current_lines).strip()
    if prev_text:
        chapters.append((current_title, prev_text))
    
    if not found_any_header:
        # No headers found, return whole text as one chapter
        return [(book_name, text)]
    
    # Filter out very short sections that are just headers
    filtered = []
    for title, content in chapters:
        if content.strip():
            filtered.append((title, content))
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
    """Try to extract a chapter number from the title."""
    # Try "CAPÍTULO N" pattern
    m = re.search(r'(?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s+(\d+|[IXVLCM]+)', title, re.IGNORECASE)
    if m:
        num_str = m.group(1)
        if num_str.isdigit():
            return int(num_str), title
        roman_val = roman_to_int(num_str)
        if roman_val:
            return roman_val, title
        return 0, title
    
    # Try standalone Roman numeral
    words = title.strip('.,:;!? ').split()
    if len(words) == 1 and is_roman_numeral(words[0]):
        roman_val = roman_to_int(words[0])
        if roman_val:
            return roman_val, title
        return 0, title
    
    # Try "Number -" pattern
    m = re.match(r'^(\d+)\s*[-–—]', title)
    if m:
        return int(m.group(1)), title
    
    return 0, title

print("Processing books...")
# Connect to existing db
conn = sqlite3.connect(DST)
c = conn.cursor()

# Check if tables exist
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apocrypha_books'")
if not c.fetchone():
    print("Creating apocrypha tables in existing biblia_estudo.db...")
    c.executescript('''
        CREATE TABLE IF NOT EXISTS apocrypha_books (
            _id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            book_order INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS apocrypha_chapters (
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
else:
    print("Apocrypha tables already exist, replacing data...")
    c.execute("DROP TABLE IF EXISTS apocrypha_chapters")
    c.execute("DROP TABLE IF EXISTS apocrypha_books")
    conn.commit()
    c.executescript('''
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

for bidx, (start, end, name, desc) in enumerate(books_def):
    print(f'\n[{bidx+1}/{len(books_def)}] {name}...', end=' ')
    
    raw = '\n'.join(lines[start:end])
    cleaned = clean_text(raw)
    
    # Split into chapters
    chapters = split_into_chapters(cleaned, name)
    print(f'{len(chapters)} seções')
    
    # Insert book
    c.execute('INSERT INTO apocrypha_books (name, description, book_order) VALUES (?, ?, ?)',
              (name, desc, bidx + 1))
    book_id = c.lastrowid
    
    # Insert chapters with numbering
    for ch_idx, (title, content) in enumerate(chapters):
        # Try to extract chapter number
        num, clean_title = try_extract_num(title)
        if num > 0:
            chapter_num = num
        else:
            chapter_num = ch_idx + 1
        
        c.execute('INSERT INTO apocrypha_chapters (book_id, chapter_number, title, content) VALUES (?, ?, ?, ?)',
                  (book_id, chapter_num, title, content))
    
    conn.commit()

print('\n\n=== FINAL VERIFICATION ===')
c.execute('SELECT COUNT(*) FROM apocrypha_books')
print(f'Total books: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM apocrypha_chapters')
print(f'Total chapters: {c.fetchone()[0]}')
c.execute('SELECT SUM(LENGTH(content)) FROM apocrypha_chapters')
total_chars = c.fetchone()[0]
print(f'Total content: {total_chars} chars')

print('\nPer-book stats:')
c.execute('SELECT b._id, b.name, COUNT(c._id), SUM(LENGTH(c.content)) FROM apocrypha_books b LEFT JOIN apocrypha_chapters c ON b._id=c.book_id GROUP BY b._id ORDER BY b.book_order')
for row in c.fetchall():
    print(f'  {row[0]:2d}. {row[1]:45s} {row[2]:3d} chaps, {row[3]:7d} chars')

# Update database version to trigger re-copy
c.execute('PRAGMA user_version')
old_ver = c.fetchone()[0]
new_ver = old_ver + 1
c.execute(f'PRAGMA user_version = {new_ver}')
conn.commit()

print(f'\nDatabase user_version: {old_ver} -> {new_ver}')
conn.close()

print(f'\nDone! Database updated: {DST}')
