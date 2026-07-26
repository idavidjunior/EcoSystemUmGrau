package com.biblia.estudo.model;

import java.io.Serializable;
import java.util.Date;

public class Favorite implements Serializable {
    private long id;
    private long bookId;
    private int chapter;
    private int verseNumber;
    private String verseText;
    private String bookName;
    private String tags;
    private int color;
    private Date createdAt;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getBookId() { return bookId; }
    public void setBookId(long bookId) { this.bookId = bookId; }

    public int getChapter() { return chapter; }
    public void setChapter(int chapter) { this.chapter = chapter; }

    public int getVerseNumber() { return verseNumber; }
    public void setVerseNumber(int verseNumber) { this.verseNumber = verseNumber; }

    public String getVerseText() { return verseText; }
    public void setVerseText(String verseText) { this.verseText = verseText; }

    public String getBookName() { return bookName; }
    public void setBookName(String bookName) { this.bookName = bookName; }

    public String getTags() { return tags; }
    public void setTags(String tags) { this.tags = tags; }

    public int getColor() { return color; }
    public void setColor(int color) { this.color = color; }

    public Date getCreatedAt() { return createdAt; }
    public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }

    public String getReference() {
        return bookName + " " + chapter + ":" + verseNumber;
    }
}
