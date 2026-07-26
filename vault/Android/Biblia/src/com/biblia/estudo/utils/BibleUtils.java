package com.biblia.estudo.utils;

import com.biblia.estudo.model.Book;

public class BibleUtils {

    public static int getTestamentCategory(int testament) {
        return testament;
    }

    public static String getTestamentName(int testament) {
        switch (testament) {
            case Book.TESTAMENT_OLD: return "Antigo Testamento";
            case Book.TESTAMENT_NEW: return "Novo Testamento";
            case Book.TESTAMENT_APOCRYPHA: return "Livros Apócrifos";
            default: return "Desconhecido";
        }
    }

    public static String getBookCategoryName(int category) {
        switch (category) {
            case 0: return "Pentateuco";
            case 1: return "Livros Históricos";
            case 2: return "Livros Poéticos";
            case 3: return "Profetas Maiores";
            case 4: return "Profetas Menores";
            case 5: return "Evangelhos";
            case 6: return "Atos";
            case 7: return "Cartas Paulinas";
            case 8: return "Cartas Gerais";
            case 9: return "Apocalipse";
            default: return "Outros";
        }
    }

    public static String formatReference(String bookName, int chapter, int verse) {
        return bookName + " " + chapter + ":" + verse;
    }

    public static String formatReferenceRange(String bookName, int chapter, int startVerse, int endVerse) {
        if (startVerse == endVerse) {
            return formatReference(bookName, chapter, startVerse);
        }
        return bookName + " " + chapter + ":" + startVerse + "-" + endVerse;
    }
}
