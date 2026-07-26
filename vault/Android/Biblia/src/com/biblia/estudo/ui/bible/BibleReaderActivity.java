package com.biblia.estudo.ui.bible;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.SpannableString;
import android.text.Spanned;
import android.text.style.BackgroundColorSpan;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.view.GestureDetector;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.app.ThemeManager;
import com.biblia.estudo.data.BookDao;
import com.biblia.estudo.data.FavoriteDao;
import com.biblia.estudo.data.HighlightDao;
import com.biblia.estudo.data.NoteDao;
import com.biblia.estudo.data.ReadingProgressDao;
import com.biblia.estudo.data.VerseDao;
import com.biblia.estudo.model.Favorite;
import com.biblia.estudo.model.Highlight;
import com.biblia.estudo.model.UserNote;
import com.biblia.estudo.model.Verse;
import com.biblia.estudo.ui.dictionary.DictionaryActivity;
import com.biblia.estudo.utils.NavigationHelper;
import com.biblia.estudo.utils.ShareUtils;

import java.util.List;

public class BibleReaderActivity extends Activity {

    private LinearLayout versesContainer;
    private ScrollView scrollView;
    private TextView toolbarTitle;
    private Spinner chapterSpinner;
    private TextView btnPrev, btnNext;
    private TextView btnChapterTitle;
    private TextView btnFavorite, btnShare, btnNote, btnDictionary;

    private long bookId;
    private String bookName;
    private int chapterCount;
    private int currentChapter = 1;
    private int currentVerse = 1;

    private VerseDao verseDao;
    private NoteDao noteDao;
    private HighlightDao highlightDao;
    private FavoriteDao favoriteDao;
    private ReadingProgressDao progressDao;
    private ThemeManager themeManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        themeManager = BibliaApplication.getThemeManager();
        themeManager.applyTheme(this);
        setContentView(R.layout.activity_bible_reader);

        bookId = getIntent().getLongExtra("book_id", 1);
        bookName = getIntent().getStringExtra("book_name");
        chapterCount = getIntent().getIntExtra("chapter_count", 1);

        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
        verseDao = new VerseDao(db);
        highlightDao = new HighlightDao(db);
        noteDao = new NoteDao(db);
        favoriteDao = new FavoriteDao(db);
        progressDao = new ReadingProgressDao(db);

        initViews();
        setupChapterSpinner();
        setupNavigationButtons();
        setupBottomPanel();
        loadChapter(currentChapter);
    }

    private void initViews() {
        versesContainer = findViewById(R.id.versesContainer);
        scrollView = findViewById(R.id.scrollView);
        toolbarTitle = findViewById(R.id.toolbarTitle);
        chapterSpinner = findViewById(R.id.chapterSpinner);
        btnPrev = (TextView) findViewById(R.id.btnPreviousChapter);
        btnNext = (TextView) findViewById(R.id.btnNextChapter);
        btnChapterTitle = findViewById(R.id.btnChapterTitle);

        toolbarTitle.setText(bookName);
        NavigationHelper.setupBackButton(this);
    }

    private void setupChapterSpinner() {
        String[] chapters = new String[chapterCount];
        for (int i = 0; i < chapterCount; i++) {
            chapters[i] = "Capítulo " + (i + 1);
        }
        android.widget.ArrayAdapter<String> adapter = new android.widget.ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, chapters);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        chapterSpinner.setAdapter(adapter);

        chapterSpinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> parent, View view, int position, long id) {
                if (position + 1 != currentChapter) {
                    currentChapter = position + 1;
                    loadChapter(currentChapter);
                }
            }
            @Override
            public void onNothingSelected(android.widget.AdapterView<?> parent) {}
        });
    }

    private void setupNavigationButtons() {
        btnPrev.setOnClickListener(v -> {
            if (currentChapter > 1) {
                currentChapter--;
                chapterSpinner.setSelection(currentChapter - 1);
                loadChapter(currentChapter);
            }
        });
        btnNext.setOnClickListener(v -> {
            if (currentChapter < chapterCount) {
                currentChapter++;
                chapterSpinner.setSelection(currentChapter - 1);
                loadChapter(currentChapter);
            }
        });
    }

    private void setupBottomPanel() {
        btnFavorite = findViewById(R.id.btnFavorite);
        btnShare = findViewById(R.id.btnShare);
        btnNote = findViewById(R.id.btnNote);
        btnDictionary = findViewById(R.id.btnDictionary);

        btnFavorite.setOnClickListener(v -> toggleFavorite());
        btnShare.setOnClickListener(v -> shareCurrentVerse());
        btnNote.setOnClickListener(v -> showNoteDialog());
        btnDictionary.setOnClickListener(v -> {
            startActivity(new Intent(this, DictionaryActivity.class));
        });
    }

    private void loadChapter(int chapter) {
        if (btnChapterTitle != null) {
            btnChapterTitle.setText("Capítulo " + chapter);
        }

        List<Verse> verses = verseDao.getChapter(bookId, chapter);
        if (verses.isEmpty()) {
            versesContainer.removeAllViews();
            TextView empty = new TextView(this);
            empty.setText("Capítulo não encontrado");
            empty.setTextSize(themeManager.getFontSize());
            empty.setTextColor(getResources().getColor(R.color.text_secondary));
            empty.setPadding(20, 40, 20, 40);
            versesContainer.addView(empty);
            return;
        }

        List<Highlight> highlights = highlightDao.getByChapter(bookId, chapter);
        versesContainer.removeAllViews();

        int fontSize = themeManager.getFontSize();
        int fontFamily = themeManager.getFontFamily();
        float spacing = themeManager.getLineSpacing();

        // Add chapter heading
        TextView heading = new TextView(this);
        heading.setText("Capítulo " + chapter);
        heading.setTextSize(fontSize + 4);
        heading.setTextColor(getResources().getColor(R.color.chapter_number));
        heading.setTypeface(null, Typeface.BOLD);
        heading.setPadding(20, 16, 20, 16);
        versesContainer.addView(heading);

        for (Verse verse : verses) {
            final long fBookId = verse.getBookId();
            final int fChapter = verse.getChapter();
            final int fVerseNum = verse.getVerseNumber();
            final String fVerseText = verse.getText();

            boolean isHighlighted = false;
            String hlColor = null;
            for (Highlight h : highlights) {
                if (fVerseNum >= h.getVerseStart() && fVerseNum <= h.getVerseEnd()) {
                    isHighlighted = true;
                    hlColor = h.getColor();
                    break;
                }
            }

            boolean hasNote = noteDao.getByVerse(fBookId, fChapter, fVerseNum) != null;

            LinearLayout verseLayout = new LinearLayout(this);
            verseLayout.setOrientation(LinearLayout.HORIZONTAL);
            verseLayout.setPadding(20, 6, 20, 6);
            verseLayout.setBackgroundResource(isHighlighted ? 0 : android.R.color.transparent);

            if (isHighlighted && hlColor != null) {
                try {
                    verseLayout.setBackgroundColor(Color.parseColor(hlColor));
                } catch (Exception ignored) {}
            }

            // Verse number
            TextView numView = new TextView(this);
            numView.setText(String.valueOf(fVerseNum));
            numView.setTextSize(fontSize - 2);
            numView.setTextColor(getResources().getColor(R.color.verse_number));
            numView.setTypeface(null, Typeface.BOLD);
            numView.setPadding(0, 0, 8, 0);
            if (hasNote) {
                numView.setText(numView.getText() + "📝");
            }

            // Verse text
            TextView textView = new TextView(this);
            textView.setText(fVerseText);
            textView.setTextSize(fontSize);
            textView.setLineSpacing(0f, spacing);
            if (fontFamily == ThemeManager.FONT_SERIF) {
                textView.setTypeface(Typeface.SERIF);
            } else {
                textView.setTypeface(Typeface.DEFAULT);
            }
            textView.setTextColor(getResources().getColor(R.color.text_primary));

            verseLayout.addView(numView);
            verseLayout.addView(textView, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

            // Click on verse number or text
            View.OnClickListener clickListener = v -> {
                currentVerse = fVerseNum;
                showVerseActions(fVerseNum, fVerseText);
            };

            View.OnLongClickListener longClickListener = v -> {
                currentVerse = fVerseNum;
                v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
                showVerseActions(fVerseNum, fVerseText);
                return true;
            };

            numView.setOnClickListener(clickListener);
            textView.setOnClickListener(clickListener);
            numView.setOnLongClickListener(longClickListener);
            textView.setOnLongClickListener(longClickListener);

            versesContainer.addView(verseLayout);

            // Add a thin divider between verses
            View divider = new View(this);
            divider.setLayoutParams(new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT, 1));
            divider.setBackgroundColor(getResources().getColor(R.color.divider));
            versesContainer.addView(divider);
        }

        progressDao.saveProgress(bookId, chapter, 1);
        themeManager.saveLastPosition(bookId, chapter, 1);
    }

    private void showVerseActions(int verseNum, String verseText) {
        currentVerse = verseNum;
        boolean isFav = favoriteDao.isFavorite(bookId, currentChapter, currentVerse);
        boolean hasNote = noteDao.getByVerse(bookId, currentChapter, currentVerse) != null;
        boolean isHl = highlightDao.isHighlighted(bookId, currentChapter, currentVerse);

        String[] options = new String[4];
        options[0] = isFav ? "★ Remover Favorito" : "☆ Favoritar";
        options[1] = "📤 Compartilhar";
        options[2] = hasNote ? "📝 Editar Nota" : "📝 Adicionar Nota";
        options[3] = isHl ? "🎨 Remover Destaque" : "🎨 Destacar cor";

        new AlertDialog.Builder(this)
                .setTitle(bookName + " " + currentChapter + ":" + verseNum)
                .setItems(options, (dialog, which) -> {
                    switch (which) {
                        case 0: toggleFavorite(); break;
                        case 1: shareCurrentVerse(); break;
                        case 2: showNoteDialog(); break;
                        case 3: showColorPicker(); break;
                    }
                }).show();
    }

    private void toggleFavorite() {
        boolean isFav = favoriteDao.isFavorite(bookId, currentChapter, currentVerse);
        if (isFav) {
            favoriteDao.deleteByReference(bookId, currentChapter, currentVerse);
            Toast.makeText(this, R.string.favorite_removed, Toast.LENGTH_SHORT).show();
        } else {
            Favorite fav = new Favorite();
            fav.setBookId(bookId);
            fav.setChapter(currentChapter);
            fav.setVerseNumber(currentVerse);
            fav.setBookName(bookName);
            List<Verse> verses = verseDao.getVersesRange(bookId, currentChapter, currentVerse, currentVerse);
            if (!verses.isEmpty()) fav.setVerseText(verses.get(0).getText());
            favoriteDao.insert(fav);
            Toast.makeText(this, R.string.favorite_added, Toast.LENGTH_SHORT).show();
        }
    }

    private void shareCurrentVerse() {
        List<Verse> verses = verseDao.getVersesRange(bookId, currentChapter, currentVerse, currentVerse);
        if (!verses.isEmpty()) {
            Verse v = verses.get(0);
            String ref = bookName + " " + currentChapter + ":" + currentVerse;
            String fullText = ref + "\n\n" + v.getText();
            ShareUtils.shareVerse(this, ref, v.getText());
        }
    }

    private void showNoteDialog() {
        UserNote existing = noteDao.getByVerse(bookId, currentChapter, currentVerse);
        android.widget.EditText input = new android.widget.EditText(this);
        input.setHint("Escreva sua anotação...");
        if (existing != null) input.setText(existing.getContent());
        input.setPadding(40, 20, 40, 20);

        new AlertDialog.Builder(this)
                .setTitle("Anotação - " + bookName + " " + currentChapter + ":" + currentVerse)
                .setView(input)
                .setPositiveButton("Salvar", (dialog, which) -> {
                    String text = input.getText().toString().trim();
                    if (text.isEmpty()) {
                        if (existing != null) {
                            noteDao.delete(existing.getId());
                            Toast.makeText(this, "Anotação removida", Toast.LENGTH_SHORT).show();
                        }
                        return;
                    }
                    if (existing != null) {
                        existing.setContent(text);
                        noteDao.update(existing);
                    } else {
                        UserNote n = new UserNote();
                        n.setBookId(bookId);
                        n.setChapter(currentChapter);
                        n.setVerseNumber(currentVerse);
                        n.setContent(text);
                        noteDao.insert(n);
                    }
                    Toast.makeText(this, "Anotação salva", Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton("Cancelar", null)
                .show();
    }

    private void showColorPicker() {
        final String[] colors = {"#FFF9C4", "#FFCDD2", "#C8E6C9", "#BBDEFB", "#E1BEE7", "#FFE0B2"};
        final String[] labels = {"Amarelo", "Vermelho", "Verde", "Azul", "Roxo", "Laranja"};

        new AlertDialog.Builder(this)
                .setTitle("Destacar versículo")
                .setItems(labels, (dialog, which) -> {
                    String color = colors[which];
                    boolean hl = highlightDao.isHighlighted(bookId, currentChapter, currentVerse);
                    if (hl) {
                        highlightDao.deleteByVerse(bookId, currentChapter, currentVerse);
                        Toast.makeText(this, "Destaque removido", Toast.LENGTH_SHORT).show();
                    } else {
                        Highlight h = new Highlight();
                        h.setBookId(bookId);
                        h.setChapter(currentChapter);
                        h.setVerseStart(currentVerse);
                        h.setVerseEnd(currentVerse);
                        h.setColor(color);
                        highlightDao.insert(h);
                        Toast.makeText(this, "Destaque adicionado", Toast.LENGTH_SHORT).show();
                    }
                    loadChapter(currentChapter);
                }).show();
    }
}
