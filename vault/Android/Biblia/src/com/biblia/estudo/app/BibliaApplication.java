package com.biblia.estudo.app;

import android.app.Application;
import android.content.SharedPreferences;
import android.preference.PreferenceManager;

import com.biblia.estudo.data.DatabaseManager;

public class BibliaApplication extends Application {

    private static BibliaApplication instance;
    private DatabaseManager databaseManager;
    private SharedPreferences preferences;
    private ThemeManager themeManager;

    public static final String PREFS_NAME = "biblia_estudo_prefs";
    public static final String KEY_THEME = "theme";
    public static final String KEY_FONT_SIZE = "font_size";
    public static final String KEY_FONT_FAMILY = "font_family";
    public static final String KEY_LINE_SPACING = "line_spacing";
    public static final String KEY_SHOW_VERSE_NUMBERS = "show_verse_numbers";
    public static final String KEY_SHOW_NOTES = "show_notes";
    public static final String KEY_SHOW_COMMENTARIES = "show_commentaries";
    public static final String KEY_SHOW_CROSS_REFS = "show_cross_refs";
    public static final String KEY_SCROLL_MODE = "scroll_mode";
    public static final String KEY_MARGINS = "margins";
    public static final String KEY_LAST_BOOK = "last_book";
    public static final String KEY_LAST_CHAPTER = "last_chapter";
    public static final String KEY_LAST_VERSE = "last_verse";

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        databaseManager = DatabaseManager.getInstance(this);
        preferences = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        themeManager = new ThemeManager(this, preferences);
    }

    public static BibliaApplication getInstance() {
        return instance;
    }

    public static DatabaseManager getDatabaseManager() {
        return instance.databaseManager;
    }

    public static SharedPreferences getAppPreferences() {
        return instance.preferences;
    }

    public static ThemeManager getThemeManager() {
        return instance.themeManager;
    }

    @Override
    public void onTerminate() {
        if (databaseManager != null) {
            databaseManager.closeAll();
        }
        super.onTerminate();
    }
}
