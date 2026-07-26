package com.biblia.estudo.data;

import android.content.Context;
import android.content.SharedPreferences;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

public class DatabaseManager {

    private static final String PREFS_NAME = "db_manager_prefs";
    private static final String KEY_DB_VERSION = "db_copied_version";
    private static final int CURRENT_DB_VERSION = 6;

    private static DatabaseManager instance;
    private Context context;
    private Map<String, SQLiteDatabase> databases;

    private BibleDatabaseHelper bibleHelper;
    private CommentaryDatabaseHelper commentaryHelper;
    private DictionaryDatabaseHelper dictionaryHelper;
    private CrossReferenceDatabaseHelper crossRefHelper;
    private TopicIndexDatabaseHelper topicHelper;

    private DatabaseManager(Context context) {
        this.context = context.getApplicationContext();
        this.databases = new HashMap<>();

        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        int copiedVersion = prefs.getInt(KEY_DB_VERSION, 0);

        if (copiedVersion < CURRENT_DB_VERSION) {
            deleteDatabase("biblia_estudo.db");
            deleteDatabase("comentarios.db");
            deleteDatabase("dicionario.db");
            deleteDatabase("referencias.db");
            deleteDatabase("indices.db");
        }

        copyPrepopulatedDb("biblia_estudo.db");
        copyPrepopulatedDb("comentarios.db");
        copyPrepopulatedDb("dicionario.db");
        copyPrepopulatedDb("referencias.db");
        copyPrepopulatedDb("indices.db");

        if (copiedVersion < CURRENT_DB_VERSION) {
            prefs.edit().putInt(KEY_DB_VERSION, CURRENT_DB_VERSION).apply();
        }

        this.bibleHelper = new BibleDatabaseHelper(context);
        this.commentaryHelper = new CommentaryDatabaseHelper(context);
        this.dictionaryHelper = new DictionaryDatabaseHelper(context);
        this.crossRefHelper = new CrossReferenceDatabaseHelper(context);
        this.topicHelper = new TopicIndexDatabaseHelper(context);
    }

    private void deleteDatabase(String dbName) {
        File dbFile = context.getDatabasePath(dbName);
        if (dbFile.exists()) {
            dbFile.delete();
        }
    }

    private void copyPrepopulatedDb(String dbName) {
        File dbFile = context.getDatabasePath(dbName);
        if (dbFile.exists()) return;

        try {
            dbFile.getParentFile().mkdirs();
            InputStream in = context.getAssets().open("databases/" + dbName);
            FileOutputStream out = new FileOutputStream(dbFile);
            byte[] buf = new byte[8192];
            int len;
            while ((len = in.read(buf)) > 0) out.write(buf, 0, len);
            in.close();
            out.close();
        } catch (Exception ignored) {}
    }

    public static synchronized DatabaseManager getInstance(Context context) {
        if (instance == null) {
            instance = new DatabaseManager(context);
        }
        return instance;
    }

    public SQLiteDatabase getBibleDatabase() {
        return getDatabase("bible", bibleHelper);
    }

    public SQLiteDatabase getCommentaryDatabase() {
        return getDatabase("commentary", commentaryHelper);
    }

    public SQLiteDatabase getDictionaryDatabase() {
        return getDatabase("dictionary", dictionaryHelper);
    }

    public SQLiteDatabase getCrossReferenceDatabase() {
        return getDatabase("cross_ref", crossRefHelper);
    }

    public SQLiteDatabase getTopicIndexDatabase() {
        return getDatabase("topic", topicHelper);
    }

    private SQLiteDatabase getDatabase(String key, SQLiteOpenHelper helper) {
        if (!databases.containsKey(key) || !databases.get(key).isOpen()) {
            databases.put(key, helper.getWritableDatabase());
        }
        return databases.get(key);
    }

    public void closeAll() {
        for (SQLiteDatabase db : databases.values()) {
            if (db != null && db.isOpen()) {
                db.close();
            }
        }
        databases.clear();
    }
}
