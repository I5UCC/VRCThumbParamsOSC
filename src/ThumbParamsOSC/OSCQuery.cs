using System;
using System.Net;
using System.Threading.Tasks;
using VRC.OSCQuery;

namespace ThumbParamsOSC;

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery HTTP service – advertises our OSC endpoint over mDNS (DNS-SD).
// Backed by vrchat-community/vrc-oscquery-lib.
// ─────────────────────────────────────────────────────────────────────────────
internal sealed class OscQueryService
{
    private readonly string _name;
    private readonly int _httpPort;
    private readonly int _oscPort;
    private OSCQueryService? _service;

    public OscQueryService(string name, int httpPort, int oscPort)
    {
        _name = name;
        _httpPort = httpPort;
        _oscPort = oscPort;
    }

    public void Start()
    {
        try
        {
            _service = new OSCQueryServiceBuilder()
                .WithTcpPort(_httpPort)
                .WithUdpPort(_oscPort)
                .WithServiceName(_name)
                .WithDefaults()
                .Build();

            _service.AddEndpoint("/avatar/change", "s", Attributes.AccessValues.ReadWrite);
            AppLogger.Info($"OSCQuery service started on TCP {_httpPort}, OSC {_oscPort}.");
        }
        catch (Exception ex)
        {
            AppLogger.Error($"OSCQuery service error: {ex.Message}");
        }
    }

    public void Stop()
    {
        try { _service?.Dispose(); } catch { }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery client – queries VRChat's OSCQuery endpoint over HTTP.
// ─────────────────────────────────────────────────────────────────────────────
internal sealed class OscQueryClient
{
    private readonly IPAddress _address;
    private readonly int _port;

    public OscQueryClient(IPAddress address, int port)
    {
        _address = address;
        _port = port;
    }

    public async Task<string?> QueryAvatarIdAsync()
    {
        try
        {
            var tree = await Extensions.GetOSCTree(_address, _port);
            var node = tree?.GetNodeWithPath("/avatar/change");
            if (node?.Value is { Length: > 0 })
                return node.Value[0]?.ToString();
            return null;
        }
        catch
        {
            return null;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery browser – discovers VRChat's OSCQuery endpoint via mDNS DNS-SD.
// ─────────────────────────────────────────────────────────────────────────────
internal static class OscQueryBrowser
{
    /// <summary>
    /// Browses for VRChat's OSCQuery service via mDNS.
    /// Returns an OscQueryClient once found, or null after the timeout.
    /// </summary>
    public static async Task<OscQueryClient?> FindVrChatAsync()
    {
        var tcs = new TaskCompletionSource<OscQueryClient?>();

        using var discovery = new OSCQueryServiceBuilder()
            .WithTcpPort(Extensions.GetAvailableTcpPort())
            .WithUdpPort(Extensions.GetAvailableUdpPort())
            .WithDefaults()
            .Build();

        discovery.OnOscQueryServiceAdded += profile =>
        {
            if (!profile.name.Equals("VRChat", StringComparison.OrdinalIgnoreCase)) return;
            tcs.TrySetResult(new OscQueryClient(profile.address, profile.port));
        };

        // Check services that were already discovered before our event was hooked up.
        foreach (var profile in discovery.GetOSCQueryServices())
        {
            if (profile.name.Equals("VRChat", StringComparison.OrdinalIgnoreCase))
            {
                tcs.TrySetResult(new OscQueryClient(profile.address, profile.port));
                break;
            }
        }

        discovery.RefreshServices();

        await Task.WhenAny(tcs.Task, Task.Delay(2000));
        return tcs.Task.IsCompletedSuccessfully ? tcs.Task.Result : null;
    }
}
