package com.biblia.estudo.model;

import java.io.Serializable;
import java.util.Date;

public class ReadingPlan implements Serializable {
    private long id;
    private String name;
    private String description;
    private int durationDays;
    private String category;
    private boolean isActive;
    private Date startDate;
    private int currentDay;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getDurationDays() { return durationDays; }
    public void setDurationDays(int durationDays) { this.durationDays = durationDays; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public boolean isActive() { return isActive; }
    public void setActive(boolean active) { isActive = active; }

    public Date getStartDate() { return startDate; }
    public void setStartDate(Date startDate) { this.startDate = startDate; }

    public int getCurrentDay() { return currentDay; }
    public void setCurrentDay(int currentDay) { this.currentDay = currentDay; }

    public double getProgressPercent() {
        if (durationDays <= 0) return 0;
        return (double) currentDay / durationDays * 100;
    }
}
