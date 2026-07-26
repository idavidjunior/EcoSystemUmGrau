package com.biblia.estudo.model;

import java.io.Serializable;

public class BibleMap implements Serializable {
    private long id;
    private String name;
    private String description;
    private String imageFile;
    private String era;
    private float centerLat;
    private float centerLng;
    private float zoomLevel;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getImageFile() { return imageFile; }
    public void setImageFile(String imageFile) { this.imageFile = imageFile; }

    public String getEra() { return era; }
    public void setEra(String era) { this.era = era; }

    public float getCenterLat() { return centerLat; }
    public void setCenterLat(float centerLat) { this.centerLat = centerLat; }

    public float getCenterLng() { return centerLng; }
    public void setCenterLng(float centerLng) { this.centerLng = centerLng; }

    public float getZoomLevel() { return zoomLevel; }
    public void setZoomLevel(float zoomLevel) { this.zoomLevel = zoomLevel; }
}
