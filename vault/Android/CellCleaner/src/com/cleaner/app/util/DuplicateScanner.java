package com.cleaner.app.util;

import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class DuplicateScanner {

    public static class DuplicateGroup {
        public long fileSize;
        public List<File> files;

        public DuplicateGroup(File first, long size) {
            this.fileSize = size;
            this.files = new ArrayList<>();
            this.files.add(first);
        }
    }

    public static List<DuplicateGroup> findDuplicates(File rootDir, boolean useHash) {
        Map<String, DuplicateGroup> groups = new HashMap<>();
        walkDir(rootDir, groups, useHash);
        List<DuplicateGroup> result = new ArrayList<>();
        for (DuplicateGroup g : groups.values()) {
            if (g.files.size() > 1) result.add(g);
        }
        return result;
    }

    private static void walkDir(File dir, Map<String, DuplicateGroup> groups, boolean useHash) {
        if (dir == null || !dir.exists()) return;
        File[] files = dir.listFiles();
        if (files == null) return;

        for (File f : files) {
            try {
                if (f.isDirectory()) {
                    String name = f.getName().toLowerCase();
                    if (!name.startsWith(".") && !name.equals("android")) {
                        walkDir(f, groups, useHash);
                    }
                } else if (f.isFile() && f.length() > 0) {
                    String key = useHash ? sha1Hash(f) : (f.getName() + "|" + f.length());
                    if (key != null) {
                        DuplicateGroup group = groups.get(key);
                        if (group != null) {
                            group.files.add(f);
                        } else {
                            groups.put(key, new DuplicateGroup(f, f.length()));
                        }
                    }
                }
            } catch (Exception e) {}
        }
    }

    public static String sha1Hash(File file) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            FileInputStream fis = new FileInputStream(file);
            byte[] buf = new byte[8192];
            int len;
            while ((len = fis.read(buf)) > 0) md.update(buf, 0, len);
            fis.close();
            StringBuilder sb = new StringBuilder();
            for (byte b : md.digest()) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) { return null; }
    }

    public static long getTotalWasted(List<DuplicateGroup> groups) {
        long total = 0;
        for (DuplicateGroup g : groups) {
            total += g.fileSize * (g.files.size() - 1);
        }
        return total;
    }
}