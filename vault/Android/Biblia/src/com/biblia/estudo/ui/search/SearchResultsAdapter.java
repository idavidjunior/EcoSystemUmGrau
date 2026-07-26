package com.biblia.estudo.ui.search;

import android.content.Context;
import android.database.Cursor;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CursorAdapter;
import android.widget.TextView;

import com.biblia.estudo.R;

public class SearchResultsAdapter extends CursorAdapter {

    private LayoutInflater inflater;

    public SearchResultsAdapter(Context context, Cursor cursor) {
        super(context, cursor, 0);
        inflater = LayoutInflater.from(context);
    }

    @Override
    public View newView(Context context, Cursor cursor, ViewGroup parent) {
        View view = inflater.inflate(R.layout.list_item_result, parent, false);
        ViewHolder holder = new ViewHolder();
        holder.resultRef = view.findViewById(R.id.resultRef);
        holder.resultSnippet = view.findViewById(R.id.resultSnippet);
        view.setTag(holder);
        return view;
    }

    @Override
    public void bindView(View view, Context context, Cursor cursor) {
        ViewHolder holder = (ViewHolder) view.getTag();

        String bookName = cursor.getString(cursor.getColumnIndexOrThrow("book_name"));
        int chapter = cursor.getInt(cursor.getColumnIndexOrThrow("chapter"));
        int verse = cursor.getInt(cursor.getColumnIndexOrThrow("verse_number"));
        String text = cursor.getString(cursor.getColumnIndexOrThrow("text"));

        holder.resultRef.setText(bookName + " " + chapter + ":" + verse);
        holder.resultSnippet.setText(text);
    }

    static class ViewHolder {
        TextView resultRef;
        TextView resultSnippet;
    }
}
