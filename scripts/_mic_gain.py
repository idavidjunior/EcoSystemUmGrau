"""Diagnostica e ajusta o ganho do microfone do Windows."""
import ctypes
from ctypes import POINTER, byref, c_float, c_int, c_uint, cast, wintypes

CLSID_MMDEVICE_ENUM = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
IID_IMMDEVICEENUM = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
IID_IAUDIOENDPOINTVOLUME = "{5CDF2C82-841E-4546-9722-0CF74078229A}"
IID_IMMDEVICE = "{D666063F-1587-4E43-81F1-B948E807363F}"

import subprocess
import sys

def list_devices():
    """Lista microfones e seus níveis usando a Core Audio API via PowerShell."""
    ps = r'''
$code = @"
using System;
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
  int RegisterControlChangeNotify(IntPtr p);
  int UnregisterControlChangeNotify(IntPtr p);
  int GetChannelCount(out int count);
  int SetMasterVolumeLevel(float level, ref Guid ctx);
  int SetMasterVolumeLevelScalar(float level, ref Guid ctx);
  int GetMasterVolumeLevel(out float level);
  int GetMasterVolumeLevelScalar(out float level);
  int SetChannelVolumeLevel(uint ch, float level, ref Guid ctx);
  int SetChannelVolumeLevelScalar(uint ch, float level, ref Guid ctx);
  int GetChannelVolumeLevel(uint ch, out float level);
  int GetChannelVolumeLevelScalar(uint ch, out float level);
  int SetMute(bool mute, ref Guid ctx);
  int GetMute(out bool mute);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
  int Activate(ref Guid iid, int clsctx, IntPtr p, out IAudioEndpointVolume vol);
  int OpenPropertyStore(int stgm, out IntPtr props);
  int GetId(out IntPtr id);
  int GetState(out int state);
}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
  int EnumAudioEndpoints(int dataflow, int mask, out IntPtr list);
  int GetDefaultAudioEndpoint(int dataflow, int role, out IMMDevice device);
  int GetDevice(string id, out IMMDevice device);
  int RegisterEndpointNotificationCallback(IntPtr p);
  int UnregisterEndpointNotificationCallback(IntPtr p);
}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject { }
public class MicGain {
  public static string GetLevels() {
    var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
    IMMDevice dev;
    en.GetDefaultAudioEndpoint(1, 0, out dev); // eCapture=1, eConsole=0
    IAudioEndpointVolume vol;
    Guid iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    dev.Activate(ref iid, 1, IntPtr.Zero, out vol);
    float lvl; bool mute;
    vol.GetMasterVolumeLevelScalar(out lvl);
    vol.GetMute(out mute);
    return "nivel=" + Math.Round(lvl*100) + "% mute=" + mute;
  }
  public static string SetLevels(float scalar) {
    var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
    IMMDevice dev;
    en.GetDefaultAudioEndpoint(1, 0, out dev);
    IAudioEndpointVolume vol;
    Guid iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    dev.Activate(ref iid, 1, IntPtr.Zero, out vol);
    Guid ctx = Guid.Empty;
    vol.SetMasterVolumeLevelScalar(scalar, ref ctx);
    vol.SetMute(false, ref ctx);
    return "ok";
  }
}
"@
Add-Type -TypeDefinition $code -Language CSharp
[MicGain]::GetLevels()
'''
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=30)
    return r.stdout.strip(), r.stderr.strip()

if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "get"
    if modo == "get":
        out, err = list_devices()
        print("nivel atual:", out)
        if err:
            print("erro:", err[:300])
    else:
        scalar = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
        out, err = list_devices()
        # set via powershell inline
        ps = f'''
$code = @"
using System;
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
  int RegisterControlChangeNotify(IntPtr p);
  int UnregisterControlChangeNotify(IntPtr p);
  int GetChannelCount(out int count);
  int SetMasterVolumeLevel(float level, ref Guid ctx);
  int SetMasterVolumeLevelScalar(float level, ref Guid ctx);
  int GetMasterVolumeLevel(out float level);
  int GetMasterVolumeLevelScalar(out float level);
  int SetChannelVolumeLevel(uint ch, float level, ref Guid ctx);
  int SetChannelVolumeLevelScalar(uint ch, float level, ref Guid ctx);
  int GetChannelVolumeLevel(uint ch, out float level);
  int GetChannelVolumeLevelScalar(uint ch, out float level);
  int SetMute(bool mute, ref Guid ctx);
  int GetMute(out bool mute);
}}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {{
  int Activate(ref Guid iid, int clsctx, IntPtr p, out IAudioEndpointVolume vol);
  int OpenPropertyStore(int stgm, out IntPtr props);
  int GetId(out IntPtr id);
  int GetState(out int state);
}}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {{
  int EnumAudioEndpoints(int dataflow, int mask, out IntPtr list);
  int GetDefaultAudioEndpoint(int dataflow, int role, out IMMDevice device);
  int GetDevice(string id, out IMMDevice device);
  int RegisterEndpointNotificationCallback(IntPtr p);
  int UnregisterEndpointNotificationCallback(IntPtr p);
}}
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject {{ }}
public class MicGain {{
  public static string GetLevels() {{
    var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
    IMMDevice dev;
    en.GetDefaultAudioEndpoint(1, 0, out dev);
    IAudioEndpointVolume vol;
    Guid iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    dev.Activate(ref iid, 1, IntPtr.Zero, out vol);
    float lvl; bool mute;
    vol.GetMasterVolumeLevelScalar(out lvl);
    vol.GetMute(out mute);
    return "nivel=" + Math.Round(lvl*100) + "% mute=" + mute;
  }}
  public static string SetLevels(float scalar) {{
    var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorComObject();
    IMMDevice dev;
    en.GetDefaultAudioEndpoint(1, 0, out dev);
    IAudioEndpointVolume vol;
    Guid iid = new Guid("5CDF2C82-841E-4546-9722-0CF74078229A");
    dev.Activate(ref iid, 1, IntPtr.Zero, out vol);
    Guid ctx = Guid.Empty;
    vol.SetMasterVolumeLevelScalar(scalar, ref ctx);
    vol.SetMute(false, ref ctx);
    return "ok";
  }}
}}
"@
Add-Type -TypeDefinition $code -Language CSharp
[MicGain]::SetLevels({scalar})
[MicGain]::GetLevels()
'''
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=30)
        print("resultado:", r.stdout.strip() or r.stderr.strip()[:300])
