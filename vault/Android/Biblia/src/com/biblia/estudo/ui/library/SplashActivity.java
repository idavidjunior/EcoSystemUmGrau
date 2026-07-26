package com.biblia.estudo.ui.library;

import android.app.Activity;
import android.content.Intent;
import android.database.sqlite.SQLiteDatabase;
import android.os.AsyncTask;
import android.os.Bundle;
import android.widget.ProgressBar;
import android.widget.TextView;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;

public class SplashActivity extends Activity {

    private ProgressBar progressBar;
    private TextView statusText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setTheme(android.R.style.Theme_Material_NoActionBar);
        setContentView(R.layout.activity_splash);

        progressBar = findViewById(R.id.splashProgress);
        statusText = findViewById(R.id.splashStatus);

        new InitTask().execute();
    }

    private class InitTask extends AsyncTask<Void, Integer, Boolean> {
        @Override
        protected Boolean doInBackground(Void... params) {
            try {
                publishProgress(25);
                Thread.sleep(300);

                publishProgress(50);
                BibliaApplication.getThemeManager();

                publishProgress(75);
                SQLiteDatabase db = BibliaApplication.getDatabaseManager().getBibleDatabase();
                if (db != null) db.getVersion();

                publishProgress(100);
                Thread.sleep(400);
                return true;
            } catch (Exception e) {
                return true;
            }
        }

        @Override
        protected void onProgressUpdate(Integer... values) {
            if (statusText != null) {
                if (values[0] == 25) statusText.setText("Preparando aplicativo...");
                else if (values[0] == 50) statusText.setText("Carregando recursos...");
                else if (values[0] == 75) statusText.setText("Abrindo banco de dados...");
                else if (values[0] == 100) statusText.setText("Pronto!");
            }
            if (progressBar != null) progressBar.setProgress(values[0]);
        }

        @Override
        protected void onPostExecute(Boolean result) {
            Intent intent = new Intent(SplashActivity.this, HomeActivity.class);
            startActivity(intent);
            finish();
        }
    }
}
