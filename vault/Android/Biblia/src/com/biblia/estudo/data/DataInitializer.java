package com.biblia.estudo.data;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteStatement;

public class DataInitializer {

    public static final String[][] OLD_TESTAMENT_BOOKS = {
            {"Gênesis", "Gn", "0", "50"},
            {"Êxodo", "Ex", "0", "40"},
            {"Levítico", "Lv", "0", "27"},
            {"Números", "Nm", "0", "36"},
            {"Deuteronômio", "Dt", "0", "34"},
            {"Josué", "Js", "1", "24"},
            {"Juízes", "Jz", "1", "21"},
            {"Rute", "Rt", "1", "4"},
            {"1 Samuel", "1Sm", "1", "31"},
            {"2 Samuel", "2Sm", "1", "24"},
            {"1 Reis", "1Rs", "1", "22"},
            {"2 Reis", "2Rs", "1", "25"},
            {"1 Crônicas", "1Cr", "1", "29"},
            {"2 Crônicas", "2Cr", "1", "36"},
            {"Esdras", "Ed", "1", "10"},
            {"Neemias", "Ne", "1", "13"},
            {"Ester", "Et", "1", "10"},
            {"Jó", "Jó", "2", "42"},
            {"Salmos", "Sl", "2", "150"},
            {"Provérbios", "Pv", "2", "31"},
            {"Eclesiastes", "Ec", "2", "12"},
            {"Cânticos", "Ct", "2", "8"},
            {"Isaías", "Is", "3", "66"},
            {"Jeremias", "Jr", "3", "52"},
            {"Lamentações", "Lm", "3", "5"},
            {"Ezequiel", "Ez", "3", "48"},
            {"Daniel", "Dn", "3", "12"},
            {"Oseias", "Os", "4", "14"},
            {"Joel", "Jl", "4", "3"},
            {"Amós", "Am", "4", "9"},
            {"Obadias", "Ob", "4", "1"},
            {"Jonas", "Jn", "4", "4"},
            {"Miqueias", "Mq", "4", "7"},
            {"Naum", "Na", "4", "3"},
            {"Habacuque", "Hc", "4", "3"},
            {"Sofonias", "Sf", "4", "3"},
            {"Ageu", "Ag", "4", "2"},
            {"Zacarias", "Zc", "4", "14"},
            {"Malaquias", "Ml", "4", "4"}
    };

    public static final String[][] NEW_TESTAMENT_BOOKS = {
            {"Mateus", "Mt", "5", "28"},
            {"Marcos", "Mc", "5", "16"},
            {"Lucas", "Lc", "5", "24"},
            {"João", "Jo", "5", "21"},
            {"Atos", "At", "6", "28"},
            {"Romanos", "Rm", "7", "16"},
            {"1 Coríntios", "1Co", "7", "16"},
            {"2 Coríntios", "2Co", "7", "13"},
            {"Gálatas", "Gl", "7", "6"},
            {"Efésios", "Ef", "7", "6"},
            {"Filipenses", "Fp", "7", "4"},
            {"Colossenses", "Cl", "7", "4"},
            {"1 Tessalonicenses", "1Ts", "7", "5"},
            {"2 Tessalonicenses", "2Ts", "7", "3"},
            {"1 Timóteo", "1Tm", "7", "6"},
            {"2 Timóteo", "2Tm", "7", "4"},
            {"Tito", "Tt", "7", "3"},
            {"Filemom", "Fm", "7", "1"},
            {"Hebreus", "Hb", "8", "13"},
            {"Tiago", "Tg", "8", "5"},
            {"1 Pedro", "1Pe", "8", "5"},
            {"2 Pedro", "2Pe", "8", "3"},
            {"1 João", "1Jo", "8", "5"},
            {"2 João", "2Jo", "8", "1"},
            {"3 João", "3Jo", "8", "1"},
            {"Judas", "Jd", "8", "1"},
            {"Apocalipse", "Ap", "9", "22"}
    };

    public static void initializeDefaultPlans(Context context) {
        SQLiteDatabase db = DatabaseManager.getInstance(context).getBibleDatabase();

        // Verify if plans already exist
        android.database.Cursor c = db.rawQuery(
                "SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_READING_PLANS, null);
        if (c != null && c.moveToFirst() && c.getInt(0) > 0) {
            c.close();
            return;
        }
        if (c != null) c.close();

        // Insert default reading plans
        SQLiteStatement stmt = db.compileStatement(
                "INSERT INTO " + BibleDatabaseHelper.TABLE_READING_PLANS +
                        " (name, description, duration_days, category) VALUES (?, ?, ?, ?)");

        stmt.bindString(1, "Bíblia em 1 Ano");
        stmt.bindString(2, "Leia a Bíblia completa em 365 dias");
        stmt.bindLong(3, 365);
        stmt.bindString(4, "Anual");
        stmt.executeInsert();

        stmt.bindString(1, "Novo Testamento em 3 Meses");
        stmt.bindString(2, "Leia o Novo Testamento em 90 dias");
        stmt.bindLong(3, 90);
        stmt.bindString(4, "Temático");
        stmt.executeInsert();

        stmt.bindString(1, "Salmos e Provérbios em 30 Dias");
        stmt.bindString(2, "Leitura diária de Salmos e Provérbios");
        stmt.bindLong(3, 30);
        stmt.bindString(4, "Temático");
        stmt.executeInsert();

        stmt.bindString(1, "Os 4 Evangelhos em 30 Dias");
        stmt.bindString(2, "Conheça a vida de Jesus através dos evangelhos");
        stmt.bindLong(3, 30);
        stmt.bindString(4, "Temático");
        stmt.executeInsert();
    }
}
