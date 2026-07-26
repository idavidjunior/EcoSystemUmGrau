package com.biblia.estudo.model;

import java.io.Serializable;

public class Book implements Serializable {
    private long id;
    private String name;
    private String abbreviation;
    private int testament; // 1 = OT, 2 = NT, 3 = Apocrypha
    private int category;
    private int chapterCount;
    private int order;
    private String author;
    private String historicalContext;
    private String literaryStructure;
    private String outline;
    private String mainThemes;
    private String curiosities;

    public static final int TESTAMENT_OLD = 1;
    public static final int TESTAMENT_NEW = 2;
    public static final int TESTAMENT_APOCRYPHA = 3;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getAbbreviation() { return abbreviation; }
    public void setAbbreviation(String abbreviation) { this.abbreviation = abbreviation; }

    public int getTestament() { return testament; }
    public void setTestament(int testament) { this.testament = testament; }

    public int getCategory() { return category; }
    public void setCategory(int category) { this.category = category; }

    public int getChapterCount() { return chapterCount; }
    public void setChapterCount(int chapterCount) { this.chapterCount = chapterCount; }

    public int getOrder() { return order; }
    public void setOrder(int order) { this.order = order; }

    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }

    public String getHistoricalContext() { return historicalContext; }
    public void setHistoricalContext(String historicalContext) { this.historicalContext = historicalContext; }

    public String getLiteraryStructure() { return literaryStructure; }
    public void setLiteraryStructure(String literaryStructure) { this.literaryStructure = literaryStructure; }

    public String getOutline() { return outline; }
    public void setOutline(String outline) { this.outline = outline; }

    public String getMainThemes() { return mainThemes; }
    public void setMainThemes(String mainThemes) { this.mainThemes = mainThemes; }

    public String getCuriosities() { return curiosities; }
    public void setCuriosities(String curiosities) { this.curiosities = curiosities; }
}
