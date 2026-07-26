package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class BibleDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "biblia_estudo.db";
    private static final int DATABASE_VERSION = 6;

    public static final String TABLE_BOOKS = "books";
    public static final String TABLE_VERSES = "verses";
    public static final String TABLE_FAVORITES = "favorites";
    public static final String TABLE_NOTES = "user_notes";
    public static final String TABLE_HIGHLIGHTS = "highlights";
    public static final String TABLE_READING_PROGRESS = "reading_progress";
    public static final String TABLE_READING_PLANS = "reading_plans";
    public static final String TABLE_PLAN_DAYS = "plan_days";

    public BibleDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        createBooksTable(db);
        createVersesTable(db);
        createFavoritesTable(db);
        createNotesTable(db);
        createHighlightsTable(db);
        createReadingProgressTable(db);
        createReadingPlansTable(db);
        createPlanDaysTable(db);
        createIndexes(db);
    }

    private void createBooksTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_BOOKS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "abbreviation TEXT," +
                "testament INTEGER NOT NULL," +
                "category INTEGER," +
                "chapter_count INTEGER NOT NULL," +
                "book_order INTEGER NOT NULL," +
                "author TEXT," +
                "historical_context TEXT," +
                "literary_structure TEXT," +
                "outline TEXT," +
                "main_themes TEXT," +
                "curiosities TEXT" +
                ");");
    }

    private void createVersesTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_VERSES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse_number INTEGER NOT NULL," +
                "text TEXT NOT NULL," +
                "hebrew_text TEXT," +
                "greek_text TEXT," +
                "has_commentary INTEGER DEFAULT 0," +
                "has_cross_ref INTEGER DEFAULT 0" +
                ");");
    }

    private void createFavoritesTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_FAVORITES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse_number INTEGER," +
                "verse_text TEXT," +
                "book_name TEXT," +
                "tags TEXT," +
                "color INTEGER DEFAULT 0," +
                "created_at INTEGER NOT NULL" +
                ");");
    }

    private void createNotesTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_NOTES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER," +
                "verse_number INTEGER," +
                "content TEXT NOT NULL," +
                "color INTEGER DEFAULT 0," +
                "created_at INTEGER NOT NULL," +
                "updated_at INTEGER NOT NULL" +
                ");");
    }

    private void createHighlightsTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_HIGHLIGHTS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse_start INTEGER NOT NULL," +
                "verse_end INTEGER NOT NULL," +
                "color TEXT NOT NULL," +
                "created_at INTEGER NOT NULL" +
                ");");
    }

    private void createReadingProgressTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_READING_PROGRESS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse INTEGER," +
                "last_read_at INTEGER NOT NULL," +
                "reading_time_millis INTEGER DEFAULT 0" +
                ");");
    }

    private void createReadingPlansTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_READING_PLANS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "description TEXT," +
                "duration_days INTEGER NOT NULL," +
                "category TEXT," +
                "is_active INTEGER DEFAULT 1," +
                "start_date INTEGER," +
                "current_day INTEGER DEFAULT 0" +
                ");");
    }

    private void createPlanDaysTable(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE_PLAN_DAYS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "plan_id INTEGER NOT NULL," +
                "day_number INTEGER NOT NULL," +
                "book_id INTEGER," +
                "chapter_start INTEGER," +
                "chapter_end INTEGER," +
                "completed INTEGER DEFAULT 0" +
                ");");
    }

    private void createIndexes(SQLiteDatabase db) {
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_verses_book_chapter ON " + TABLE_VERSES + "(book_id, chapter);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_verses_text ON " + TABLE_VERSES + "(text);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_favorites_book ON " + TABLE_FAVORITES + "(book_id, chapter);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_notes_book ON " + TABLE_NOTES + "(book_id, chapter, verse_number);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_reading_progress ON " + TABLE_READING_PROGRESS + "(last_read_at DESC);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_highlights_book ON " + TABLE_HIGHLIGHTS + "(book_id, chapter);");
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_verses_chapter_verse ON " + TABLE_VERSES + "(chapter, verse_number);");
        db.execSQL("CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts4(content=\"\", text, book_id, chapter, verse_number);");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        if (oldVersion < 2) {
            db.execSQL("CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts4(content=\"\", text, book_id, chapter, verse_number);");
            try {
                db.execSQL("INSERT INTO verses_fts(book_id, chapter, verse_number, text) " +
                        "SELECT book_id, chapter, verse_number, text FROM verses");
            } catch (Exception ignored) {}
        }
        if (oldVersion < 3) {
            // Apocryphal books added in pre-populated database, no structural change needed
        }
    }

    @Override
    public void onConfigure(SQLiteDatabase db) {
        super.onConfigure(db);
        try { db.setForeignKeyConstraintsEnabled(true); } catch (Exception ignored) {}
    }
}
