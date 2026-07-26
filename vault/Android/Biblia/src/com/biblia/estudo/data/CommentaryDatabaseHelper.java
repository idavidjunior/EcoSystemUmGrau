package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class CommentaryDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "comentarios.db";
    private static final int DATABASE_VERSION = 1;

    public static final String TABLE_COMMENTARIES = "commentaries";
    public static final String TABLE_COMMENTARY_AUTHORS = "commentary_authors";

    public CommentaryDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE " + TABLE_COMMENTARY_AUTHORS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "description TEXT," +
                "abbreviation TEXT" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_COMMENTARIES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "author_id INTEGER," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse_start INTEGER DEFAULT 0," +
                "verse_end INTEGER DEFAULT 0," +
                "title TEXT," +
                "content TEXT NOT NULL," +
                "category TEXT," +
                "FOREIGN KEY (author_id) REFERENCES " + TABLE_COMMENTARY_AUTHORS + "(_id)" +
                ");");

        db.execSQL("CREATE INDEX idx_commentaries_book_chapter ON " + TABLE_COMMENTARIES + "(book_id, chapter);");
        db.execSQL("CREATE INDEX idx_commentaries_verse ON " + TABLE_COMMENTARIES + "(verse_start, verse_end);");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        // Future migrations
    }
}
