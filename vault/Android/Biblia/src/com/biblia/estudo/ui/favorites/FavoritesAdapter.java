package com.biblia.estudo.ui.favorites;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.model.Favorite;

import java.util.List;

public class FavoritesAdapter extends BaseAdapter {

    private Context context;
    private List<Favorite> favorites;
    private LayoutInflater inflater;

    public FavoritesAdapter(Context context, List<Favorite> favorites) {
        this.context = context;
        this.favorites = favorites;
        this.inflater = LayoutInflater.from(context);
    }

    @Override
    public int getCount() { return favorites.size(); }

    @Override
    public Favorite getItem(int position) { return favorites.get(position); }

    @Override
    public long getItemId(int position) { return favorites.get(position).getId(); }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder holder;
        if (convertView == null) {
            convertView = inflater.inflate(R.layout.list_item_favorite, parent, false);
            holder = new ViewHolder();
            holder.favRef = convertView.findViewById(R.id.favRef);
            holder.favSnippet = convertView.findViewById(R.id.favSnippet);
            holder.btnRemove = convertView.findViewById(R.id.btnRemoveFav);
            convertView.setTag(holder);
        } else {
            holder = (ViewHolder) convertView.getTag();
        }

        Favorite fav = favorites.get(position);
        holder.favRef.setText(fav.getReference());
        holder.favSnippet.setText(fav.getVerseText());

        final int pos = position;
        holder.btnRemove.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (context instanceof FavoritesActivity) {
                    ((FavoritesActivity) context).removeFavorite(pos);
                }
            }
        });

        return convertView;
    }

    static class ViewHolder {
        TextView favRef;
        TextView favSnippet;
        TextView btnRemove;
    }
}
