package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

public class TopicIndexDatabaseHelper extends SQLiteOpenHelper {

    private static final String DATABASE_NAME = "indices.db";
    private static final int DATABASE_VERSION = 1;

    public static final String TABLE_TOPICS = "topics";
    public static final String TABLE_TOPIC_VERSES = "topic_verses";
    public static final String TABLE_PROPHEcies = "prophecies";
    public static final String TABLE_MIRACLES = "miracles";
    public static final String TABLE_PARABLES = "parables";
    public static final String TABLE_FIGURES = "figures";

    public TopicIndexDatabaseHelper(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE " + TABLE_TOPICS + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "description TEXT," +
                "category TEXT," +
                "UNIQUE(name)" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_TOPIC_VERSES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "topic_id INTEGER NOT NULL," +
                "book_id INTEGER NOT NULL," +
                "chapter INTEGER NOT NULL," +
                "verse INTEGER," +
                "verse_text TEXT," +
                "FOREIGN KEY (topic_id) REFERENCES " + TABLE_TOPICS + "(_id)" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_PROPHEcies + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "prophecy TEXT NOT NULL," +
                "book_id INTEGER," +
                "chapter INTEGER," +
                "verse INTEGER," +
                "fulfillment TEXT," +
                "fulfillment_ref TEXT," +
                "category TEXT" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_MIRACLES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "title TEXT NOT NULL," +
                "description TEXT," +
                "book_id INTEGER," +
                "chapter INTEGER," +
                "verse INTEGER," +
                "category TEXT" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_PARABLES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "title TEXT NOT NULL," +
                "description TEXT," +
                "book_id INTEGER," +
                "chapter INTEGER," +
                "verse INTEGER," +
                "theme TEXT" +
                ");");

        db.execSQL("CREATE TABLE " + TABLE_FIGURES + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "meaning TEXT," +
                "description TEXT," +
                "role TEXT," +
                "references TEXT," +
                "family TEXT," +
                "events TEXT" +
                ");");

        db.execSQL("CREATE INDEX idx_topics_name ON " + TABLE_TOPICS + "(name);");
        db.execSQL("CREATE INDEX idx_topic_verses_topic ON " + TABLE_TOPIC_VERSES + "(topic_id);");
        db.execSQL("CREATE INDEX idx_figures_name ON " + TABLE_FIGURES + "(name);");
        db.execSQL("CREATE INDEX idx_prophecies_book ON " + TABLE_PROPHEcies + "(book_id, chapter);");
        db.execSQL("CREATE INDEX idx_miracles_book ON " + TABLE_MIRACLES + "(book_id, chapter);");
        db.execSQL("CREATE INDEX idx_parables_book ON " + TABLE_PARABLES + "(book_id, chapter);");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        // Future migrations
    }
}
