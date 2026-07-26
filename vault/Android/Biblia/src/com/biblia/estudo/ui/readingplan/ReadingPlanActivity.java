package com.biblia.estudo.ui.readingplan;

import android.app.Activity;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;

import java.util.ArrayList;
import java.util.List;

public class ReadingPlanActivity extends Activity {

    private static final String PREFS_KEY_PREFIX = "reading_plan_";
    private static final String PREFS_KEY_PLAN_TYPE = "reading_plan_type";

    private ListView planList;
    private ProgressBar progressBar;
    private TextView progressText;
    private RadioGroup planSelector;
    private LayoutInflater inflater;

    private int currentPlanDays = 365;
    private List<PlanDay> days = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_reading_plan);
        inflater = LayoutInflater.from(this);

        planList = findViewById(R.id.planList);
        progressBar = findViewById(R.id.progressBar);
        progressText = findViewById(R.id.progressText);
        planSelector = findViewById(R.id.planSelector);

        int savedPlan = getPreferences(MODE_PRIVATE).getInt(PREFS_KEY_PLAN_TYPE, 365);
        switch (savedPlan) {
            case 90: planSelector.check(R.id.planThreeMonths); break;
            case 180: planSelector.check(R.id.planSixMonths); break;
            default: planSelector.check(R.id.planOneYear); break;
        }
        loadPlan(savedPlan);

        planSelector.setOnCheckedChangeListener((group, checkedId) -> {
            int days;
            if (checkedId == R.id.planThreeMonths) days = 90;
            else if (checkedId == R.id.planSixMonths) days = 180;
            else days = 365;
            getPreferences(MODE_PRIVATE).edit().putInt(PREFS_KEY_PLAN_TYPE, days).apply();
            loadPlan(days);
        });
    }

    private void loadPlan(int totalDays) {
        currentPlanDays = totalDays;
        days.clear();

        String[] bookNames;
        int[] chapterCounts;
        SharedPreferences prefs = getPreferences(MODE_PRIVATE);

        try {
            SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
            Cursor c = db.rawQuery("SELECT name, chapter_count FROM books ORDER BY book_order", null);
            List<String> names = new ArrayList<>();
            List<Integer> counts = new ArrayList<>();
            while (c.moveToNext()) {
                names.add(c.getString(0));
                counts.add(c.getInt(1));
            }
            c.close();
            bookNames = names.toArray(new String[0]);
            chapterCounts = new int[counts.size()];
            for (int i = 0; i < counts.size(); i++) chapterCounts[i] = counts.get(i);
        } catch (Exception e) {
            bookNames = new String[]{"Gênesis", "Êxodo", "Mateus", "Salmos"};
            chapterCounts = new int[]{50, 40, 28, 150};
        }

        int totalChapters = 0;
        for (int ch : chapterCounts) totalChapters += ch;

        int chaptersPerDay = Math.max(1, totalChapters / totalDays);

        int bookIdx = 0;
        int chapterInBook = 1;
        StringBuilder currentReading = new StringBuilder();
        int dayChapters = 0;

        for (int day = 1; day <= totalDays; day++) {
            PlanDay planDay = new PlanDay();
            planDay.dayNumber = day;
            planDay.completed = prefs.getBoolean(PREFS_KEY_PREFIX + day, false);
            planDay.reading = "";

            dayChapters = 0;
            currentReading.setLength(0);

            while (bookIdx < bookNames.length && dayChapters < chaptersPerDay) {
                if (currentReading.length() > 0) currentReading.append("; ");
                currentReading.append(bookNames[bookIdx]).append(" ").append(chapterInBook);

                dayChapters++;
                chapterInBook++;

                if (chapterInBook > chapterCounts[bookIdx]) {
                    chapterInBook = 1;
                    bookIdx++;
                }
            }

            if (currentReading.length() == 0 && bookIdx >= bookNames.length) {
                planDay.reading = "Concluído!";
            } else {
                planDay.reading = currentReading.toString();
            }

            days.add(planDay);
        }

        planList.setAdapter(new PlanAdapter());
        updateProgress();
    }

    private void updateProgress() {
        int completed = 0;
        for (PlanDay d : days) {
            if (d.completed) completed++;
        }
        int progress = days.size() > 0 ? (completed * 100 / days.size()) : 0;
        progressBar.setProgress(progress);
        progressText.setText(completed + " de " + days.size() + " dias concluídos (" + progress + "%)");
    }

    private class PlanAdapter extends BaseAdapter {
        @Override public int getCount() { return days.size(); }
        @Override public Object getItem(int pos) { return days.get(pos); }
        @Override public long getItemId(int pos) { return pos; }

        @Override
        public View getView(int pos, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = inflater.inflate(R.layout.list_item_book, parent, false);
            }
            PlanDay d = days.get(pos);
            TextView numView = convertView.findViewById(R.id.bookNumber);
            TextView nameView = convertView.findViewById(R.id.bookName);

            numView.setText(String.valueOf(d.dayNumber));
            numView.setTextSize(14);
            numView.setWidth(0);

            if (d.completed) {
                nameView.setText("✓ " + d.reading);
                nameView.setTextColor(0xFF16A34A);
                convertView.setBackgroundColor(0x0F16A34A);
            } else {
                nameView.setText(d.reading);
                nameView.setTextColor(0xFF1A1A2E);
                convertView.setBackgroundColor(0);
            }

            convertView.setOnClickListener(v -> {
                d.completed = !d.completed;
                getPreferences(MODE_PRIVATE).edit()
                        .putBoolean(PREFS_KEY_PREFIX + d.dayNumber, d.completed).apply();
                updateProgress();
                notifyDataSetChanged();
            });

            return convertView;
        }
    }

    static class PlanDay {
        int dayNumber;
        String reading;
        boolean completed;
    }
}
