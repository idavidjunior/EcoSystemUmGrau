package com.biblia.estudo.model;

import java.io.Serializable;
import java.util.Date;

public class ReadingProgress implements Serializable {
    private long id;
    private long bookId;
    private int chapter;
    private int verse;
    private Date lastReadDate;
    private long readingTimeMillis;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getBookId() { return bookId; }
    public void setBookId(long bookId) { this.bookId = bookId; }

    public int getChapter() { return chapter; }
    public void setChapter(int chapter) { this.chapter = chapter; }

    public int getVerse() { return verse; }
    public void setVerse(int verse) { this.verse = verse; }

    public Date getLastReadDate() { return lastReadDate; }
    public void setLastReadDate(Date lastReadDate) { this.lastReadDate = lastReadDate; }

    public long getReadingTimeMillis() { return readingTimeMillis; }
    public void setReadingTimeMillis(long readingTimeMillis) { this.readingTimeMillis = readingTimeMillis; }
}
