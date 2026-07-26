package com.cleaner.app.util;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.InputStreamReader;

public class RootUtils {

    public static boolean hasRoot() {
        try {
            Process p = Runtime.getRuntime().exec("su -c id");
            final boolean[] finished = {false};
            Thread waiter = new Thread(() -> {
                try { Thread.sleep(3000); } catch (InterruptedException e) {}
                if (!finished[0]) p.destroy();
            });
            waiter.start();
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line = br.readLine();
            finished[0] = true;
            br.close();
            return line != null && line.contains("uid=0");
        } catch (Exception e) {
            return false;
        }
    }

    public static boolean hasRootSync() {
        try {
            Process p = Runtime.getRuntime().exec("su -c echo root_ok");
            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line = br.readLine();
            br.close();
            return line != null && line.contains("root_ok");
        } catch (Exception e) {
            return false;
        }
    }

    public static String runCommand(String command) {
        try {
            Process p = Runtime.getRuntime().exec("su");
            DataOutputStream os = new DataOutputStream(p.getOutputStream());
            os.writeBytes(command + "\n");
            os.writeBytes("exit\n");
            os.flush();

            final Process fp = p;
            Thread killer = new Thread(() -> {
                try { Thread.sleep(5000); } catch (InterruptedException e) {}
                try { fp.destroy(); } catch (Exception e) {}
            });
            killer.start();
            p.waitFor();

            BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line).append("\n");
            br.close();
            BufferedReader er = new BufferedReader(new InputStreamReader(p.getErrorStream()));
            StringBuilder eb = new StringBuilder();
            while ((line = er.readLine()) != null) eb.append(line).append("\n");
            er.close();
            return sb.length() > 0 ? sb.toString() : eb.toString();
        } catch (Exception e) {
            return null;
        }
    }

    public static boolean uninstallSystemPackage(String packageName) {
        String result = runCommand("pm uninstall -k --user 0 " + packageName);
        return result != null && result.contains("Success");
    }

    public static boolean disablePackage(String packageName) {
        String result = runCommand("pm disable " + packageName);
        return result != null && (result.contains("disabled") || result.contains("Success"));
    }

    public static boolean enablePackage(String packageName) {
        String result = runCommand("pm enable " + packageName);
        return result != null && (result.contains("enabled") || result.contains("Success"));
    }

    public static boolean hidePackage(String packageName) {
        String result = runCommand("pm hide " + packageName);
        return result != null && (result.contains("hidden") || result.contains("Success"));
    }

    public static boolean unhidePackage(String packageName) {
        String result = runCommand("pm unhide " + packageName);
        return result != null && (result.contains("unhidden") || result.contains("Success"));
    }

    public static boolean clearAppData(String packageName) {
        String result = runCommand("pm clear " + packageName);
        return result != null && result.contains("Success");
    }

    public static boolean forceStopApp(String packageName) {
        String result = runCommand("am force-stop " + packageName);
        return result != null && !result.contains("Error");
    }
}
