#!/usr/bin/env python3
import sys, re, os, sqlite3

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'C:\Users\Playtec-bancada\Desktop\Downloads\TodososLivrosAPÓCRIFOS.txt'
DST = r'C:\Users\Playtec-bancada\.local\share\opencode\worktree\699a669f2471f9aad160ee2785dc9a1ba96b1245\crisp-lagoon\BibliaEstudo\scripts\apocrypha.db'

with open(SRC, 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Book definitions: (start_line, end_line, name, description)
books_def = [
    (228, 1882, 'Gênesis Apócrifo', 'O Gênesis Apócrifo (1QapGen) é um dos rolos do Mar Morto, recontando a história de Gênesis com elaborações midráshicas. Fonte: Manuscritos de Qumran.'),
    (1882, 3786, 'Livro de Melquisedeque', 'Narração pseudepígrafa que expande a figura de Melquisedeque, sacerdote-rei de Salém, e sua conexão com a teologia celeste.'),
    (3786, 3837, 'Oração de Manassés', 'Oração penitencial atribuída ao rei Manassés de Judá, encontrada em algumas tradições gregas e siríacas.'),
    (3837, 3956, 'Apocalipse das Semanas de Enoch', 'Parte do Livro de Enoque, dividindo a história em dez semanas proféticas, desde a criação até o juízo final.'),
    (3956, 3983, 'Salmo 151', 'Salmo apócrifo atribuído a Davi, narrando sua unção e vitória sobre Golias. Presente na Septuaginta e em Qumran.'),
    (3983, 4510, 'Proto-Evangelho de Tiago', 'Evangelho da infância que narra a vida de Maria, seu nascimento milagroso, educação no Templo e o nascimento de Jesus. Século II d.C.'),
    (4510, 5037, 'Evangelho de Tomé', 'Coleção de 114 ditos de Jesus, descoberta em Nag Hammadi (1945). Considerada uma das fontes mais antigas sobre os ensinamentos de Jesus.'),
    (5037, 5927, 'Evangelho de Pedro', 'Evangelho fragmentário que narra a paixão, morte e ressurreição de Jesus sob uma perspectiva docética. Descoberto em Akhmim, Egito.'),
    (5927, 6382, 'Evangelho de Bartolomeu', 'Diálogo entre Jesus ressuscitado e o apóstolo Bartolomeu, revelando mistérios celestes e a descida ao inferno.'),
    (6382, 7055, 'Evangelho de Filipe', 'Evangelho gnóstico contendo ditos e parábolas sobre sacramentos, a união espiritual e a natureza de Cristo. Nag Hammadi.'),
    (7055, 7139, 'Evangelho de Maria Madalena', 'Diálogo entre Jesus e Maria Madalena, focando na natureza do pecado e na ascensão da alma. Papiro de Berlim 8502.'),
    (7139, 7564, 'A Sophia de Jesus Cristo', 'Revelação gnóstica onde Jesus ressurreto transmite ensinamentos sobre a Sophia divina e a criação do universo. Nag Hammadi.'),
    (7564, 15129, 'Pistis Sophia', 'Longo tratado gnóstico em quatro livros, descrevendo os ensinamentos de Jesus após a ressurreição sobre os mistérios celestes e a queda e redenção de Pistis Sophia. Século III d.C.'),
    (15129, 15169, 'Epístola do Rei Abgaro', 'Correspondência entre o rei Abgaro V de Edessa e Jesus Cristo, com a promessa de cura e proteção para a cidade.'),
    (15169, 15715, 'História de José, o Carpinteiro', 'Narração da vida e morte de José, pai terreno de Jesus, com diálogos entre Jesus e Maria sobre a morte de José. Século IV d.C.'),
    (15715, 15795, 'Atos de João', 'Atos apócrifos narrando os milagres e ensinamentos do apóstolo João, incluindo o famoso hino de Jesus. Século II d.C.'),
    (15795, 15823, 'A Sentença Condenatória de Jesus Cristo', 'Documento que registra a sentença oficial de Pilatos contra Jesus, conforme supostos arquivos romanos.'),
    (15823, 15908, 'Relatório de Pôncio Pilatos a Tibério César', 'Relato de Pilatos ao imperador Tibério sobre o julgamento, crucificação e ressurreição de Jesus.'),
    (15908, 15943, 'Epístola aos Laodicenses', 'Breve carta apócrifa atribuída a Paulo, mencionada em Colossenses 4:16, contendo exortações morais.'),
    (15943, 17069, 'Primeira Carta de São Clemente aos Coríntios', 'Carta escrita pelo bispo Clemente de Roma à igreja de Corinto (~96 d.C.), tratando de divisões internas e exortando à unidade e ao arrependimento.'),
]

def clean_text(text):
    # Remove page markers like "=== Página N ==="
    text = re.sub(r'={3,}\s*P[áa]gina\s+\d+\s*={3,}', '', text)
    # Remove leading/trailing whitespace per line
    lines_clean = []
    for l in text.split('\n'):
        lines_clean.append(l.strip())
    text = '\n'.join(lines_clean)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_chapters(text, book_name):
    """Try to split text into chapters based on various chapter marker patterns."""
    # Try multiple chapter patterns
    patterns = [
        r'(?:CAP[IÍ]TULO|Cap[ií]tulo)\s+(?:[IXVLCM]+|\d+)',  # CAPÍTULO I, Capítulo 1
        r'(?:CAPITULO|Cap[ií]tulo)\s+(?:[IXVLCM]+|\d+)',       # CAPITULO XLIV
    ]
    
    chapters = []
    
    # Build a combined regex
    chapter_re = re.compile(r'^((?:CAP[IÍ]TULO|Cap[ií]tulo|CAPITULO)\s+[\dIVXLCOM]+)', re.IGNORECASE | re.MULTILINE)
    
    # Split by chapter markers
    parts = chapter_re.split(text)
    
    if len(parts) <= 1:
        # No chapter markers found - whole text is one chapter
        return [(1, book_name, text)]
    
    # First part is the intro/preface
    intro = parts[0].strip()
    
    # Process subsequent pairs
    chapter_num = 0
    if intro:
        chapter_num += 1
        chapters.append((chapter_num, 'Introdução', intro))
    
    for i in range(1, len(parts), 2):
        chapter_num += 1
        title = parts[i].strip() if i < len(parts) else f'Capítulo {chapter_num}'
        content = parts[i+1].strip() if i+1 < len(parts) else ''
        # Try to extract the chapter number from title
        num_match = re.search(r'(\d+|[IXVLCM]+)', title)
        if num_match:
            try:
                # Roman numeral conversion
                roman = num_match.group(1)
                if roman.isdigit():
                    chapter_num = int(roman)
                else:
                    chapter_num = roman_to_int(roman)
            except:
                chapter_num += 1
        else:
            chapter_num += 1
        
        chapters.append((chapter_num, title, content))
    
    return chapters

def roman_to_int(s):
    roman_map = {'I':1, 'V':5, 'X':10, 'L':50, 'C':100, 'D':500, 'M':1000}
    result = 0
    for i in range(len(s)):
        if i+1 < len(s) and roman_map.get(s[i], 0) < roman_map.get(s[i+1], 0):
            result -= roman_map.get(s[i], 0)
        else:
            result += roman_map.get(s[i], 0)
    return result

def split_long_chapter(name, content, max_chars=50000):
    """Split very long chapters by page sections or into manageable chunks."""
    if len(content) <= max_chars:
        return [(1, name, content)]
    
    # Try to split by numbered sections (like "1 -", "2 -")
    parts = re.split(r'\n(?:^|\s)(\d+)\s*[-–]\s*', content, flags=re.MULTILINE)
    if len(parts) <= 1:
        # Try splitting by double newlines
        paragraphs = content.split('\n\n')
        chunks = []
        current = []
        current_len = 0
        chunk_num = 0
        for p in paragraphs:
            if current_len + len(p) > max_chars and current:
                chunk_num += 1
                chunks.append((chunk_num, f'{name} (parte {chunk_num})', '\n\n'.join(current)))
                current = [p]
                current_len = len(p)
            else:
                current.append(p)
                current_len += len(p) + 2
        if current:
            chunk_num += 1
            chunks.append((chunk_num, f'{name} (parte {chunk_num})', '\n\n'.join(current)))
        return chunks
    
    # Process numbered sections
    chunks = []
    current_parts = [parts[0]]
    current_len = len(parts[0])
    chunk_num = 0
    
    for i in range(1, len(parts), 2):
        if current_len + len(parts[i]) + len(parts[i+1] if i+1 < len(parts) else '') > max_chars and current_parts:
            chunk_num += 1
            chunks.append((chunk_num, f'{name} (parte {chunk_num})', ''.join(current_parts)))
            current_parts = []
            current_len = 0
        current_parts.append('\n' + parts[i] + ' - ' + (parts[i+1] if i+1 < len(parts) else ''))
        current_len += len(parts[i]) + len(parts[i+1] if i+1 < len(parts) else '') + 4
    
    if current_parts:
        chunk_num += 1
        chunks.append((chunk_num, f'{name} (parte {chunk_num})', ''.join(current_parts)))
    
    return chunks

print("Creating database...")
conn = sqlite3.connect(DST)
c = conn.cursor()

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

for bidx, (start, end, name, desc) in enumerate(books_def):
    print(f'\nProcessing: {name} ({bidx+1}/{len(books_def)})')
    
    raw = '\n'.join(lines[start:end])
    cleaned = clean_text(raw)
    
    print(f'  Cleaned size: {len(cleaned)} chars')
    
    # Parse chapters
    chapters = parse_chapters(cleaned, name)
    print(f'  Chapters found: {len(chapters)}')
    
    # For very long books, check if any chapter needs splitting
    final_chapters = []
    for ch_num, ch_title, ch_content in chapters:
        if len(ch_content) > 60000:
            print(f'  Splitting chapter {ch_num} ({len(ch_content)} chars)...')
            sub_chapters = split_long_chapter(f'{ch_title}', ch_content)
            for sub_num, sub_title, sub_content in sub_chapters:
                final_chapters.append((sub_num, sub_title, sub_content))
        else:
            final_chapters.append((ch_num, ch_title, ch_content))
    
    # Insert book
    c.execute('INSERT INTO apocrypha_books (name, description, book_order) VALUES (?, ?, ?)',
              (name, desc, bidx + 1))
    book_id = c.lastrowid
    
    # Insert chapters
    for ch_num, ch_title, ch_content in final_chapters:
        c.execute('INSERT INTO apocrypha_chapters (book_id, chapter_number, title, content) VALUES (?, ?, ?, ?)',
                  (book_id, ch_num, ch_title, ch_content))
    
    conn.commit()
    print(f'  Inserted {len(final_chapters)} chapters')

# Verify
print('\n\n=== VERIFICATION ===')
c.execute('SELECT COUNT(*) FROM apocrypha_books')
print(f'Total books: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM apocrypha_chapters')
print(f'Total chapters: {c.fetchone()[0]}')
c.execute('SELECT SUM(LENGTH(content)) FROM apocrypha_chapters')
print(f'Total content size: {c.fetchone()[0]} chars')

print('\nBooks:')
c.execute('SELECT _id, name, book_order FROM apocrypha_books ORDER BY book_order')
for row in c.fetchall():
    c.execute('SELECT COUNT(*), SUM(LENGTH(content)) FROM apocrypha_chapters WHERE book_id=?', (row[0],))
    stats = c.fetchone()
    print(f'  {row[0]}: {row[1]} ({stats[0]} chaps, {stats[1]} chars)')

conn.close()
print(f'\nDatabase saved to: {DST}')
print(f'Size: {os.path.getsize(DST)} bytes')
