package com.biblia.estudo.utils;

import android.app.Activity;
import android.content.Intent;
import android.view.View;

import com.biblia.estudo.R;
import com.biblia.estudo.ui.bible.BibleReaderActivity;
import com.biblia.estudo.ui.dictionary.DictionaryActivity;
import com.biblia.estudo.ui.favorites.FavoritesActivity;
import com.biblia.estudo.ui.library.HomeActivity;
import com.biblia.estudo.ui.library.LibraryActivity;
import com.biblia.estudo.ui.notes.NotesActivity;
import com.biblia.estudo.ui.readingplan.ReadingPlanActivity;
import com.biblia.estudo.ui.search.SearchActivity;
import com.biblia.estudo.ui.settings.SettingsActivity;
import com.biblia.estudo.ui.study.StudyCommentaryActivity;
import com.biblia.estudo.ui.study.TopicIndexActivity;
import com.biblia.estudo.ui.timeline.TimelineActivity;

public class NavigationHelper {

    public static void setupBottomNav(Activity activity) {
        View navHome = activity.findViewById(R.id.navHome);
        View navBible = activity.findViewById(R.id.navBible);
        View navSearch = activity.findViewById(R.id.navSearch);
        View navFavorites = activity.findViewById(R.id.navFavorites);
        View navMore = activity.findViewById(R.id.navMore);

        if (navHome != null) {
            navHome.setOnClickListener(v -> {
                if (!(activity instanceof HomeActivity)) {
                    activity.startActivity(new Intent(activity, HomeActivity.class));
                }
            });
        }
        if (navBible != null) {
            navBible.setOnClickListener(v -> {
                activity.startActivity(new Intent(activity, LibraryActivity.class));
            });
        }
        if (navSearch != null) {
            navSearch.setOnClickListener(v -> {
                activity.startActivity(new Intent(activity, SearchActivity.class));
            });
        }
        if (navFavorites != null) {
            navFavorites.setOnClickListener(v -> {
                activity.startActivity(new Intent(activity, FavoritesActivity.class));
            });
        }
        if (navMore != null) {
            navMore.setOnClickListener(v -> {
                showMoreMenu(activity);
            });
        }
    }

    private static void showMoreMenu(Activity activity) {
        String[] items = {"Dicionário", "Índice Temático", "Plano de Leitura", "Notas", "Configurações"};
        final Intent[] intents = {
                new Intent(activity, DictionaryActivity.class),
                new Intent(activity, TopicIndexActivity.class),
                new Intent(activity, ReadingPlanActivity.class),
                new Intent(activity, NotesActivity.class),
                new Intent(activity, SettingsActivity.class)
        };
        new android.app.AlertDialog.Builder(activity)
                .setTitle("Mais Recursos")
                .setItems(items, (dialog, which) -> activity.startActivity(intents[which]))
                .show();
    }

    public static void setupBackButton(Activity activity) {
        View btnBack = activity.findViewById(R.id.btnBack);
        if (btnBack != null) {
            btnBack.setOnClickListener(v -> activity.finish());
        }
    }
}
