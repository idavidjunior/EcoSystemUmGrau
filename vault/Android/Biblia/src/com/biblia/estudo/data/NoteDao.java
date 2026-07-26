package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.UserNote;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

public class NoteDao {

    private SQLiteDatabase db;

    public NoteDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(UserNote note) {
        ContentValues cv = new ContentValues();
        cv.put("book_id", note.getBookId());
        cv.put("chapter", note.getChapter());
        cv.put("verse_number", note.getVerseNumber());
        cv.put("content", note.getContent());
        cv.put("color", note.getColor());
        cv.put("created_at", System.currentTimeMillis());
        cv.put("updated_at", System.currentTimeMillis());
        return db.insert(BibleDatabaseHelper.TABLE_NOTES, null, cv);
    }

    public int update(UserNote note) {
        ContentValues cv = new ContentValues();
        cv.put("content", note.getContent());
        cv.put("color", note.getColor());
        cv.put("updated_at", System.currentTimeMillis());
        return db.update(BibleDatabaseHelper.TABLE_NOTES, cv, "_id=?", new String[]{String.valueOf(note.getId())});
    }

    public int delete(long id) {
        return db.delete(BibleDatabaseHelper.TABLE_NOTES, "_id=?", new String[]{String.valueOf(id)});
    }

    public UserNote getByVerse(long bookId, int chapter, int verseNumber) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_NOTES, null,
                "book_id=? AND chapter=? AND verse_number=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter), String.valueOf(verseNumber)},
                null, null, null);
        if (c != null && c.moveToFirst()) {
            UserNote n = cursorToNote(c);
            c.close();
            return n;
        }
        return null;
    }

    public List<UserNote> getByChapter(long bookId, int chapter) {
        List<UserNote> list = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_NOTES, null,
                "book_id=? AND chapter=?",
                new String[]{String.valueOf(bookId), String.valueOf(chapter)},
                null, null, "verse_number ASC");
        if (c != null) {
            while (c.moveToNext()) list.add(cursorToNote(c));
            c.close();
        }
        return list;
    }

    public List<UserNote> getAll() {
        List<UserNote> list = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_NOTES, null,
                null, null, null, null, "updated_at DESC");
        if (c != null) {
            while (c.moveToNext()) list.add(cursorToNote(c));
            c.close();
        }
        return list;
    }

    public int getCount() {
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_NOTES, null);
        int count = 0;
        if (c != null && c.moveToFirst()) { count = c.getInt(0); c.close(); }
        return count;
    }

    private UserNote cursorToNote(Cursor c) {
        UserNote n = new UserNote();
        n.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        n.setBookId(c.getLong(c.getColumnIndexOrThrow("book_id")));
        n.setChapter(c.getInt(c.getColumnIndexOrThrow("chapter")));
        n.setVerseNumber(c.getInt(c.getColumnIndexOrThrow("verse_number")));
        n.setContent(c.getString(c.getColumnIndexOrThrow("content")));
        n.setColor(c.getInt(c.getColumnIndexOrThrow("color")));
        n.setCreatedAt(new Date(c.getLong(c.getColumnIndexOrThrow("created_at"))));
        n.setUpdatedAt(new Date(c.getLong(c.getColumnIndexOrThrow("updated_at"))));
        return n;
    }
}
