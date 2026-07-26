package com.cleaner.app.util;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.IBinder;
import android.os.Parcel;
import android.os.ParcelFileDescriptor;
import android.os.RemoteException;
import android.util.Log;

public class ShizukuHelper {

    public static final String SHIZUKU_PACKAGE = "moe.shizuku.privileged.api";
    public static final String PERMISSION_API = "moe.shizuku.manager.permission.API_V23";
    public static final String ACTION_REQUEST_BINDER = "rikka.shizuku.intent.action.REQUEST_BINDER";
    public static final String EXTRA_BINDER = "moe.shizuku.privileged.api.intent.extra.BINDER";
    public static final String EXTRA_APP_UID = "moe.shizuku.privileged.api.intent.extra.APPLICATION_UID";

    private static final String TAG = "ShizukuHelper";
    private static volatile IBinder sBinder = null;
    private static volatile boolean sBinderRequested = false;
    private static Runnable sOnReceivedCallback = null;

    public static void setOnReceivedCallback(Runnable r) {
        sOnReceivedCallback = r;
    }

    public static boolean isShizukuInstalled(Context context) {
        try {
            context.getPackageManager().getPackageInfo(SHIZUKU_PACKAGE, 0);
            return true;
        } catch (PackageManager.NameNotFoundException e) {
            return false;
        }
    }

    public static boolean hasApiPermission(Context context) {
        return context.checkSelfPermission(PERMISSION_API) == PackageManager.PERMISSION_GRANTED;
    }

    public static void requestPermission(Activity activity, int requestCode) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            activity.requestPermissions(new String[]{PERMISSION_API}, requestCode);
        }
    }

    public static boolean isShizukuRunning() {
        try {
            return sBinder != null && sBinder.pingBinder();
        } catch (Exception e) {
            return false;
        }
    }

    public static boolean hasBinder() {
        return sBinder != null;
    }

    public static void clearBinder() {
        sBinder = null;
        sBinderRequested = false;
    }

    public static void resetBinderRequested() {
        sBinderRequested = false;
    }

    public static void requestBinderAsync(Context context) {
        if (sBinderRequested && sBinder != null) return;
        sBinderRequested = true;

        try {
            android.os.Binder callback = new android.os.Binder() {
                @Override
                protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
                    if (code == 1) {
                        data.setDataPosition(0);
                        IBinder shizukuBinder = data.readStrongBinder();
                        String sourceDir = data.readString();
                        Log.i(TAG, "Received Shizuku binder via callback: " + shizukuBinder + " sourceDir=" + sourceDir);
                        if (shizukuBinder != null) {
                            sBinder = shizukuBinder;
                            sBinderRequested = false;
                            Log.i(TAG, "Shizuku binder stored! ping=" + shizukuBinder.pingBinder());
                            if (sOnReceivedCallback != null) {
                                new android.os.Handler(android.os.Looper.getMainLooper()).post(sOnReceivedCallback);
                            }
                        }
                        return true;
                    }
                    return false;
                }
            };

            Bundle bundle = new Bundle();
            bundle.putBinder("binder", callback);

            Intent intent = new Intent(ACTION_REQUEST_BINDER);
            intent.setPackage(SHIZUKU_PACKAGE);
            intent.putExtra("data", bundle);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            intent.addFlags(Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS);

            Log.i(TAG, "Starting binder request intent...");
            context.startActivity(intent);
            Log.i(TAG, "Activity started for binder request (code=1 callback)");
        } catch (Exception e) {
            Log.e(TAG, "requestBinderAsync activity failed: " + e.getMessage());
            try {
                android.os.Binder callback2 = new android.os.Binder() {
                    @Override
                    protected boolean onTransact(int code, Parcel data, Parcel reply, int flags) {
                        if (code == 1) {
                            data.setDataPosition(0);
                            IBinder shizukuBinder = data.readStrongBinder();
                            if (shizukuBinder != null) {
                                sBinder = shizukuBinder;
                                sBinderRequested = false;
                                if (sOnReceivedCallback != null) {
                                    new android.os.Handler(android.os.Looper.getMainLooper()).post(sOnReceivedCallback);
                                }
                            }
                            Log.i(TAG, "Fallback onTransact called, binder=" + shizukuBinder);
                            return true;
                        }
                        return false;
                    }
                };
                Bundle bundle2 = new Bundle();
                bundle2.putBinder("binder", callback2);
                Intent fallback = new Intent(ACTION_REQUEST_BINDER);
                fallback.setPackage(SHIZUKU_PACKAGE);
                fallback.putExtra("data", bundle2);
                if (Build.VERSION.SDK_INT >= 33) {
                    fallback.addFlags(0x00200000);
                }
                context.sendBroadcast(fallback);
                Log.i(TAG, "Fallback broadcast sent");
            } catch (Exception e2) {
                Log.e(TAG, "fallback broadcast also failed: " + e2.getMessage());
                sBinderRequested = false;
            }
        }
    }

    public static void openShizukuPlayStore(Context context) {
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setData(Uri.parse("market://details?id=" + SHIZUKU_PACKAGE));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
        } catch (Exception e) {
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setData(Uri.parse("https://play.google.com/store/apps/details?id=" + SHIZUKU_PACKAGE));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(intent);
            } catch (Exception ignored) {}
        }
    }

    public static void openShizukuApp(Context context) {
        try {
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(SHIZUKU_PACKAGE);
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(intent);
            }
        } catch (Exception ignored) {}
    }

    public static String getStatus(Context context) {
        if (!isShizukuInstalled(context)) return "NAO_INSTALADO";
        if (sBinder != null && sBinder.pingBinder()) return "ATIVO";
        if (sBinderRequested) return "AGUARDANDO";
        return "PRONTO";
    }

    public static String executeShellCommand(String command) {
        if (!isShizukuRunning()) return "SHIZUKU_NOT_RUNNING";
        Log.i(TAG, "executeShellCommand: " + command);
        try {
            Parcel data = Parcel.obtain();
            Parcel reply = Parcel.obtain();
            try {
                data.writeInterfaceToken("moe.shizuku.server.IShizukuService");
                data.writeStringArray(new String[]{"sh", "-c", command});
                data.writeStringArray(null);
                data.writeString(null);

                try {
                    sBinder.transact(7, data, reply, 0);
                } catch (Exception e) {
                    return "ERROR: transact(7) threw " + e.getClass().getSimpleName() + ": " + e.getMessage();
                }
                reply.readException();

                IBinder processBinder = reply.readStrongBinder();
                Log.i(TAG, "Process binder=" + processBinder + " dataSize=" + reply.dataSize());

                if (processBinder == null) return "ERROR: no process binder";

                // Get stdin write end to send input (unused for now)
                // Get stdout: IRemoteProcess.getInputStream() = transaction code 2
                ParcelFileDescriptor stdoutPfd;
                Parcel isData = Parcel.obtain();
                Parcel isReply = Parcel.obtain();
                try {
                    isData.writeInterfaceToken("moe.shizuku.server.IRemoteProcess");
                    processBinder.transact(2, isData, isReply, 0);
                    isReply.readException();
                    stdoutPfd = isReply.readParcelable(null);
                } finally { isData.recycle(); isReply.recycle(); }

                if (stdoutPfd == null) return "ERROR: no stdout";

                StringBuilder output = new StringBuilder();
                java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.InputStreamReader(
                        new ParcelFileDescriptor.AutoCloseInputStream(stdoutPfd)));
                try {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        if (output.length() > 0) output.append("\n");
                        output.append(line);
                    }
                } finally { reader.close(); }

                // Wait for process: IRemoteProcess.waitFor() = transaction code 4
                Parcel wd = Parcel.obtain();
                Parcel wp = Parcel.obtain();
                try {
                    wd.writeInterfaceToken("moe.shizuku.server.IRemoteProcess");
                    processBinder.transact(4, wd, wp, 0);
                    wp.readException();
                    int exitCode = wp.readInt();
                    Log.i(TAG, "Exit code=" + exitCode);
                } finally { wd.recycle(); wp.recycle(); }

                String result = output.length() > 0 ? output.toString() : "OK";
                Log.i(TAG, "Result: " + (result.length() > 80 ? result.substring(0, 80) + "..." : result));
                return result;
            } finally { data.recycle(); reply.recycle(); }
        } catch (Exception e) {
            String detail = e.getMessage();
            if (e instanceof android.os.RemoteException) {
                detail = "RemoteException: " + e.toString();
            }
            Log.e(TAG, "executeShellCommand: " + detail);
            return "ERROR: " + detail;
        }
    }

    public static String disablePackage(String pkg) { return executeShellCommand("pm disable-user --user 0 " + pkg); }
    public static String uninstallPackage(String pkg) { return executeShellCommand("pm uninstall -k --user 0 " + pkg); }
    public static String enablePackage(String pkg) { return executeShellCommand("pm enable " + pkg); }
    public static String forceStopPackage(String pkg) { return executeShellCommand("am force-stop " + pkg); }
    public static String clearAppData(String pkg) { return executeShellCommand("pm clear " + pkg); }
    public static String listDisabledPackages() { return executeShellCommand("pm list packages -d"); }

    public static boolean isSuccess(String result) {
        if (result == null) return false;
        return !result.startsWith("SHIZUKU_NOT_RUNNING") && !result.startsWith("ERROR")
            && !result.contains("Error") && !result.contains("SecurityException")
            && !result.contains("not found");
    }

    public static String findNewProcessCode() {
        if (!isShizukuRunning()) return "SHIZUKU_NOT_RUNNING";
        StringBuilder sb = new StringBuilder();
        Log.i(TAG, "=== findNewProcessCode START ===");

        // Test 7 with known format (newProcess)
        for (int code = 7; code <= 8; code++) {
            try {
                Parcel data = Parcel.obtain();
                Parcel reply = Parcel.obtain();
                try {
                    data.writeStringArray(new String[]{"sh", "-c", "echo hello"});
                    data.writeStringArray(null);
                    data.writeString(null);
                    sBinder.transact(code, data, reply, 0);
                    reply.readException();
                    int pid = reply.readInt();
                    IBinder proc = reply.readStrongBinder();
                    String r = "T" + code + " (raw): pid=" + pid + " binder=" + (proc != null ? "OK" : "null");
                    Log.i(TAG, r);
                    sb.append(r).append("\n");
                } finally { data.recycle(); reply.recycle(); }
            } catch (Exception e) {
                String r = "T" + code + " (raw): " + e.getClass().getSimpleName() + ": " + e.getMessage();
                Log.i(TAG, r);
                sb.append(r).append("\n");
            }
        }

        // Test code 8 as transactRemote - scan transaction codes on system services
        // Format confirmed: writeInterfaceToken + writeStrongBinder(target) + writeInt(code) + writeInt(dataSize) + writeByteArray(data) + writeInt(flags)
        String[] services = {"power", "package", "activity"};
        int[] codeRanges = {1, 30}; // scan codes 1-30
        // First, find the correct interface descriptors for each service by scanning
        String[] descriptors = {
            "android.os.IPowerManager",
            "android.content.pm.IPackageManager",
            "android.app.IActivityManager"
        };
        for (int si = 0; si < services.length; si++) {
            String svc = services[si];
            String descriptor = descriptors[si];
            try {
                IBinder svcBinder = (IBinder) Class.forName("android.os.ServiceManager")
                    .getMethod("getService", String.class).invoke(null, svc);
                if (svcBinder == null) continue;
                for (int code = codeRanges[0]; code <= codeRanges[1]; code++) {
                    try {
                        Parcel data = Parcel.obtain();
                        Parcel reply = Parcel.obtain();
                        Parcel targetData = Parcel.obtain();
                        try {
                            targetData.writeInterfaceToken(descriptor);
                            byte[] raw = targetData.marshall();
                            
                            data.writeInterfaceToken("moe.shizuku.server.IShizukuService");
                            data.writeStrongBinder(svcBinder);
                            data.writeInt(code);
                            data.writeInt(raw.length);
                            data.writeByteArray(raw);
                            data.writeInt(0);
                            
                            sBinder.transact(8, data, reply, 0);
                            reply.readException();
                            int replySize = reply.readInt();
                            if (replySize > 0) {
                                byte[] result = reply.createByteArray();
                                String msg = "T8-" + svc + "/" + descriptor + " code=" + code
                                    + ": OK! replySize=" + replySize + " bytes=" + result.length;
                                Log.i(TAG, msg);
                                sb.append(msg).append("\n");
                            } else {
                                sb.append("T8-" + svc + "/" + descriptor + " code=" + code + ": replySize=0\n");
                            }
                        } finally { data.recycle(); reply.recycle(); targetData.recycle(); }
                    } catch (Exception e) {
                        // Don't log individual failures, just count
                    }
                }
            } catch (Exception e) {
                sb.append("T8-" + svc + ": setup: ").append(e.getClass().getSimpleName()).append("\n");
            }
        }
        
        // Scan codes 1-120 on package service with empty data
        try {
            IBinder pkgBinder2 = (IBinder) Class.forName("android.os.ServiceManager")
                .getMethod("getService", String.class).invoke(null, "package");
            if (pkgBinder2 != null) {
                for (int code = 1; code <= 120; code++) {
                    try {
                        Parcel data = Parcel.obtain();
                        Parcel reply = Parcel.obtain();
                        try {
                            data.writeInterfaceToken("moe.shizuku.server.IShizukuService");
                            data.writeStrongBinder(pkgBinder2);
                            data.writeInt(code);
                            data.writeInt(0);
                            data.writeByteArray(new byte[0]);
                            data.writeInt(0);
                            sBinder.transact(8, data, reply, 0);
                            reply.readException();
                            int replySize = reply.readInt();
                            if (replySize > 0) {
                                String msg = "T8-empty pkg code=" + code + ": replySize=" + replySize;
                                Log.i(TAG, msg);
                                sb.append(msg).append("\n");
                                byte[] result = reply.createByteArray();
                                sb.append("  result=").append(result.length).append(" bytes\n");
                            }
                        } finally { data.recycle(); reply.recycle(); }
                    } catch (Exception e) {
                        if (code < 5) {
                            Log.i(TAG, "T8-empty pkg code=" + code + ": " + e.getClass().getSimpleName());
                        }
                    }
                }
            }
        } catch (Exception e) {
            sb.append("T8-scan pkg: ").append(e.getClass().getSimpleName()).append("\n");
        }

        String result = sb.length() == 0 ? "Nothing found" : sb.toString();
        Log.i(TAG, "=== findNewProcessCode RESULT ===\n" + result);
        return result;
    }
}
