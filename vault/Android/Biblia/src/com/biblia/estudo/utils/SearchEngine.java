package com.biblia.estudo.utils;

import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.data.BibleDatabaseHelper;
import com.biblia.estudo.data.DatabaseManager;
import com.biblia.estudo.model.Verse;

import java.util.ArrayList;
import java.util.List;

public class SearchEngine {

    private SQLiteDatabase db;

    public SearchEngine(DatabaseManager dbManager) {
        this.db = dbManager.getBibleDatabase();
    }

    public List<Verse> searchByWord(String word) {
        List<Verse> results = new ArrayList<>();
        Cursor c = db.rawQuery(
                "SELECT v.*, b.name as book_name FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE v.text LIKE ? ORDER BY b.book_order, v.chapter, v.verse_number LIMIT 200",
                new String[]{"%" + word.trim() + "%"});
        if (c != null) {
            while (c.moveToNext()) {
                results.add(cursorToVerse(c));
            }
            c.close();
        }
        return results;
    }

    public Cursor searchByWordCursor(String word) {
        return db.rawQuery(
                "SELECT v._id, v.book_id, v.chapter, v.verse_number, v.text, " +
                        "b.name as book_name " +
                        "FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE v.text LIKE ? ORDER BY b.book_order, v.chapter, v.verse_number LIMIT 200",
                new String[]{"%" + word.trim() + "%"});
    }

    public Cursor searchByPhraseCursor(String phrase) {
        return db.rawQuery(
                "SELECT v._id, v.book_id, v.chapter, v.verse_number, v.text, " +
                        "b.name as book_name " +
                        "FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE v.text LIKE ? ORDER BY b.book_order, v.chapter, v.verse_number LIMIT 200",
                new String[]{"%" + phrase.trim() + "%"});
    }

    public Cursor searchByBookAndWord(long bookId, String word) {
        return db.rawQuery(
                "SELECT v._id, v.book_id, v.chapter, v.verse_number, v.text, " +
                        "b.name as book_name " +
                        "FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE v.book_id=? AND v.text LIKE ? " +
                        "ORDER BY v.chapter, v.verse_number LIMIT 200",
                new String[]{String.valueOf(bookId), "%" + word.trim() + "%"});
    }

    public Cursor searchByBookCursor(String bookName) {
        return db.rawQuery(
                "SELECT v._id, v.book_id, v.chapter, v.verse_number, v.text, " +
                        "b.name as book_name " +
                        "FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE b.name LIKE ? " +
                        "ORDER BY b.book_order, v.chapter, v.verse_number LIMIT 200",
                new String[]{"%" + bookName.trim() + "%"});
    }

    public Cursor searchByTopic(String topic) {
        return db.rawQuery(
                "SELECT v._id, v.book_id, v.chapter, v.verse_number, v.text, " +
                        "b.name as book_name, b.main_themes " +
                        "FROM " + BibleDatabaseHelper.TABLE_VERSES + " v " +
                        "JOIN " + BibleDatabaseHelper.TABLE_BOOKS + " b ON v.book_id = b._id " +
                        "WHERE b.main_themes LIKE ? OR b.name LIKE ? " +
                        "ORDER BY b.book_order, v.chapter, v.verse_number LIMIT 200",
                new String[]{"%" + topic.trim() + "%", "%" + topic.trim() + "%"});
    }

    public List<String> getSuggestions(String prefix) {
        List<String> suggestions = new ArrayList<>();
        Cursor c = db.rawQuery(
                "SELECT DISTINCT b.name FROM " + BibleDatabaseHelper.TABLE_BOOKS + " b " +
                        "WHERE b.name LIKE ? LIMIT 10",
                new String[]{"%" + prefix + "%"});
        if (c != null) {
            while (c.moveToNext()) {
                suggestions.add(c.getString(0));
            }
            c.close();
        }
        return suggestions;
    }

    public Cursor searchApocrypha(String query) {
        return db.rawQuery(
                "SELECT c._id, c.book_id, c.chapter_number as chapter, c.title, c.content as text, " +
                        "b.name as book_name " +
                        "FROM apocrypha_chapters c " +
                        "JOIN apocrypha_books b ON c.book_id = b._id " +
                        "WHERE c.content LIKE ? OR c.title LIKE ? " +
                        "ORDER BY b.book_order, c.chapter_number LIMIT 200",
                new String[]{"%" + query.trim() + "%", "%" + query.trim() + "%"});
    }

    private Verse cursorToVerse(Cursor c) {
        Verse v = new Verse();
        v.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        v.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        v.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        v.setVerseNumber(c.getInt(c.getColumnIndexOrThrow("verse_number")));
        v.setText(c.getString(c.getColumnIndexOrThrow("text")));
        return v;
    }
}
