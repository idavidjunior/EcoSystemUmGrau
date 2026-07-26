package com.biblia.estudo.data;

import android.content.ContentValues;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;

import com.biblia.estudo.model.Book;

import java.util.ArrayList;
import java.util.List;

public class BookDao {

    private SQLiteDatabase db;

    public BookDao(SQLiteDatabase db) {
        this.db = db;
    }

    public long insert(Book book) {
        ContentValues cv = new ContentValues();
        cv.put("name", book.getName());
        cv.put("abbreviation", book.getAbbreviation());
        cv.put("testament", book.getTestament());
        cv.put("category", book.getCategory());
        cv.put("chapter_count", book.getChapterCount());
        cv.put("book_order", book.getOrder());
        cv.put("author", book.getAuthor());
        cv.put("historical_context", book.getHistoricalContext());
        cv.put("literary_structure", book.getLiteraryStructure());
        cv.put("outline", book.getOutline());
        cv.put("main_themes", book.getMainThemes());
        cv.put("curiosities", book.getCuriosities());
        return db.insert(BibleDatabaseHelper.TABLE_BOOKS, null, cv);
    }

    public Book getById(long id) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_BOOKS, null, "_id=?",
                new String[]{String.valueOf(id)}, null, null, null);
        if (c != null && c.moveToFirst()) {
            Book b = cursorToBook(c);
            c.close();
            return b;
        }
        return null;
    }

    public Book getByOrder(int order) {
        Cursor c = db.query(BibleDatabaseHelper.TABLE_BOOKS, null, "book_order=?",
                new String[]{String.valueOf(order)}, null, null, null);
        if (c != null && c.moveToFirst()) {
            Book b = cursorToBook(c);
            c.close();
            return b;
        }
        return null;
    }

    public List<Book> getByTestament(int testament) {
        List<Book> books = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_BOOKS, null,
                "testament=?", new String[]{String.valueOf(testament)},
                null, null, "book_order ASC");
        if (c != null) {
            while (c.moveToNext()) {
                books.add(cursorToBook(c));
            }
            c.close();
        }
        return books;
    }

    public List<Book> getAll() {
        List<Book> books = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_BOOKS, null,
                null, null, null, null, "testament ASC, book_order ASC");
        if (c != null) {
            while (c.moveToNext()) {
                books.add(cursorToBook(c));
            }
            c.close();
        }
        return books;
    }

    public List<Book> searchByName(String query) {
        List<Book> books = new ArrayList<>();
        Cursor c = db.query(BibleDatabaseHelper.TABLE_BOOKS, null,
                "name LIKE ?", new String[]{"%" + query + "%"},
                null, null, "book_order ASC");
        if (c != null) {
            while (c.moveToNext()) {
                books.add(cursorToBook(c));
            }
            c.close();
        }
        return books;
    }

    public int getCount(int testament) {
        Cursor c = db.rawQuery("SELECT COUNT(*) FROM " + BibleDatabaseHelper.TABLE_BOOKS +
                " WHERE testament=?", new String[]{String.valueOf(testament)});
        int count = 0;
        if (c != null && c.moveToFirst()) {
            count = c.getInt(0);
            c.close();
        }
        return count;
    }

    private Book cursorToBook(Cursor c) {
        Book b = new Book();
        b.setId(c.getLong(c.getColumnIndexOrThrow("_id")));
        b.setName(c.getString(c.getColumnIndexOrThrow("name")));
        b.setAbbreviation(c.getString(c.getColumnIndexOrThrow("abbreviation")));
        b.setTestament(c.getInt(c.getColumnIndexOrThrow("testament")));
        b.setCategory(c.getInt(c.getColumnIndexOrThrow("category")));
        b.setChapterCount(c.getInt(c.getColumnIndexOrThrow("chapter_count")));
        b.setOrder(c.getInt(c.getColumnIndexOrThrow("book_order")));
        b.setAuthor(c.getString(c.getColumnIndexOrThrow("author")));
        b.setHistoricalContext(c.getString(c.getColumnIndexOrThrow("historical_context")));
        b.setLiteraryStructure(c.getString(c.getColumnIndexOrThrow("literary_structure")));
        b.setOutline(c.getString(c.getColumnIndexOrThrow("outline")));
        b.setMainThemes(c.getString(c.getColumnIndexOrThrow("main_themes")));
        b.setCuriosities(c.getString(c.getColumnIndexOrThrow("curiosities")));
        return b;
    }
}
