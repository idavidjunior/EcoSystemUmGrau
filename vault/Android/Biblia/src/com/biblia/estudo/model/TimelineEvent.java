package com.biblia.estudo.model;

import java.io.Serializable;

public class TimelineEvent implements Serializable {
    private long id;
    private String title;
    private String description;
    private int yearStart;
    private int yearEnd;
    private String period;
    private String category;
    private String bibleReference;
    private long relatedBookId;
    private String iconName;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getYearStart() { return yearStart; }
    public void setYearStart(int yearStart) { this.yearStart = yearStart; }

    public int getYearEnd() { return yearEnd; }
    public void setYearEnd(int yearEnd) { this.yearEnd = yearEnd; }

    public String getPeriod() { return period; }
    public void setPeriod(String period) { this.period = period; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getBibleReference() { return bibleReference; }
    public void setBibleReference(String bibleReference) { this.bibleReference = bibleReference; }

    public long getRelatedBookId() { return relatedBookId; }
    public void setRelatedBookId(long relatedBookId) { this.relatedBookId = relatedBookId; }

    public String getIconName() { return iconName; }
    public void setIconName(String iconName) { this.iconName = iconName; }
}
