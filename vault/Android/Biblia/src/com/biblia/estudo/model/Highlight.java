package com.biblia.estudo.model;

public class Highlight {
    private long id;
    private long bookId;
    private int chapter;
    private int verseStart;
    private int verseEnd;
    private String color;
    private long createdAt;

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
    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }
    public long getCreatedAt() { return createdAt; }
    public void setCreatedAt(long createdAt) { this.createdAt = createdAt; }
}
