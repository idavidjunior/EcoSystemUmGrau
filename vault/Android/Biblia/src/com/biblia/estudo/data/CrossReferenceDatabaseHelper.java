package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class CrossReferenceDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "referencias.db";
    private static final int DATABASE_VERSION = 1;

    public static final String TABLE_CROSS_REFERENCES = "cross_references";

    public CrossReferenceDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE " + TABLE_CROSS_REFERENCES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "source_book_id INTEGER NOT NULL," +
                "source_chapter INTEGER NOT NULL," +
                "source_verse INTEGER NOT NULL," +
                "target_book_id INTEGER NOT NULL," +
                "target_chapter INTEGER NOT NULL," +
                "target_verse INTEGER NOT NULL," +
                "target_verse_text TEXT," +
                "target_book_name TEXT," +
                "notes TEXT" +
                ");");

        db.execSQL("CREATE INDEX idx_cross_ref_source ON " + TABLE_CROSS_REFERENCES +
                "(source_book_id, source_chapter, source_verse);");
        db.execSQL("CREATE INDEX idx_cross_ref_target ON " + TABLE_CROSS_REFERENCES +
                "(target_book_id, target_chapter, target_verse);");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        // Future migrations
    }
}
