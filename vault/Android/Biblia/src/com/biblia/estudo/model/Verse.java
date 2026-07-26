package com.biblia.estudo.model;

import java.io.Serializable;

public class Verse implements Serializable {
    private long id;
    private long bookId;
    private int chapter;
    private int verseNumber;
    private String text;
    private String hebrewText;
    private String greekText;
    private boolean hasCommentary;
    private boolean hasNotes;
    private boolean hasCrossReferences;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getBookId() { return bookId; }
    public void setBookId(long bookId) { this.bookId = bookId; }

    public int getChapter() { return chapter; }
    public void setChapter(int chapter) { this.chapter = chapter; }

    public int getVerseNumber() { return verseNumber; }
    public void setVerseNumber(int verseNumber) { this.verseNumber = verseNumber; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public String getHebrewText() { return hebrewText; }
    public void setHebrewText(String hebrewText) { this.hebrewText = hebrewText; }

    public String getGreekText() { return greekText; }
    public void setGreekText(String greekText) { this.greekText = greekText; }

    public boolean hasCommentary() { return hasCommentary; }
    public void setHasCommentary(boolean hasCommentary) { this.hasCommentary = hasCommentary; }

    public boolean hasNotes() { return hasNotes; }
    public void setHasNotes(boolean hasNotes) { this.hasNotes = hasNotes; }

    public boolean hasCrossReferences() { return hasCrossReferences; }
    public void setHasCrossReferences(boolean hasCrossReferences) { this.hasCrossReferences = hasCrossReferences; }

    public String getReference() {
        return bookId + " " + chapter + ":" + verseNumber;
    }
}
