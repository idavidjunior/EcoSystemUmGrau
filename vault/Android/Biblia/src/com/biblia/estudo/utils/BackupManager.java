package com.biblia.estudo.utils;

import android.content.Context;
import android.content.SharedPreferences;

import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.data.FavoriteDao;
import com.biblia.estudo.data.NoteDao;
import com.biblia.estudo.data.ReadingProgressDao;
import com.biblia.estudo.model.Favorite;
import com.biblia.estudo.model.UserNote;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class BackupManager {

    private Context context;
    private NoteDao noteDao;
    private FavoriteDao favoriteDao;
    private ReadingProgressDao progressDao;

    public BackupManager(Context context) {
        this.context = context;
        this.noteDao = new NoteDao(BibliaApplication.getDatabaseManager().getBibleDatabase());
        this.favoriteDao = new FavoriteDao(BibliaApplication.getDatabaseManager().getBibleDatabase());
        this.progressDao = new ReadingProgressDao(BibliaApplication.getDatabaseManager().getBibleDatabase());
    }

    public String exportToJson() throws Exception {
        JSONObject backup = new JSONObject();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.getDefault());

        backup.put("export_date", sdf.format(new Date()));
        backup.put("app_version", "1.0.0");

        JSONArray notesArray = new JSONArray();
        List<UserNote> notes = noteDao.getAll();
        for (UserNote note : notes) {
            JSONObject n = new JSONObject();
            n.put("book_id", note.getBookId());
            n.put("chapter", note.getChapter());
            n.put("verse_number", note.getVerseNumber());
            n.put("content", note.getContent());
            n.put("color", note.getColor());
            n.put("created_at", note.getCreatedAt().getTime());
            n.put("updated_at", note.getUpdatedAt().getTime());
            notesArray.put(n);
        }
        backup.put("notes", notesArray);

        JSONArray favsArray = new JSONArray();
        List<Favorite> favorites = favoriteDao.getAll();
        for (Favorite fav : favorites) {
            JSONObject f = new JSONObject();
            f.put("book_id", fav.getBookId());
            f.put("chapter", fav.getChapter());
            f.put("verse_number", fav.getVerseNumber());
            f.put("verse_text", fav.getVerseText());
            f.put("book_name", fav.getBookName());
            f.put("tags", fav.getTags());
            f.put("color", fav.getColor());
            f.put("created_at", fav.getCreatedAt().getTime());
            favsArray.put(f);
        }
        backup.put("favorites", favsArray);

        JSONObject prefs = new JSONObject();
        SharedPreferences sp = BibliaApplication.getAppPreferences();
        prefs.put("theme", sp.getInt(BibliaApplication.KEY_THEME, 0));
        prefs.put("font_size", sp.getInt(BibliaApplication.KEY_FONT_SIZE, 16));
        prefs.put("font_family", sp.getInt(BibliaApplication.KEY_FONT_FAMILY, 0));
        prefs.put("line_spacing", sp.getFloat(BibliaApplication.KEY_LINE_SPACING, 1.5f));
        prefs.put("show_verse_numbers", sp.getBoolean(BibliaApplication.KEY_SHOW_VERSE_NUMBERS, true));
        prefs.put("show_notes", sp.getBoolean(BibliaApplication.KEY_SHOW_NOTES, true));
        prefs.put("show_commentaries", sp.getBoolean(BibliaApplication.KEY_SHOW_COMMENTARIES, true));
        prefs.put("show_cross_refs", sp.getBoolean(BibliaApplication.KEY_SHOW_CROSS_REFS, true));
        prefs.put("scroll_mode", sp.getInt(BibliaApplication.KEY_SCROLL_MODE, 0));
        backup.put("preferences", prefs);

        String fileName = "biblia_backup_" + sdf.format(new Date()) + ".json";
        File exportDir = new File(context.getExternalFilesDir(null), "backups");
        if (!exportDir.exists()) exportDir.mkdirs();

        File file = new File(exportDir, fileName);
        FileOutputStream fos = new FileOutputStream(file);
        OutputStreamWriter writer = new OutputStreamWriter(fos, StandardCharsets.UTF_8);
        writer.write(backup.toString(4));
        writer.flush();
        writer.close();
        fos.close();

        return file.getAbsolutePath();
    }

    public void importFromJson(File file) throws Exception {
        FileInputStream fis = new FileInputStream(file);
        BufferedReader reader = new BufferedReader(new InputStreamReader(fis, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();

        JSONObject backup = new JSONObject(sb.toString());

        if (backup.has("notes")) {
            JSONArray notesArray = backup.getJSONArray("notes");
            for (int i = 0; i < notesArray.length(); i++) {
                JSONObject n = notesArray.getJSONObject(i);
                UserNote note = new UserNote();
                note.setBookId(n.getLong("book_id"));
                note.setChapter(n.getInt("chapter"));
                note.setVerseNumber(n.getInt("verse_number"));
                note.setContent(n.getString("content"));
                note.setColor(n.getInt("color"));
                note.setCreatedAt(new Date(n.getLong("created_at")));
                note.setUpdatedAt(new Date(n.getLong("updated_at")));
                noteDao.insert(note);
            }
        }

        if (backup.has("favorites")) {
            JSONArray favsArray = backup.getJSONArray("favorites");
            for (int i = 0; i < favsArray.length(); i++) {
                JSONObject f = favsArray.getJSONObject(i);
                Favorite fav = new Favorite();
                fav.setBookId(f.getLong("book_id"));
                fav.setChapter(f.getInt("chapter"));
                fav.setVerseNumber(f.getInt("verse_number"));
                fav.setVerseText(f.getString("verse_text"));
                fav.setBookName(f.getString("book_name"));
                fav.setTags(f.optString("tags"));
                fav.setColor(f.getInt("color"));
                fav.setCreatedAt(new Date(f.getLong("created_at")));
                favoriteDao.insert(fav);
            }
        }

        if (backup.has("preferences")) {
            JSONObject prefs = backup.getJSONObject("preferences");
            SharedPreferences.Editor editor = BibliaApplication.getAppPreferences().edit();
            editor.putInt(BibliaApplication.KEY_THEME, prefs.optInt("theme", 0));
            editor.putInt(BibliaApplication.KEY_FONT_SIZE, prefs.optInt("font_size", 16));
            editor.putInt(BibliaApplication.KEY_FONT_FAMILY, prefs.optInt("font_family", 0));
            editor.putFloat(BibliaApplication.KEY_LINE_SPACING, (float) prefs.optDouble("line_spacing", 1.5));
            editor.putBoolean(BibliaApplication.KEY_SHOW_VERSE_NUMBERS, prefs.optBoolean("show_verse_numbers", true));
            editor.putBoolean(BibliaApplication.KEY_SHOW_NOTES, prefs.optBoolean("show_notes", true));
            editor.putBoolean(BibliaApplication.KEY_SHOW_COMMENTARIES, prefs.optBoolean("show_commentaries", true));
            editor.putBoolean(BibliaApplication.KEY_SHOW_CROSS_REFS, prefs.optBoolean("show_cross_refs", true));
            editor.putInt(BibliaApplication.KEY_SCROLL_MODE, prefs.optInt("scroll_mode", 0));
            editor.apply();
        }
    }
}
