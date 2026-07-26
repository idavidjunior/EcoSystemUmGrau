package com.biblia.estudo.ui.about;

import android.app.Activity;
import android.os.Bundle;

import com.biblia.estudo.R;
import com.biblia.estudo.app.BibliaApplication;

public class AboutActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BibliaApplication.getThemeManager().applyTheme(this);
        setContentView(R.layout.activity_about);
    }
}
