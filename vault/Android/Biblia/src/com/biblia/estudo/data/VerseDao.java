package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.Verse;

import java.util.ArrayList;
import java.util.List;

public class VerseDao {

    private SQLiteDatabase db;

    public VerseDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(Verse verse) {
        ContentValues cv = new ContentValues();
        cv.put("book_id", verse.getBookId());
        cv.put("chapter", verse.getChapter());
        cv.put("verse_number", verse.getVerseNumber());
        cv.put("text", verse.getText());
        cv.put("hebrew_text", verse.getHebrewText());
        cv.put("greek_text", verse.getGreekText());
        cv.put("has_commentary", verse.hasCommentary() ? 1 : 0);
        cv.put("has_cross_ref", verse.hasCrossReferences() ? 1 : 0);
        return db.insertWithOnConflict(BibleDatabaseHelper.TABLE_VERSES, null, cv,
                SQLiteDatabase.CONFLICT_REPLACE);
    }

    public Verse getVerse(long bookId, int chapter, int verseNumber) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "book_id=? AND chapter=? AND verse_number=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(verseNumber)},
                null, null, null);
        if (c != null && c.moveToFirst()) {
            Verse v = cursorToVerse(c);
            c.close();
            return v;
        }
        return null;
    }

    public List<Verse> getChapter(long bookId, int chapter) {
        List<Verse> verses = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, "verse_number ASC");
        if (c != null) {
            while (c.moveToNext()) {
                verses.add(cursorToVerse(c));
            }
            c.close();
        }
        return verses;
    }

    public List<Verse> getVersesRange(long bookId, int chapter, int startVerse, int endVerse) {
        List<Verse> verses = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "book_id=? AND chapter=? AND verse_number>=? AND verse_number<=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter),
                        String.valueOf(startVerse), String.valueOf(endVerse)},
                null, null, "verse_number ASC");
        if (c != null) {
            while (c.moveToNext()) {
                verses.add(cursorToVerse(c));
            }
            c.close();
        }
        return verses;
    }

    public int getVerseCount(long bookId, int chapter) {
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_VERSES +
                " WHERE book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)});
        int count = 0;
        if (c != null && c.moveToFirst()) {
            count = c.getInt(0);
            c.close();
        }
        return count;
    }

    public List<Verse> searchByText(String query) {
        List<Verse> results = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "text LIKE ?", new String[]{"%" + query + "%"},
                null, null, "book_id ASC, chapter ASC, verse_number ASC", "100");
        if (c != null) {
            while (c.moveToNext()) {
                results.add(cursorToVerse(c));
            }
            c.close();
        }
        return results;
    }

    public Cursor searchByTextCursor(String query) {
        return db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "text LIKE ?", new String[]{"%" + query + "%"},
                null, null, "book_id ASC, chapter ASC, verse_number ASC");
    }

    public Cursor searchByPhraseCursor(String phrase) {
        return db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "text LIKE ?", new String[]{"%" + phrase + "%"},
                null, null, "book_id ASC, chapter ASC, verse_number ASC");
    }

    public List<Verse> searchByBook(long bookId, String query) {
        List<Verse> results = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_VERSES, null,
                "book_id=? AND text LIKE ?",
                new String[]{String.valueOf(bookId), "%" + query + "%"},
                null, null, "chapter ASC, verse_number ASC");
        if (c != null) {
            while (c.moveToNext()) {
                results.add(cursorToVerse(c));
            }
            c.close();
        }
        return results;
    }

    public void updateCommentaryFlag(long verseId, boolean hasCommentary) {
        ContentValues cv = new ContentValues();
        cv.put("has_commentary", hasCommentary ? 1 : 0);
        db.update(BibleDatabaseHelper.TABLE_VERSES, cv, "_id=?", new String[]{String.valueOf(verseId)});
    }

    public void updateCrossRefFlag(long verseId, boolean hasCrossRef) {
        ContentValues cv = new ContentValues();
        cv.put("has_cross_ref", hasCrossRef ? 1 : 0);
        db.update(BibleDatabaseHelper.TABLE_VERSES, cv, "_id=?", new String[]{String.valueOf(verseId)});
    }

    private Verse cursorToVerse(Cursor c) {
        Verse v = new Verse();
        v.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        v.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        v.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        v.setVerseNumber(c.getInt(c.getColumnIndexOrThrow("verse_number")));
        v.setText(c.getString(c.getColumnIndexOrThrow("text")));
        v.setHebrewText(c.getString(c.getColumnIndexOrThrow("hebrew_text")));
        v.setGreekText(c.getString(c.getColumnIndexOrThrow("greek_text")));
        v.setHasCommentary(c.getInt(c.getColumnIndexOrThrow("has_commentary")) > 0);
        v.setHasCrossReferences(c.getInt(c.getColumnIndexOrThrow("has_cross_ref")) > 0);
        return v;
    }
}
