using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace ThumbParamsOSC;

/// <summary>
/// Handles OSC communication with VRChat (client + server) and implements all parameter-send logic.
/// Mirrors the Python OSC class.
/// </summary>
internal sealed class OSC : IDisposable
{
    // ── constants ──────────────────────────────────────────────────────────────
    private const string AVATAR_PARAMETERS_PREFIX = "/avatar/parameters/";
    private const string AVATAR_CHANGE_PARAMETER = "/avatar/change";

    // ── fields ─────────────────────────────────────────────────────────────────
    private readonly JObject _config;
    private UdpClient? _udpClient;
    private UdpClient? _udpServer;
    private readonly Action<string, object>? _avatarChangeCallback;

    private int _binaryNumBits;
    private int[] _binaryPotencies = Array.Empty<int>();
    private int _binaryPotency;
    private float _stickTolerance;

    public readonly string IP;
    public readonly int Port;
    public readonly int ServerPort;
    public readonly int HttpPort;
    public string CurrAvatar = "";
    public double CurrTime;

    // ── constructor ────────────────────────────────────────────────────────────
    public OSC(JObject config, Action<string, object> avatarChangeCallback, bool runServer)
    {
        _config = config;
        _avatarChangeCallback = avatarChangeCallback;

        IP = config["IP"]!.Value<string>()!;
        Port = config["Port"]!.Value<int>();
        ServerPort = config["Server_Port"]!.Value<int>();
        HttpPort = config["HTTP_Port"]!.Value<int>();
        _stickTolerance = (float)(config["StickMoveTolerance"]!.Value<int>() / 100.0);
        _binaryNumBits = config["Binary_bits"]!.Value<int>();
        _binaryPotencies = Enumerable.Range(0, _binaryNumBits).Select(i => (int)Math.Pow(2, i)).ToArray();
        _binaryPotency = (int)Math.Pow(2, _binaryNumBits) - 1;

        _udpClient = new UdpClient();
        _udpClient.Connect(IP, Port);

        if (runServer)
        {
            _ = Task.Run(() => StartServerAsync(avatarChangeCallback));
        }
    }

    // ── time ───────────────────────────────────────────────────────────────────
    public void RefreshTime() =>
        CurrTime = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;

    // ── public send API ────────────────────────────────────────────────────────

    /// <summary>
    /// Sends a named parameter (ControllerType, LeftThumb, etc.) by looking up the config dict.
    /// Mirrors the Python: if isinstance(action, str): … _send_boolean(…).
    /// </summary>
    public void Send(string actionName, object? value)
    {
        if (!_config.ContainsKey(actionName)) return;
        var action = (JObject)_config[actionName]!;
        action["osc_parameter"] = actionName;
        action["floating"] = 0.0;
        SendBoolean(action, value);
    }

    /// <summary>Sends a value for a config action dict, dispatching by type.</summary>
    public void Send(JObject action, object? value)
    {
        string type = action["type"]!.Value<string>()!;
        switch (type)
        {
            case "boolean":
                float floatingVal = action["floating"] is JToken ft ? ft.Value<float>() : 0f;
                if (floatingVal == -1f)
                    SendBooleanToggle(action, value is bool b && b);
                else
                    SendBoolean(action, value);
                break;
            case "vector1":
                SendVector1(action, value is float fv ? fv : Convert.ToSingle(value));
                break;
            case "vector2":
                if (value is (float vx, float vy))
                    SendVector2(action, vx, vy);
                else if (value is ValueTuple<float, float> t2)
                    SendVector2(action, t2.Item1, t2.Item2);
                break;
            case "skeleton":
                SendSkeleton(action, value as SkeletonData);
                break;
        }
    }

    // ── internal send methods ──────────────────────────────────────────────────

    private void SendBoolean(JObject action, object? value)
    {
        bool enabled = action["enabled"]!.Value<bool>();
        int always = action["always"]!.Value<int>();
        var lastValueToken = action["last_value"];
        object lastValue = lastValueToken?.Type == JTokenType.Boolean
            ? (object)lastValueToken.Value<bool>()
            : (lastValueToken?.Value<double>() ?? 0);

        bool doSend = always == 2
            || (always == 0 && !AreEqual(lastValue, value))
            || (always == 1 && IsTruthy(value));

        if (!enabled || !doSend) return;

        float floating = action["floating"] is JToken ft ? ft.Value<float>() : 0f;
        double timestamp = action["timestamp"] is JToken ts ? ts.Value<double>() : 0;

        if (floating > 0f)
        {
            if (IsTruthy(value))
            {
                action["timestamp"] = CurrTime;
            }
            else if (!IsTruthy(value) && CurrTime - timestamp <= floating)
            {
                value = lastValue;
            }
        }

        SendParameter(action["osc_parameter"]!.Value<string>()!, value);
        action["last_value"] = value == null ? null : JToken.FromObject(value);
    }

    private void SendBooleanToggle(JObject action, bool pressed)
    {
        if (!action["enabled"]!.Value<bool>()) return;

        if (pressed)
        {
            bool last = action["last_value"]?.Value<bool>() ?? false;
            bool newVal = !last;
            action["last_value"] = newVal;
            string paramName = action["osc_parameter"]!.Value<string>()!;
            // Delay asynchronously so the polling loop is not blocked.
            _ = Task.Run(async () =>
            {
                await Task.Delay(100);
                SendParameter(paramName, newVal);
            });
            return;
        }

        int always = action["always"]!.Value<int>();
        if (always != 0)
            SendParameter(action["osc_parameter"]!.Value<string>()!, action["last_value"]?.Value<bool>() ?? false);
    }

    private void SendVector1(JObject action, float value)
    {
        bool enabled = action["enabled"]!.Value<bool>();
        int always = action["always"]!.Value<int>();
        float lastValue = action["last_value"] is JToken lv ? lv.Value<float>() : 0f;

        bool doSend = always == 2
            || (always == 0 && !lastValue.Equals(value))
            || (always == 1 && value != 0f);

        if (!enabled || !doSend) return;

        float floating = action["floating"] is JToken ft ? ft.Value<float>() : 0f;
        double timestamp = action["timestamp"] is JToken ts ? ts.Value<double>() : 0;

        if (floating > 0f)
        {
            if (value > lastValue)
                action["timestamp"] = CurrTime;
            else if (value < lastValue && CurrTime - timestamp <= floating)
                value = lastValue;
        }

        bool binary = action["binary"] is JToken bt && bt.Value<bool>();
        if (binary)
        {
            var (bits, negative) = FloatToBinary(value);
            SendParameter(action["osc_parameter"]!.Value<string>()! + "_Negative", negative);
            for (int i = 0; i < bits.Length; i++)
                SendParameter(action["osc_parameter"]!.Value<string>()! + _binaryPotencies[i].ToString(), bits[i] == 1);
        }
        else
        {
            SendParameter(action["osc_parameter"]!.Value<string>()!, value);
        }

        action["last_value"] = value;
    }

    private void SendVector2(JObject action, float valX, float valY)
    {
        var oscParams = (JArray)action["osc_parameter"]!;
        var alwaysArr = (JArray)action["always"]!;
        var enabledArr = (JArray)action["enabled"]!;
        var lastValueArr = (JArray)action["last_value"]!;
        var floatingArr = (JArray)action["floating"]!;
        var timestampArr = (JArray)action["timestamp"]!;
        var unsignedArr = (JArray)action["unsigned"]!;
        var binaryArr = (JArray)action["binary"]!;

        if (unsignedArr[0].Value<bool>()) valX = (valX + 1f) / 2f;
        if (unsignedArr[1].Value<bool>()) valY = (valY + 1f) / 2f;

        float flt0 = floatingArr[0].Value<float>();
        float flt1 = floatingArr[1].Value<float>();
        double ts0 = timestampArr[0].Value<double>();
        double ts1 = timestampArr[1].Value<double>();
        float lv0 = lastValueArr[0].Value<float>();
        float lv1 = lastValueArr[1].Value<float>();

        if (flt0 > 0f)
        {
            if (valX != 0f) timestampArr[0] = CurrTime;
            else if (CurrTime - ts0 <= flt0) valX = lv0;
        }
        if (flt1 > 0f)
        {
            if (valY != 0f) timestampArr[1] = CurrTime;
            else if (CurrTime - ts1 <= flt1) valY = lv1;
        }

        bool valBool = valX > _stickTolerance || valY > _stickTolerance
                    || valX < -_stickTolerance || valY < -_stickTolerance;

        object[] values = { valX, valY, valBool };

        for (int i = 0; i < oscParams.Count; i++)
        {
            if (!enabledArr[i].Value<bool>()) continue;

            int always = alwaysArr[i].Value<int>();
            object lastVal = i < 2
                ? (object)lastValueArr[i].Value<float>()
                : (object)lastValueArr[i].Value<bool>();

            bool doSend = always == 2
                || (always == 0 && !AreEqual(lastVal, values[i]))
                || (always == 1 && IsTruthy(values[i]));

            if (!doSend) continue;

            bool binary = binaryArr[i].Value<bool>();
            if (binary && i < 2)
            {
                float fval = Convert.ToSingle(values[i]);
                var (bits, negative) = FloatToBinary(fval);
                string paramName = oscParams[i].Value<string>()!;
                SendParameter(paramName + "_Negative", negative);
                for (int j = 0; j < bits.Length; j++)
                    SendParameter(paramName + _binaryPotencies[j].ToString(), bits[j] == 1);
                lastValueArr[i] = JToken.FromObject(values[i]);
            }
            else
            {
                SendParameter(oscParams[i].Value<string>()!, values[i]);
                lastValueArr[i] = JToken.FromObject(values[i]);
            }
        }
    }

    private void SendSkeleton(JObject action, SkeletonData? skeleton)
    {
        if (skeleton == null || !action["enabled"]!.Value<bool>()) return;

        string baseParam = action["osc_parameter"]!.Value<string>()!;

        // Finger curls
        var curlNames = new[] { ("Thumb", Fingers.Thumb), ("Index", Fingers.Index), ("Middle", Fingers.Middle), ("Ring", Fingers.Ring), ("Pinky", Fingers.Pinky) };
        foreach (var (name, idx) in curlNames)
            SendVector1(BuildSkeletonSubAction(action, $"{baseParam}/Curl/{name}"), skeleton.FingerCurl[idx]);

        // Finger splays
        var splayNames = new[] { ("Index", SplayFingers.Index), ("Middle", SplayFingers.Middle), ("Ring", SplayFingers.Ring), ("Pinky", SplayFingers.Pinky) };
        foreach (var (name, idx) in splayNames)
            SendVector1(BuildSkeletonSubAction(action, $"{baseParam}/Splay/{name}"), skeleton.FingerSplay[idx]);
    }

    /// <summary>
    /// Creates a copy of the skeleton action with a specific osc_parameter.
    /// Mirrors the Python {**action, "osc_parameter": osc_parameter} dict spread.
    /// </summary>
    private static JObject BuildSkeletonSubAction(JObject action, string oscParameter)
    {
        var clone = (JObject)action.DeepClone();
        clone["osc_parameter"] = oscParameter;
        return clone;
    }

    // ── binary helpers ─────────────────────────────────────────────────────────

    private (int[] bits, bool negative) FloatToBinary(float value)
    {
        bool negative = value < 0;
        value = Math.Abs(value);
        int totalBase10 = (int)(value * _binaryPotency);
        string bitStr = Convert.ToString(totalBase10, 2).PadLeft(_binaryNumBits, '0');
        int[] bits = bitStr.Select(c => c == '1' ? 1 : 0).Reverse().ToArray(); // LSB first
        return (bits, negative);
    }

    // ── raw OSC send ───────────────────────────────────────────────────────────

    /// <summary>
    /// Sends an OSC message to the configured VRChat endpoint.
    /// </summary>
    public void SendParameter(string parameter, object? value)
    {
        string address = AVATAR_PARAMETERS_PREFIX + parameter;
        byte[] packet = BuildOscPacket(address, value);
        try { _udpClient?.Send(packet, packet.Length); }
        catch (Exception ex) { AppLogger.Error($"OSC send error: {ex.Message}"); }
    }

    // ── OSC packet encoding ────────────────────────────────────────────────────

    internal static byte[] BuildOscPacket(string address, object? value)
    {
        using var ms = new MemoryStream();
        WriteOscString(ms, address);

        if (value is bool b)
        {
            WriteOscString(ms, b ? ",T" : ",F");
        }
        else if (value is int intVal)
        {
            WriteOscString(ms, ",i");
            ms.Write(ToBigEndian(intVal));
        }
        else if (value is float floatVal)
        {
            WriteOscString(ms, ",f");
            ms.Write(ToBigEndian(floatVal));
        }
        else if (value is double doubleVal)
        {
            WriteOscString(ms, ",f");
            ms.Write(ToBigEndian((float)doubleVal));
        }
        else if (value is string str)
        {
            WriteOscString(ms, ",s");
            WriteOscString(ms, str);
        }
        else
        {
            // Fallback: try int
            WriteOscString(ms, ",i");
            ms.Write(ToBigEndian(Convert.ToInt32(value)));
        }

        return ms.ToArray();
    }

    private static void WriteOscString(MemoryStream ms, string s)
    {
        byte[] bytes = Encoding.ASCII.GetBytes(s + "\0");
        ms.Write(bytes, 0, bytes.Length);
        int pad = (4 - (bytes.Length % 4)) % 4;
        if (pad > 0) ms.Write(new byte[pad], 0, pad);
    }

    private static byte[] ToBigEndian(int v)
    {
        byte[] b = BitConverter.GetBytes(v);
        if (BitConverter.IsLittleEndian) Array.Reverse(b);
        return b;
    }

    private static byte[] ToBigEndian(float v)
    {
        byte[] b = BitConverter.GetBytes(v);
        if (BitConverter.IsLittleEndian) Array.Reverse(b);
        return b;
    }

    // ── OSC receive / avatar change ────────────────────────────────────────────

    private async Task StartServerAsync(Action<string, object> avatarChangeCallback)
    {
        try
        {
            int udpPort = ServerPort;
            int httpPortNum = HttpPort;

            if (udpPort != 9001)
            {
                AppLogger.Info("OSC Server port is not default, testing port availability.");
                udpPort = udpPort <= 0 || !IsUdpPortOpen(udpPort) ? GetOpenUdpPort() : udpPort;
                httpPortNum = httpPortNum <= 0 || !IsTcpPortOpen(httpPortNum)
                    ? (IsTcpPortOpen(udpPort) ? udpPort : GetOpenTcpPort())
                    : httpPortNum;
            }

            AppLogger.Info("Waiting for VRChat to start.");
            while (!IsVrChatRunning())
                await Task.Delay(3000);
            AppLogger.Info("VRChat started!");

            var qClient = await WaitGetOscQueryClientAsync();
            if (qClient != null)
            {
                string? avatarId = await qClient.QueryAvatarIdAsync();
                if (avatarId != null)
                    CurrAvatar = avatarId;
            }

            _udpServer = new UdpClient(udpPort);
            AppLogger.Info($"OSC server listening on port {udpPort}.");
            _ = Task.Run(() => OscReceiveLoopAsync(avatarChangeCallback));

            var oscQuery = new OscQueryService("ThumbParamsOSC", httpPortNum, udpPort);
            oscQuery.Start();
            AppLogger.Info($"OSCQuery advertised on HTTP port {httpPortNum}.");
        }
        catch (Exception ex)
        {
            AppLogger.Error($"OSC server error: {ex.Message}");
        }
    }

    private async Task OscReceiveLoopAsync(Action<string, object> cb)
    {
        while (_udpServer != null)
        {
            try
            {
                var result = await _udpServer.ReceiveAsync();
                var (address, args) = ParseOscPacket(result.Buffer);
                if (address == AVATAR_CHANGE_PARAMETER && args.Length > 0)
                    cb(address, args[0]);
            }
            catch (ObjectDisposedException) { break; }
            catch { }
        }
    }

    // ── OSC packet decoding ────────────────────────────────────────────────────

    internal static (string address, object[] args) ParseOscPacket(byte[] data)
    {
        int pos = 0;
        string address = ReadOscString(data, ref pos);
        if (pos >= data.Length) return (address, Array.Empty<object>());

        string typeTags = ReadOscString(data, ref pos);
        var args = new List<object>();

        for (int i = 1; i < typeTags.Length; i++)
        {
            switch (typeTags[i])
            {
                case 'i':
                    args.Add(ReadInt32(data, ref pos));
                    break;
                case 'f':
                    args.Add(ReadFloat32(data, ref pos));
                    break;
                case 's':
                    args.Add(ReadOscString(data, ref pos));
                    break;
                case 'T':
                    args.Add(true);
                    break;
                case 'F':
                    args.Add(false);
                    break;
            }
        }

        return (address, args.ToArray());
    }

    private static string ReadOscString(byte[] data, ref int pos)
    {
        int start = pos;
        while (pos < data.Length && data[pos] != 0) pos++;
        string s = Encoding.ASCII.GetString(data, start, pos - start);
        pos++; // null terminator
        int pad = (4 - (pos % 4)) % 4;
        pos += pad;
        return s;
    }

    private static int ReadInt32(byte[] data, ref int pos)
    {
        byte[] b = data[pos..(pos + 4)];
        if (BitConverter.IsLittleEndian) Array.Reverse(b);
        pos += 4;
        return BitConverter.ToInt32(b);
    }

    private static float ReadFloat32(byte[] data, ref int pos)
    {
        byte[] b = data[pos..(pos + 4)];
        if (BitConverter.IsLittleEndian) Array.Reverse(b);
        pos += 4;
        return BitConverter.ToSingle(b);
    }

    // ── port utilities ─────────────────────────────────────────────────────────

    private static int GetOpenUdpPort()
    {
        using var s = new UdpClient(0);
        return ((IPEndPoint)s.Client.LocalEndPoint!).Port;
    }

    private static int GetOpenTcpPort()
    {
        using var s = new System.Net.Sockets.TcpListener(IPAddress.Loopback, 0);
        s.Start();
        int port = ((IPEndPoint)s.LocalEndpoint).Port;
        s.Stop();
        return port;
    }

    private static bool IsUdpPortOpen(int port)
    {
        try { using var s = new UdpClient(port); return true; }
        catch { return false; }
    }

    private static bool IsTcpPortOpen(int port)
    {
        try
        {
            using var s = new System.Net.Sockets.TcpListener(IPAddress.Loopback, port);
            s.Start(); s.Stop(); return true;
        }
        catch { return false; }
    }

    private static bool IsVrChatRunning()
    {
        foreach (var p in System.Diagnostics.Process.GetProcesses())
        {
            if (p.ProcessName.Equals("VRChat", StringComparison.OrdinalIgnoreCase))
                return true;
        }
        return false;
    }

    private static async Task<OscQueryClient?> WaitGetOscQueryClientAsync()
    {
        AppLogger.Info("Waiting for VRChat to be discovered via OSCQuery.");
        OscQueryClient? client = null;
        while (client == null)
        {
            client = await OscQueryBrowser.FindVrChatAsync();
            if (client == null)
                await Task.Delay(2000);
        }
        AppLogger.Info("VRChat discovered!");

        AppLogger.Info("Waiting for VRChat to be ready.");
        while (await client.QueryAvatarIdAsync() == null)
            await Task.Delay(2000);
        AppLogger.Info("VRChat ready!");
        return client;
    }

    // ── helpers ────────────────────────────────────────────────────────────────

    private static bool IsTruthy(object? v) =>
        v switch
        {
            bool b => b,
            int i => i != 0,
            float f => f != 0f,
            double d => d != 0.0,
            null => false,
            _ => true,
        };

    private static bool AreEqual(object? a, object? b)
    {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        if (a is float fa && b is float fb) return Math.Abs(fa - fb) < 1e-6f;
        if (a is double da && b is double db) return Math.Abs(da - db) < 1e-9;
        return a.Equals(b);
    }

    public void Shutdown()
    {
        try { _udpClient?.Close(); } catch { }
        try { _udpServer?.Close(); } catch { }
        _udpClient = null;
        _udpServer = null;
    }

    public void Dispose() => Shutdown();
}
