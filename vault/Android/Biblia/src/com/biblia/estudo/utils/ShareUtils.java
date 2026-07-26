package com.biblia.estudo.utils;

import android.content.Context;
import android.content.Intent;

public class ShareUtils {

    public static void shareVerse(Context context, String reference, String text) {
        String shareText = reference + "\n\n\"" + text + "\"\n\n— " + reference +
                "\n\nCompartilhado via Bíblia de Estudo Completa";

        Intent shareIntent = new Intent(Intent.ACTION_SEND);
        shareIntent.setType("text/plain");
        shareIntent.putExtra(Intent.EXTRA_SUBJECT, reference);
        shareIntent.putExtra(Intent.EXTRA_TEXT, shareText);
        context.startActivity(Intent.createChooser(shareIntent, "Compartilhar versículo"));
    }

    public static void shareMultipleVerses(Context context, String reference, String text) {
        shareVerse(context, reference, text);
    }
}
