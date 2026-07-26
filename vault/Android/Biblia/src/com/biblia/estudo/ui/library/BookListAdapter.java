package com.biblia.estudo.ui.library;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.model.Book;

import java.util.List;

public class BookListAdapter extends BaseAdapter {

    private Context context;
    private List<Book> books;
    private LayoutInflater inflater;

    public BookListAdapter(Context context, List<Book> books) {
        this.context = context;
        this.books = books;
        this.inflater = LayoutInflater.from(context);
    }

    @Override
    public int getCount() { return books.size(); }

    @Override
    public Book getItem(int position) { return books.get(position); }

    @Override
    public long getItemId(int position) { return books.get(position).getId(); }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder holder;
        if (convertView == null) {
            convertView = inflater.inflate(R.layout.list_item_book, parent, false);
            holder = new ViewHolder();
            holder.bookNumber = convertView.findViewById(R.id.bookNumber);
            holder.bookName = convertView.findViewById(R.id.bookName);
            holder.chapterCount = convertView.findViewById(R.id.chapterCount);
            convertView.setTag(holder);
        } else {
            holder = (ViewHolder) convertView.getTag();
        }

        Book book = books.get(position);
        holder.bookNumber.setText(String.valueOf(position + 1));
        holder.bookName.setText(book.getName());
        holder.chapterCount.setText(book.getChapterCount() + " capítulos");
        holder.chapterCount.setVisibility(View.VISIBLE);

        return convertView;
    }

    static class ViewHolder {
        TextView bookNumber;
        TextView bookName;
        TextView chapterCount;
    }
}
