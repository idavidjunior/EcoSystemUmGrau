package com.biblia.estudo.ui.favorites;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.data.FavoriteDao;
import com.biblia.estudo.model.Favorite;
import com.biblia.estudo.ui.bible.BibleReaderActivity;

import java.util.List;

public class FavoritesActivity extends Activity {

    private ListView favoritesList;
    private TextView emptyView;
    private FavoriteDao favoriteDao;
    private FavoritesAdapter adapter;
    private List<Favorite> favorites;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_favorites);

        favoritesList = findViewById(R.id.favoritesList);
        emptyView = findViewById(R.id.emptyView);

        favoriteDao = new FavoriteDao(BibliaApplication.getDatabaseManager().getBibleDatabase());

        loadFavorites();
    }

    private void loadFavorites() {
        favorites = favoriteDao.getAll();
        if (favorites.isEmpty()) {
            emptyView.setVisibility(View.VISIBLE);
            favoritesList.setVisibility(View.GONE);
        } else {
            emptyView.setVisibility(View.GONE);
            favoritesList.setVisibility(View.VISIBLE);
            adapter = new FavoritesAdapter(this, favorites);
            favoritesList.setAdapter(adapter);

            favoritesList.setOnItemClickListener(new AdapterView.OnItemClickListener() {
                @Override
                public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                    Favorite fav = adapter.getItem(position);
                    Intent intent = new Intent(FavoritesActivity.this, BibleReaderActivity.class);
                    intent.putExtra("book_id", fav.getBookId());
                    intent.putExtra("book_name", fav.getBookName());
                    intent.putExtra("chapter", fav.getChapter());
                    intent.putExtra("verse", fav.getVerseNumber());
                    startActivity(intent);
                }
            });
        }
    }

    public void removeFavorite(int position) {
        if (favorites != null && position >= 0 && position < favorites.size()) {
            Favorite fav = favorites.get(position);
            favoriteDao.delete(fav.getId());
            favorites.remove(position);
            adapter.notifyDataSetChanged();
            if (favorites.isEmpty()) {
                emptyView.setVisibility(View.VISIBLE);
                favoritesList.setVisibility(View.GONE);
            }
        }
    }
}
