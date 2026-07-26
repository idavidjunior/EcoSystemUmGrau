package com.biblia.estudo.ui.notes;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.model.UserNote;

import java.text.SimpleDateFormat;
import java.util.List;
import java.util.Locale;

public class NotesAdapter extends BaseAdapter {

    private Context context;
    private List<UserNote> notes;
    private LayoutInflater inflater;
    private SimpleDateFormat sdf;

    public NotesAdapter(Context context, List<UserNote> notes) {
        this.context = context;
        this.notes = notes;
        this.inflater = LayoutInflater.from(context);
        this.sdf = new SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault());
    }

    @Override
    public int getCount() { return notes.size(); }

    @Override
    public UserNote getItem(int position) { return notes.get(position); }

    @Override
    public long getItemId(int position) { return notes.get(position).getId(); }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        ViewHolder holder;
        if (convertView == null) {
            convertView = inflater.inflate(R.layout.list_item_note, parent, false);
            holder = new ViewHolder();
            holder.noteRef = convertView.findViewById(R.id.noteRef);
            holder.noteContent = convertView.findViewById(R.id.noteContent);
            holder.noteDate = convertView.findViewById(R.id.noteDate);
            convertView.setTag(holder);
        } else {
            holder = (ViewHolder) convertView.getTag();
        }

        UserNote note = notes.get(position);
        String reference = "Livro " + note.getBookId() + " " + note.getChapter() + ":" + note.getVerseNumber();
        holder.noteRef.setText(reference);
        holder.noteContent.setText(note.getContent());
        holder.noteDate.setText(sdf.format(note.getUpdatedAt()));

        return convertView;
    }

    static class ViewHolder {
        TextView noteRef;
        TextView noteContent;
        TextView noteDate;
    }
}
