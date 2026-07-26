package com.biblia.estudo.ui.timeline;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;
import com.biblia.estudo.utils.NavigationHelper;

public class TimelineActivity extends Activity {

    private TextView prevPeriod;
    private TextView nextPeriod;
    private LinearLayout timelineContent;
    private int currentPeriod = 0;
    private String[] periods = {"Criação", "Patriarcas", "Êxodo", "Juízes",
            "Reino Unido", "Reino Dividido", "Exílio", "Pós-Exílio",
            "Período Intertestamentário", "Vida de Jesus", "Igreja Primitiva"};

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_timeline);

        NavigationHelper.setupBackButton(this);
        prevPeriod = findViewById(R.id.prevPeriod);
        nextPeriod = findViewById(R.id.nextPeriod);
        timelineContent = findViewById(R.id.timelineContent);

        prevPeriod.setOnClickListener(v -> {
            if (currentPeriod > 0) {
                currentPeriod--;
                loadTimeline(currentPeriod);
            }
        });

        nextPeriod.setOnClickListener(v -> {
            if (currentPeriod < periods.length - 1) {
                currentPeriod++;
                loadTimeline(currentPeriod);
            }
        });

        loadTimeline(currentPeriod);
    }

    private void loadTimeline(int periodIndex) {
        if (periodIndex < 0 || periodIndex >= periods.length) return;

        prevPeriod.setVisibility(periodIndex > 0 ? View.VISIBLE : View.INVISIBLE);
        nextPeriod.setVisibility(periodIndex < periods.length - 1 ? View.VISIBLE : View.INVISIBLE);

        String period = periods[periodIndex];
        timelineContent.removeAllViews();

        SQLiteDatabase db = BibliaApplication.getDatabaseManager().getTopicIndexDatabase();
        Cursor c = db.query("timeline_events", new String[]{"_id", "title", "year_start", "year_end", "description"},
                "period=?", new String[]{period}, null, null, "year_start ASC");

        while (c.moveToNext()) {
            String title = c.getString(c.getColumnIndexOrThrow("title"));
            int yearStart = c.getInt(c.getColumnIndexOrThrow("year_start"));
            int yearEnd = c.getInt(c.getColumnIndexOrThrow("year_end"));
            String desc = c.getString(c.getColumnIndexOrThrow("description"));

            View card = getLayoutInflater().inflate(R.layout.list_item_book, timelineContent, false);
            TextView titleView = card.findViewById(R.id.bookName);
            TextView yearView = card.findViewById(R.id.chapterCount);
            titleView.setText(title);
            String yearText = yearStart + (yearEnd > 0 ? " - " + yearEnd : "");
            yearView.setText(yearText);
            yearView.setVisibility(View.VISIBLE);
            timelineContent.addView(card);

            if (desc != null && !desc.isEmpty()) {
                TextView descView = new TextView(this);
                descView.setText(desc);
                descView.setPadding(dp(16), 0, dp(16), dp(12));
                descView.setTextSize(13);
                descView.setTextColor(getResources().getColor(R.color.text_secondary));
                timelineContent.addView(descView);
            }
        }
        c.close();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
