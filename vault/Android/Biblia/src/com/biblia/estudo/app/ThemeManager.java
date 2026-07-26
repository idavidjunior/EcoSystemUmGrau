package com.biblia.estudo.app;

import android.app.Activity;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.graphics.Typeface;
import android.util.TypedValue;
import android.view.View;
import android.widget.TextView;

import com.biblia.estudo.R;

public class ThemeManager {

    public static final int THEME_LIGHT = 0;
    public static final int THEME_DARK = 1;
    public static final int THEME_SEPIA = 2;
    public static final int THEME_AMOLED = 3;
    public static final int THEME_PAPER = 4;

    public static final int FONT_SERIF = 0;
    public static final int FONT_SANS_SERIF = 1;

    private SharedPreferences prefs;
    private int currentTheme;

    public ThemeManager(android.content.Context context, SharedPreferences prefs) {
        this.prefs = prefs;
        this.currentTheme = prefs.getInt(BibliaApplication.KEY_THEME, THEME_LIGHT);
    }

    public int getCurrentTheme() {
        return currentTheme;
    }

    public void setTheme(int theme) {
        this.currentTheme = theme;
        prefs.edit().putInt(BibliaApplication.KEY_THEME, theme).apply();
    }

    public void applyTheme(Activity activity) {
        switch (currentTheme) {
            case THEME_DARK:
                activity.setTheme(R.style.Theme_Biblia_Dark);
                break;
            case THEME_SEPIA:
                activity.setTheme(R.style.Theme_Biblia_Sepia);
                break;
            case THEME_AMOLED:
                activity.setTheme(R.style.Theme_Biblia_AMOLED);
                break;
            case THEME_PAPER:
                activity.setTheme(R.style.Theme_Biblia_Paper);
                break;
            default:
                activity.setTheme(R.style.Theme_Biblia);
                break;
        }
    }

    public int getThemeResourceId() {
        switch (currentTheme) {
            case THEME_DARK: return R.style.Theme_Biblia_Dark;
            case THEME_SEPIA: return R.style.Theme_Biblia_Sepia;
            case THEME_AMOLED: return R.style.Theme_Biblia_AMOLED;
            case THEME_PAPER: return R.style.Theme_Biblia_Paper;
            default: return R.style.Theme_Biblia;
        }
    }

    public int getFontSize() {
        return prefs.getInt(BibliaApplication.KEY_FONT_SIZE, 16);
    }

    public void setFontSize(int size) {
        prefs.edit().putInt(BibliaApplication.KEY_FONT_SIZE, size).apply();
    }

    public int getFontFamily() {
        return prefs.getInt(BibliaApplication.KEY_FONT_FAMILY, FONT_SERIF);
    }

    public void setFontFamily(int family) {
        prefs.edit().putInt(BibliaApplication.KEY_FONT_FAMILY, family).apply();
    }

    public float getLineSpacing() {
        return prefs.getFloat(BibliaApplication.KEY_LINE_SPACING, 1.5f);
    }

    public void setLineSpacing(float spacing) {
        prefs.edit().putFloat(BibliaApplication.KEY_LINE_SPACING, spacing).apply();
    }

    public boolean showVerseNumbers() {
        return prefs.getBoolean(BibliaApplication.KEY_SHOW_VERSE_NUMBERS, true);
    }

    public boolean showNotes() {
        return prefs.getBoolean(BibliaApplication.KEY_SHOW_NOTES, true);
    }

    public boolean showCommentaries() {
        return prefs.getBoolean(BibliaApplication.KEY_SHOW_COMMENTARIES, true);
    }

    public boolean showCrossReferences() {
        return prefs.getBoolean(BibliaApplication.KEY_SHOW_CROSS_REFS, true);
    }

    public int getScrollMode() {
        return prefs.getInt(BibliaApplication.KEY_SCROLL_MODE, 0);
    }

    public int getMargins() {
        return prefs.getInt(BibliaApplication.KEY_MARGINS, 16);
    }

    public void applyTextSettings(TextView textView) {
        int fontSize = getFontSize();
        textView.setTextSize(TypedValue.COMPLEX_UNIT_SP, fontSize);

        int fontFamily = getFontFamily();
        if (fontFamily == FONT_SERIF) {
            textView.setTypeface(Typeface.SERIF);
        } else {
            textView.setTypeface(Typeface.DEFAULT);
        }

        float spacing = getLineSpacing();
        textView.setLineSpacing(0f, spacing);
    }

    public void saveLastPosition(long bookId, int chapter, int verse) {
        prefs.edit()
                .putLong(BibliaApplication.KEY_LAST_BOOK, bookId)
                .putInt(BibliaApplication.KEY_LAST_CHAPTER, chapter)
                .putInt(BibliaApplication.KEY_LAST_VERSE, verse)
                .apply();
    }

    public long getLastBook() {
        return prefs.getLong(BibliaApplication.KEY_LAST_BOOK, -1);
    }

    public int getLastChapter() {
        return prefs.getInt(BibliaApplication.KEY_LAST_CHAPTER, 1);
    }

    public int getLastVerse() {
        return prefs.getInt(BibliaApplication.KEY_LAST_VERSE, 1);
    }

    public boolean hasLastPosition() {
        return getLastBook() > 0;
    }
}
