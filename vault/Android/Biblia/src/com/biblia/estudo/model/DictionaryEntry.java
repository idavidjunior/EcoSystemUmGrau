package com.biblia.estudo.model;

import java.io.Serializable;

public class DictionaryEntry implements Serializable {
    private long id;
    private String word;
    private String transliteration;
    private String originalLanguage; // hebrew, greek, aramaic
    private String strongNumber;
    private String definition;
    private String etymology;
    private String usageNotes;
    private String relatedWords;
    private String occurrences;

    public long getId() { return id; }
    public void setId(long id) { this.id = id; }

    public String getWord() { return word; }
    public void setWord(String word) { this.word = word; }

    public String getTransliteration() { return transliteration; }
    public void setTransliteration(String transliteration) { this.transliteration = transliteration; }

    public String getOriginalLanguage() { return originalLanguage; }
    public void setOriginalLanguage(String originalLanguage) { this.originalLanguage = originalLanguage; }

    public String getStrongNumber() { return strongNumber; }
    public void setStrongNumber(String strongNumber) { this.strongNumber = strongNumber; }

    public String getDefinition() { return definition; }
    public void setDefinition(String definition) { this.definition = definition; }

    public String getEtymology() { return etymology; }
    public void setEtymology(String etymology) { this.etymology = etymology; }

    public String getUsageNotes() { return usageNotes; }
    public void setUsageNotes(String usageNotes) { this.usageNotes = usageNotes; }

    public String getRelatedWords() { return relatedWords; }
    public void setRelatedWords(String relatedWords) { this.relatedWords = relatedWords; }

    public String getOccurrences() { return occurrences; }
    public void setOccurrences(String occurrences) { this.occurrences = occurrences; }
}
