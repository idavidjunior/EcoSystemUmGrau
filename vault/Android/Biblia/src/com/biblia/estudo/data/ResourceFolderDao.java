package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.ResourceFolder;

import java.util.ArrayList;
import java.util.List;

public class ResourceFolderDao {

    private static final String TABLE = "user_resource_folders";
    private SQLiteDatabase db;

    public ResourceFolderDao(SQLiteDatabase db) {
        this.db = db;
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE + " (" +
                "_id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "name TEXT NOT NULL," +
                "icon TEXT DEFAULT '\uD83D\uDCC1'," +
                "created_at INTEGER NOT NULL" +
                ")");
    }

    public long insert(ResourceFolder f) {
        ContentValues cv = new ContentValues();
        cv.put("name", f.getName());
        cv.put("icon", f.getIcon() != null ? f.getIcon() : "\uD83D\uDCC1");
        cv.put("created_at", System.currentTimeMillis());
        return db.insert(TABLE, null, cv);
    }

    public List<ResourceFolder> getAll() {
        List<ResourceFolder> list = new ArrayList<>();
        Cursor c = db.rawQuery(
                "SELECT f._id, f.name, f.icon, f.created_at, " +
                "(SELECT COUNT(*) FROM user_resources r WHERE r.folder_id=f._id) as cnt " +
                "FROM " + TABLE + " f ORDER BY f.name ASC", null);
        if (c != null) {
            while (c.moveToNext()) {
                ResourceFolder f = new ResourceFolder();
                f.setId(c.getLong(0));
                f.setName(c.getString(1));
                f.setIcon(c.getString(2));
                f.setCreatedAt(c.getLong(3));
                f.setItemCount(c.getInt(4));
                list.add(f);
            }
            c.close();
        }
        return list;
    }

    public ResourceFolder getById(long id) {
        Cursor c = db.rawQuery(
                "SELECT f._id, f.name, f.icon, f.created_at, " +
                "(SELECT COUNT(*) FROM user_resources r WHERE r.folder_id=f._id) as cnt " +
                "FROM " + TABLE + " f WHERE f._id=?", new String[]{String.valueOf(id)});
        if (c != null && c.moveToFirst()) {
            ResourceFolder f = new ResourceFolder();
            f.setId(c.getLong(0));
            f.setName(c.getString(1));
            f.setIcon(c.getString(2));
            f.setCreatedAt(c.getLong(3));
            f.setItemCount(c.getInt(4));
            c.close();
            return f;
        }
        return null;
    }

    public void updateName(long id, String name) {
        ContentValues cv = new ContentValues();
        cv.put("name", name);
        db.update(TABLE, cv, "_id=?", new String[]{String.valueOf(id)});
    }

    public void delete(long id) {
        db.execSQL("UPDATE user_resources SET folder_id=-1 WHERE folder_id=?", new String[]{String.valueOf(id)});
        db.delete(TABLE, "_id=?", new String[]{String.valueOf(id)});
    }
}
