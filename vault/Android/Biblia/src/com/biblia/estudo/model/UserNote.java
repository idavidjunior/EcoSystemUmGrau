package com.biblia.estudo.model;

import java.io.Serializable;
import java.util.Date;

public class UserNote implements Serializable {
    private long id;
    private long bookId;
    private int chapter;
    private int verseNumber;
    private String content;
    private Date createdAt;
    private Date updatedAt;
    private int color;
    private boolean isHighlight;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getBookId() { return bookId; }
    public void setBookId(long bookId) { this.bookId = bookId; }

    public int getChapter() { return chapter; }
    public void setChapter(int chapter) { this.chapter = chapter; }

    public int getVerseNumber() { return verseNumber; }
    public void setVerseNumber(int verseNumber) { this.verseNumber = verseNumber; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public Date getCreatedAt() { return createdAt; }
    public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }

    public Date getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Date updatedAt) { this.updatedAt = updatedAt; }

    public int getColor() { return color; }
    public void setColor(int color) { this.color = color; }

    public boolean isHighlight() { return isHighlight; }
    public void setHighlight(boolean highlight) { isHighlight = highlight; }
}
