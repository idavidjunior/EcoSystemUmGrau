package com.biblia.estudo.model;

import java.io.Serializable;

public class BiblicalFigure implements Serializable {
    private long id;
    private String name;
    private String meaningOfName;
    private String description;
    private String role; // prophet, king, apostle, judge, etc.
    private String bibleReferences;
    private String family;
    private String events;
    private String relatedFigures;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getMeaningOfName() { return meaningOfName; }
    public void setMeaningOfName(String meaningOfName) { this.meaningOfName = meaningOfName; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public String getBibleReferences() { return bibleReferences; }
    public void setBibleReferences(String bibleReferences) { this.bibleReferences = bibleReferences; }

    public String getFamily() { return family; }
    public void setFamily(String family) { this.family = family; }

    public String getEvents() { return events; }
    public void setEvents(String events) { this.events = events; }

    public String getRelatedFigures() { return relatedFigures; }
    public void setRelatedFigures(String relatedFigures) { this.relatedFigures = relatedFigures; }
}
