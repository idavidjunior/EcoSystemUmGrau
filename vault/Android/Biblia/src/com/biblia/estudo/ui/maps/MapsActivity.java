package com.biblia.estudo.ui.maps;

import android.app.Activity;
import android.graphics.BitmapFactory;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

public class MapsActivity extends Activity {

    private LinearLayout mapsContainer;
    private List<MapItem> mapItems;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_maps);

        NavigationHelper.setupBackButton(this);
        mapsContainer = findViewById(R.id.mapsContainer);

        loadMapList();
    }

    private void loadMapList() {
        mapItems = new ArrayList<>();
        try {
            String[] files = getAssets().list("maps");
            if (files != null) {
                for (String file : files) {
                    if (file.endsWith(".jpg") || file.endsWith(".png")) {
                        MapItem item = new MapItem();
                        item.name = file.replace(".jpg", "").replace(".png", "")
                                .replace("_", " ").replace("-", " ");
                        item.fileName = file;
                        mapItems.add(item);
                    }
                }
            }
        } catch (Exception ignored) {}

        if (mapItems.isEmpty()) {
            MapItem placeholder = new MapItem();
            placeholder.name = "Nenhum mapa disponível no momento.\nOs mapas serão adicionados em uma atualização futura.";
            placeholder.fileName = null;
            mapItems.add(placeholder);
        }

        for (int i = 0; i < mapItems.size(); i++) {
            final MapItem item = mapItems.get(i);
            View card = getLayoutInflater().inflate(R.layout.list_item_book, mapsContainer, false);
            TextView titleView = card.findViewById(R.id.bookName);
            titleView.setText(item.name);
            card.setOnClickListener(v -> showMap(item));
            mapsContainer.addView(card);
        }
    }

    private void showMap(MapItem item) {
        // In a full implementation, would show a dialog or new activity with the map image
        if (item.fileName != null) {
            try {
                InputStream is = getAssets().open("maps/" + item.fileName);
                android.graphics.Bitmap bmp = BitmapFactory.decodeStream(is);
                is.close();

                android.app.AlertDialog.Builder builder = new android.app.AlertDialog.Builder(this);
                android.widget.ImageView iv = new android.widget.ImageView(this);
                iv.setImageBitmap(bmp);
                iv.setAdjustViewBounds(true);
                builder.setTitle(item.name);
                builder.setView(iv);
                builder.setPositiveButton("Fechar", null);
                builder.show();
            } catch (Exception ignored) {}
        }
    }

    static class MapItem {
        String name;
        String fileName;
    }
}
