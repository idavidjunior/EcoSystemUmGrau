package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.Favorite;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class FavoriteDao {

    private SQLiteDatabase db;

    public FavoriteDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(Favorite fav) {
        ContentValues cv = new ContentValues();
        cv.put("book_id", fav.getBookId());
        cv.put("chapter", fav.getChapter());
        cv.put("verse_number", fav.getVerseNumber());
        cv.put("verse_text", fav.getVerseText());
        cv.put("book_name", fav.getBookName());
        cv.put("tags", fav.getTags());
        cv.put("color", fav.getColor());
        cv.put("created_at", System.currentTimeMillis());
        return db.insert(BibleDatabaseHelper.TABLE_FAVORITES, null, cv);
    }

    public int delete(long id) {
        return db.delete(BibleDatabaseHelper.TABLE_FAVORITES, "_id=?", new String[]{String.valueOf(id)});
    }

    public int deleteByReference(long bookId, int chapter, int verseNumber) {
        return db.delete(BibleDatabaseHelper.TABLE_FAVORITES,
                "book_id=? AND chapter=? AND verse_number=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter), String.valueOf(verseNumber)});
    }

    public boolean isFavorite(long bookId, int chapter, int verseNumber) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_FAVORITES, new String[]{"_id"},
                "book_id=? AND chapter=? AND verse_number=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter), String.valueOf(verseNumber)},
                null, null, null);
        boolean exists = c != null && c.getCount() > 0;
        if (c != null) c.close();
        return exists;
    }

    public List<Favorite> getAll() {
        List<Favorite> list = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_FAVORITES, null,
                null, null, null, null, "created_at DESC");
        if (c != null) {
            while (c.moveToNext()) list.add(cursorToFavorite(c));
            c.close();
        }
        return list;
    }

    public List<Favorite> search(String query) {
        List<Favorite> list = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_FAVORITES, null,
                "verse_text LIKE ? OR book_name LIKE ? OR tags LIKE ?",
                new String[]{"%" + query + "%", "%" + query + "%", "%" + query + "%"},
                null, null, "created_at DESC");
        if (c != null) {
            while (c.moveToNext()) list.add(cursorToFavorite(c));
            c.close();
        }
        return list;
    }

    public int getCount() {
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_FAVORITES, null);
        int count = 0;
        if (c != null && c.moveToFirst()) { count = c.getInt(0); c.close(); }
        return count;
    }

    private Favorite cursorToFavorite(Cursor c) {
        Favorite f = new Favorite();
        f.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        f.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        f.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        f.setVerseNumber(c.getInt(c.getColumnIndexOrThrow("verse_number")));
        f.setVerseText(c.getString(c.getColumnIndexOrThrow("verse_text")));
        f.setBookName(c.getString(c.getColumnIndexOrThrow("book_name")));
        f.setTags(c.getString(c.getColumnIndexOrThrow("tags")));
        f.setColor(c.getInt(c.getColumnIndexOrThrow("color")));
        f.setCreatedAt(new Date(c.getLong(c.getColumnIndexOrThrow("created_at"))));
        return f;
    }
}
