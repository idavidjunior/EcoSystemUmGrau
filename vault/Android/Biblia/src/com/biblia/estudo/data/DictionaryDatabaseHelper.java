package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class DictionaryDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "dicionario.db";
    private static final int DATABASE_VERSION = 1;

    public static final String TABLE_DICTIONARY = "dictionary";

    public DictionaryDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE " + TABLE_DICTIONARY + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "word TEXT NOT NULL," +
                "transliteration TEXT," +
                "original_language TEXT," +
                "strong_number TEXT," +
                "definition TEXT NOT NULL," +
                "etymology TEXT," +
                "usage_notes TEXT," +
                "related_words TEXT," +
                "occurrences TEXT" +
                ");");

        db.execSQL("CREATE INDEX idx_dictionary_word ON " + TABLE_DICTIONARY + "(word);");
        db.execSQL("CREATE INDEX idx_dictionary_strong ON " + TABLE_DICTIONARY + "(strong_number);");
        db.execSQL("CREATE INDEX idx_dictionary_lang ON " + TABLE_DICTIONARY + "(original_language);");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        // Future migrations
    }
}
