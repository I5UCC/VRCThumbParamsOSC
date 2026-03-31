using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using Newtonsoft.Json.Linq;
using Valve.VR;

// Use an alias to avoid colliding with the "OpenVR.NET" namespace that the
// NuGet package injects – which makes the compiler treat bare "OpenVR" as a
// namespace rather than the Valve.VR.OpenVR static class.
using VR = Valve.VR.OpenVR;

namespace ThumbParamsOSC;

/// <summary>
/// Finger indices for VRSkeletalSummaryData_t.flFingerCurl (Thumb=0 … Pinky=4).
/// </summary>
internal static class Fingers
{
    public const int Thumb = 0;
    public const int Index = 1;
    public const int Middle = 2;
    public const int Ring = 3;
    public const int Pinky = 4;
}

/// <summary>
/// Splay indices for VRSkeletalSummaryData_t.flFingerSplay (Thumb_Index=0 … Ring_Pinky=3).
/// </summary>
internal static class SplayFingers
{
    public const int Index = 0;   // Thumb–Index splay
    public const int Middle = 1;  // Index–Middle splay
    public const int Ring = 2;    // Middle–Ring splay
    public const int Pinky = 3;   // Ring–Pinky splay
}

/// <summary>
/// Convenience wrapper around VRSkeletalSummaryData_t that exposes arrays.
/// </summary>
internal sealed class SkeletonData
{
    public readonly float[] FingerCurl;
    public readonly float[] FingerSplay;

    public SkeletonData(VRSkeletalSummaryData_t data)
    {
        FingerCurl = new float[]
        {
            data.flFingerCurl0,
            data.flFingerCurl1,
            data.flFingerCurl2,
            data.flFingerCurl3,
            data.flFingerCurl4,
        };
        FingerSplay = new float[]
        {
            data.flFingerSplay0,
            data.flFingerSplay1,
            data.flFingerSplay2,
            data.flFingerSplay3,
        };
    }
}

/// <summary>
/// OpenVR wrapper.  Mirrors the Python OVR class.
/// </summary>
internal sealed class OVR : IDisposable
{
    private readonly CVRSystem _vrSystem;
    private readonly VRActiveActionSet_t[] _actionSets;

    private static readonly uint SizeOfActiveActionSet =
        (uint)Marshal.SizeOf<VRActiveActionSet_t>();
    private static readonly uint SizeOfDigitalData =
        (uint)Marshal.SizeOf<InputDigitalActionData_t>();
    private static readonly uint SizeOfAnalogData =
        (uint)Marshal.SizeOf<InputAnalogActionData_t>();

    public OVR(JObject config, string configPath, string manifestPath, string firstLaunchFile)
    {
        EVRInitError initError = EVRInitError.None;
        _vrSystem = VR.Init(ref initError, EVRApplicationType.VRApplication_Utility, "");
        if (initError != EVRInitError.None)
            throw new InvalidOperationException(
                $"OpenVR init failed: {VR.GetStringForHmdError(initError)}");

        AppLogger.Info("OpenVR Initialized.");

        VR.Input.SetActionManifestPath(configPath);
        VR.Applications.AddApplicationManifest(manifestPath, false);
        AppLogger.Info("Application Manifest Added.");

        if (File.Exists(firstLaunchFile))
        {
            VR.Applications.SetApplicationAutoLaunch("i5ucc.thumbparamsosc", true);
            AppLogger.Info("Application set to auto launch.");
            File.Delete(firstLaunchFile);
        }

        ulong actionSetHandle = 0;
        VR.Input.GetActionSetHandle("/actions/thumbparams", ref actionSetHandle);

        _actionSets = new VRActiveActionSet_t[1];
        _actionSets[0].ulActionSet = actionSetHandle;

        foreach (var action in config["actions"]!.Children<JObject>())
        {
            ulong ah = 0;
            VR.Input.GetActionHandle(action["name"]!.Value<string>()!, ref ah);
            action["handle"] = ah;
        }
    }

    /// <summary>Returns the controller type integer (0=unknown, 1=Knuckles, 2=Oculus Touch).</summary>
    public int GetControllerType()
    {
        for (uint i = 1; i < VR.k_unMaxTrackedDeviceCount; i++)
        {
            if (VR.System.GetTrackedDeviceClass(i) != ETrackedDeviceClass.Controller)
                continue;

            var sb = new StringBuilder((int)VR.k_unMaxPropertyStringSize);
            var err = ETrackedPropertyError.TrackedProp_Success;
            VR.System.GetStringTrackedDeviceProperty(
                i,
                ETrackedDeviceProperty.Prop_ControllerType_String,
                sb,
                VR.k_unMaxPropertyStringSize,
                ref err);

            return sb.ToString() switch
            {
                "knuckles" => 1,
                "oculus_touch" => 2,
                _ => 0,
            };
        }
        return 0;
    }

    /// <summary>
    /// Gets the current value for an action.
    /// Returns bool (boolean), float (vector1), (float,float) tuple (vector2), or SkeletonData (skeleton).
    /// Mirrors OVR.get_value().
    /// </summary>
    public object? GetValue(JObject action)
    {
        ulong handle = action["handle"]!.Value<ulong>();

        return action["type"]!.Value<string>() switch
        {
            "boolean" => GetDigitalValue(handle),
            "vector1" => GetAnalogValue(handle),
            "vector2" => GetAnalogVector2(handle),
            "skeleton" => GetSkeletonValue(handle),
            var t => throw new ArgumentException($"Unknown action type: {t}"),
        };
    }

    private bool GetDigitalValue(ulong handle)
    {
        InputDigitalActionData_t data = default;
        VR.Input.GetDigitalActionData(
            handle, ref data, SizeOfDigitalData, VR.k_ulInvalidInputValueHandle);
        return data.bState && data.bActive;
    }

    private float GetAnalogValue(ulong handle)
    {
        InputAnalogActionData_t data = default;
        VR.Input.GetAnalogActionData(
            handle, ref data, SizeOfAnalogData, VR.k_ulInvalidInputValueHandle);
        return data.x;
    }

    private (float, float) GetAnalogVector2(ulong handle)
    {
        InputAnalogActionData_t data = default;
        VR.Input.GetAnalogActionData(
            handle, ref data, SizeOfAnalogData, VR.k_ulInvalidInputValueHandle);
        return (data.x, data.y);
    }

    private SkeletonData? GetSkeletonValue(ulong handle)
    {
        VRSkeletalSummaryData_t data = default;
        EVRInputError err = VR.Input.GetSkeletalSummaryData(
            handle, EVRSummaryType.FromDevice, ref data);
        if (err == EVRInputError.NoData)
            return null;
        return new SkeletonData(data);
    }

    /// <summary>Polls VR events and updates action state.  Mirrors OVR.poll_next_events().</summary>
    public void PollNextEvents()
    {
        VREvent_t evt = default;
        uint evtSize = (uint)Marshal.SizeOf<VREvent_t>();
        while (_vrSystem.PollNextEvent(ref evt, evtSize)) { }

        try
        {
            VR.Input.UpdateActionState(_actionSets, SizeOfActiveActionSet);
        }
        catch
        {
            AppLogger.Error("No data available for action state update.");
        }
    }

    public void Shutdown()
    {
        try { VR.Shutdown(); }
        catch (Exception ex) { AppLogger.Error($"Error shutting down OVR: {ex.Message}"); }
    }

    public void Dispose() => Shutdown();
}
