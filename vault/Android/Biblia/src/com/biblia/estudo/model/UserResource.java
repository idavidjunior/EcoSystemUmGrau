package com.biblia.estudo.model;

public class UserResource {
    private long id;
    private String title;
    private String uri;
    private String mimeType;
    private long size;
    private long folderId = -1;
    private long createdAt;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getUri() { return uri; }
    public void setUri(String uri) { this.uri = uri; }
    public String getMimeType() { return mimeType; }
    public void setMimeType(String mimeType) { this.mimeType = mimeType; }
    public long getSize() { return size; }
    public void setSize(long size) { this.size = size; }
    public long getFolderId() { return folderId; }
    public void setFolderId(long folderId) { this.folderId = folderId; }
    public long getCreatedAt() { return createdAt; }
    public void setCreatedAt(long createdAt) { this.createdAt = createdAt; }

    public String getFileTypeLabel() {
        if (mimeType == null) return "OUTROS";
        if (mimeType.contains("pdf")) return "PDF";
        if (mimeType.contains("msword") || mimeType.contains("officedocument")) return "DOC";
        if (mimeType.contains("spreadsheet") || mimeType.contains("excel")) return "XLS";
        if (mimeType.contains("presentation") || mimeType.contains("powerpoint")) return "PPT";
        if (mimeType.contains("text/")) return "TXT";
        if (mimeType.contains("image/")) return "IMG";
        return "OUTROS";
    }
}
