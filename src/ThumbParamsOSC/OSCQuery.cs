using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Text;
using System.Threading.Tasks;
using Makaretu.Dns;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ThumbParamsOSC;

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery HTTP service – advertises our OSC endpoint over mDNS (DNS-SD).
// Mirrors Python's tinyoscquery.queryservice.OSCQueryService.
// ─────────────────────────────────────────────────────────────────────────────
internal sealed class OscQueryService
{
    private readonly string _name;
    private readonly int _httpPort;
    private readonly int _oscPort;
    private HttpListener? _listener;
    private MulticastService? _mdns;
    private ServiceDiscovery? _sd;

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
            _listener = new HttpListener();
            _listener.Prefixes.Add($"http://*:{_httpPort}/");
            _listener.Start();
            _ = Task.Run(ServeAsync);
            AdvertiseMdns();
            AppLogger.Info($"OSCQuery HTTP server started on port {_httpPort}.");
        }
        catch (Exception ex)
        {
            AppLogger.Error($"OSCQuery service error: {ex.Message}");
        }
    }

    private void AdvertiseMdns()
    {
        try
        {
            _mdns = new MulticastService();
            _sd = new ServiceDiscovery(_mdns);

            // Collect local unicast IPv4 addresses for the service profile.
            var addresses = NetworkInterface.GetAllNetworkInterfaces()
                .Where(ni => ni.OperationalStatus == OperationalStatus.Up)
                .SelectMany(ni => ni.GetIPProperties().UnicastAddresses)
                .Select(ua => ua.Address)
                .Where(a => a.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)
                .ToList();

            var profile = new ServiceProfile(
                instanceName: new DomainName(_name),
                serviceName: new DomainName("_oscjson._tcp"),
                port: (ushort)_httpPort,
                addresses: addresses);

            _sd.Advertise(profile);
            _mdns.Start();
        }
        catch (Exception ex)
        {
            AppLogger.Error($"mDNS advertise error: {ex.Message}");
        }
    }

    private async Task ServeAsync()
    {
        while (_listener?.IsListening == true)
        {
            HttpListenerContext ctx;
            try { ctx = await _listener.GetContextAsync(); }
            catch { break; }

            string json = BuildRootNode();
            byte[] bytes = Encoding.UTF8.GetBytes(json);
            ctx.Response.ContentType = "application/json";
            ctx.Response.ContentLength64 = bytes.Length;
            await ctx.Response.OutputStream.WriteAsync(bytes);
            ctx.Response.Close();
        }
    }

    private string BuildRootNode()
    {
        var node = new JObject
        {
            ["DESCRIPTION"] = "ThumbParamsOSC",
            ["FULL_PATH"] = "/",
            ["ACCESS"] = 0,
            ["CONTENTS"] = new JObject
            {
                ["avatar"] = new JObject
                {
                    ["DESCRIPTION"] = "",
                    ["FULL_PATH"] = "/avatar",
                    ["ACCESS"] = 0,
                    ["CONTENTS"] = new JObject
                    {
                        ["change"] = new JObject
                        {
                            ["DESCRIPTION"] = "",
                            ["FULL_PATH"] = "/avatar/change",
                            ["ACCESS"] = 3,  // readwrite
                            ["TYPE"] = "s",
                        }
                    }
                }
            }
        };
        return node.ToString(Formatting.None);
    }

    public void Stop()
    {
        try { _mdns?.Stop(); } catch { }
        try { _listener?.Stop(); } catch { }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery client – queries VRChat's OSCQuery endpoint over HTTP.
// Mirrors Python's tinyoscquery.query.OSCQueryClient.
// ─────────────────────────────────────────────────────────────────────────────
internal sealed class OscQueryClient
{
    private readonly string _host;
    private readonly int _port;
    private static readonly HttpClient _http = new HttpClient { Timeout = TimeSpan.FromSeconds(5) };

    public OscQueryClient(string host, int port)
    {
        _host = host;
        _port = port;
    }

    public async Task<string?> QueryAvatarIdAsync()
    {
        try
        {
            string url = $"http://{_host}:{_port}/avatar/change";
            string json = await _http.GetStringAsync(url);
            var node = JObject.Parse(json);
            var value = node["VALUE"];
            if (value is JArray arr && arr.Count > 0)
                return arr[0].Value<string>();
            return value?.Value<string>();
        }
        catch
        {
            return null;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// OSCQuery browser – discovers VRChat's OSCQuery endpoint via mDNS DNS-SD.
// Mirrors Python's tinyoscquery.query.OSCQueryBrowser.
// ─────────────────────────────────────────────────────────────────────────────
internal static class OscQueryBrowser
{
    private const string ServiceType = "_oscjson._tcp";

    /// <summary>
    /// Browses for VRChat's OSCQuery service via mDNS.
    /// Returns an OscQueryClient once found, or null after the timeout.
    /// </summary>
    public static async Task<OscQueryClient?> FindVrChatAsync()
    {
        var tcs = new TaskCompletionSource<OscQueryClient?>();

        using var mdns = new MulticastService();
        using var sd = new ServiceDiscovery(mdns);

        sd.ServiceInstanceDiscovered += (_, e) =>
        {
            // ServiceInstanceName labels: [instanceName, _oscjson, _tcp, local]
            var labels = e.ServiceInstanceName.Labels;
            if (labels.Count == 0) return;
            string instanceName = labels[0];
            if (!instanceName.Equals("VRChat", StringComparison.OrdinalIgnoreCase))
                return;

            // Look for an SRV record in the message answers/additional records.
            var allRecords = e.Message.Answers
                .Concat(e.Message.AdditionalRecords)
                .Concat(e.Message.AuthorityRecords);

            foreach (var record in allRecords)
            {
                if (record is SRVRecord srv)
                {
                    string target = srv.Target.ToString().TrimEnd('.');
                    int port = srv.Port;
                    if (target.Length > 0 && port > 0)
                    {
                        // Prefer 127.0.0.1 / localhost for the host
                        string host = target.Equals("localhost", StringComparison.OrdinalIgnoreCase)
                            ? "127.0.0.1"
                            : target;
                        tcs.TrySetResult(new OscQueryClient(host, port));
                        return;
                    }
                }
            }

            // If no SRV yet, query for it – the SRV record will arrive in a later AnswerReceived.
        };

        mdns.AnswerReceived += (_, e) =>
        {
            foreach (var record in e.Message.Answers.Concat(e.Message.AdditionalRecords))
            {
                if (record is SRVRecord srv)
                {
                    // Check if this SRV belongs to a VRChat instance
                    string name = srv.Name.ToString();
                    if (!name.StartsWith("VRChat.", StringComparison.OrdinalIgnoreCase))
                        continue;
                    string target = srv.Target.ToString().TrimEnd('.');
                    int port = srv.Port;
                    if (target.Length > 0 && port > 0)
                    {
                        string host = target.Equals("localhost", StringComparison.OrdinalIgnoreCase)
                            ? "127.0.0.1"
                            : target;
                        tcs.TrySetResult(new OscQueryClient(host, port));
                    }
                }
            }
        };

        mdns.Start();
        sd.QueryServiceInstances(new DomainName(ServiceType));

        // Wait up to 2 seconds for discovery
        var delay = Task.Delay(2000);
        await Task.WhenAny(tcs.Task, delay);

        mdns.Stop();
        return tcs.Task.IsCompletedSuccessfully ? tcs.Task.Result : null;
    }
}
