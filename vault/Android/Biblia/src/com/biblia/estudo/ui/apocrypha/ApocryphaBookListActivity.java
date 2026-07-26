package com.biblia.estudo.ui.apocrypha;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

import java.util.ArrayList;
import java.util.List;

public class ApocryphaBookListActivity extends Activity {

    private ListView listView;
    private List<ApocryphaBook> books = new ArrayList<>();
    private ApocryphaBookAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_apocrypha_list);

        listView = findViewById(R.id.listView);
        NavigationHelper.setupBottomNav(this);

        loadBooks();
    }

    private void loadBooks() {
        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
        Cursor c = db.rawQuery("SELECT _id, name, description, book_order FROM apocrypha_books ORDER BY book_order", null);
        books.clear();
        while (c.moveToNext()) {
            ApocryphaBook b = new ApocryphaBook();
            b.id = c.getLong(0);
            b.name = c.getString(1);
            b.description = c.getString(2);
            b.order = c.getInt(3);
            books.add(b);
        }
        c.close();

        adapter = new ApocryphaBookAdapter();
        listView.setAdapter(adapter);

        listView.setOnItemClickListener((parent, view, position, id) -> {
            ApocryphaBook book = adapter.getItem(position);
            Intent intent = new Intent(ApocryphaBookListActivity.this, ApocryphaReaderActivity.class);
            intent.putExtra("book_id", book.id);
            intent.putExtra("book_name", book.name);
            startActivity(intent);
        });
    }

    static class ApocryphaBook {
        long id;
        String name;
        String description;
        int order;
    }

    private class ApocryphaBookAdapter extends BaseAdapter {
        @Override
        public int getCount() { return books.size(); }

        @Override
        public ApocryphaBook getItem(int position) { return books.get(position); }

        @Override
        public long getItemId(int position) { return books.get(position).id; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            ViewHolder holder;
            if (convertView == null) {
                convertView = getLayoutInflater().inflate(R.layout.list_item_apocrypha_book, parent, false);
                holder = new ViewHolder();
                holder.number = convertView.findViewById(R.id.bookNumber);
                holder.name = convertView.findViewById(R.id.bookName);
                holder.description = convertView.findViewById(R.id.bookDescription);
                convertView.setTag(holder);
            } else {
                holder = (ViewHolder) convertView.getTag();
            }

            ApocryphaBook book = getItem(position);
            holder.number.setText(String.valueOf(position + 1));
            holder.name.setText(book.name);
            holder.description.setText(book.description);
            return convertView;
        }

        class ViewHolder {
            TextView number;
            TextView name;
            TextView description;
        }
    }
}
