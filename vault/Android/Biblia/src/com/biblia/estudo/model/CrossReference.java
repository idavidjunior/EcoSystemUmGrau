package com.biblia.estudo.model;

import java.io.Serializable;

public class CrossReference implements Serializable {
    private long id;
    private long sourceBookId;
    private int sourceChapter;
    private int sourceVerse;
    private long targetBookId;
    private int targetChapter;
    private int targetVerse;
    private String targetVerseText;
    private String targetBookName;
    private String notes;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public long getSourceBookId() { return sourceBookId; }
    public void setSourceBookId(long sourceBookId) { this.sourceBookId = sourceBookId; }

    public int getSourceChapter() { return sourceChapter; }
    public void setSourceChapter(int sourceChapter) { this.sourceChapter = sourceChapter; }

    public int getSourceVerse() { return sourceVerse; }
    public void setSourceVerse(int sourceVerse) { this.sourceVerse = sourceVerse; }

    public long getTargetBookId() { return targetBookId; }
    public void setTargetBookId(long targetBookId) { this.targetBookId = targetBookId; }

    public int getTargetChapter() { return targetChapter; }
    public void setTargetChapter(int targetChapter) { this.targetChapter = targetChapter; }

    public int getTargetVerse() { return targetVerse; }
    public void setTargetVerse(int targetVerse) { this.targetVerse = targetVerse; }

    public String getTargetVerseText() { return targetVerseText; }
    public void setTargetVerseText(String targetVerseText) { this.targetVerseText = targetVerseText; }

    public String getTargetBookName() { return targetBookName; }
    public void setTargetBookName(String targetBookName) { this.targetBookName = targetBookName; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }

    public String getTargetReference() {
        return targetBookName + " " + targetChapter + ":" + targetVerse;
    }
}
