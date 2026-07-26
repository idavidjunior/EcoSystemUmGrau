package com.biblia.estudo.model;

import java.io.Serializable;

public class Commentary implements Serializable {
    private long id;
    private long bookId;
    private int chapter;
    private int verseStart;
    private int verseEnd;
    private String title;
    private String content;
    private String author;
    private String category;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getBookId() { return bookId; }
    public void setBookId(long bookId) { this.bookId = bookId; }

    public int getChapter() { return chapter; }
    public void setChapter(int chapter) { this.chapter = chapter; }

    public int getVerseStart() { return verseStart; }
    public void setVerseStart(int verseStart) { this.verseStart = verseStart; }

    public int getVerseEnd() { return verseEnd; }
    public void setVerseEnd(int verseEnd) { this.verseEnd = verseEnd; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public boolean isVerseRange() {
        return verseStart > 0 && verseEnd > 0 && verseEnd >= verseStart;
    }
}
