using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ThumbParamsOSC;

/// <summary>
/// WinForms ApplicationContext that owns the tray icon, initialises all subsystems,
/// and runs the main polling loop on a background thread.
/// Mirrors the top-level logic in the Python main.py.
/// </summary>
internal sealed class TrayApplicationContext : ApplicationContext
{
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    private static extern bool SetConsoleTitleW(string title);

    // ── paths ──────────────────────────────────────────────────────────────────
    private readonly string _basePath;
    private readonly string _configPath;
    private readonly string _manifestPath;
    private readonly string _firstLaunchFile;
    private readonly string _version;

    // ── config ─────────────────────────────────────────────────────────────────
    private JObject _config = null!;
    private double _pollingRateSec;
    private readonly bool _debug;

    // ── subsystems ─────────────────────────────────────────────────────────────
    private OVR? _ovr;
    private OSC? _osc;
    private XInputController? _xinput;

    // ── tray ───────────────────────────────────────────────────────────────────
    private NotifyIcon _trayIcon = null!;
    private volatile bool _running = true;

    // ─────────────────────────────────────────────────────────────────────────
    public TrayApplicationContext(bool debug, string? ipOverride, string? portOverride)
    {
        _debug = debug;
        _basePath = AppDomain.CurrentDomain.BaseDirectory;
        _configPath = Path.Combine(_basePath, "config.json");
        _manifestPath = Path.Combine(_basePath, "app.vrmanifest");
        _firstLaunchFile = Path.Combine(_basePath, "bindings", "first_launch");
        _version = ReadVersion();

        AppLogger.Initialize(Path.Combine(_basePath, "log.log"), debug);

        LoadConfig(ipOverride, portOverride);

        try { SetConsoleTitleW($"ThumbParamsOSC {_version}" + (debug ? " (Debug)" : "")); }
        catch { }

        CreateTrayIcon();
        HandleFirstLaunch();

        Task.Run(RunAsync);
    }

    // ── tray icon ──────────────────────────────────────────────────────────────

    private void CreateTrayIcon()
    {
        var menu = new ContextMenuStrip();

        var configuratorItem = new ToolStripMenuItem("Open Configurator");
        configuratorItem.Click += (_, _) => OpenConfigurator();
        menu.Items.Add(configuratorItem);

        menu.Items.Add(new ToolStripSeparator());

        var exitItem = new ToolStripMenuItem("Exit");
        exitItem.Click += (_, _) => Stop();
        menu.Items.Add(exitItem);

        string iconPath = Path.Combine(_basePath, "icon.ico");
        Icon icon = File.Exists(iconPath) ? new Icon(iconPath) : SystemIcons.Application;

        _trayIcon = new NotifyIcon
        {
            Icon = icon,
            Text = $"ThumbParamsOSC {_version}",
            Visible = true,
            ContextMenuStrip = menu,
        };
    }

    private void OpenConfigurator()
    {
        // Look for the Configurator executable in the same directory.
        // The Thumbparams_Configurator project builds to Configurator.exe.
        string[] candidateNames = { "Configurator.exe", "Thumbparams_Configurator.exe", "ThumbparamsConfigurator.exe" };

        string? exePath = candidateNames
            .Select(n => Path.Combine(_basePath, n))
            .FirstOrDefault(File.Exists);

        if (exePath == null)
        {
            MessageBox.Show(
                "Configurator executable not found in the application folder.",
                "ThumbParamsOSC",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning);
            return;
        }

        try
        {
            Process.Start(new ProcessStartInfo { FileName = exePath, UseShellExecute = true });
        }
        catch (Exception ex)
        {
            AppLogger.Error($"Failed to open configurator: {ex.Message}");
        }
    }

    // ── main async loop ────────────────────────────────────────────────────────

    private async Task RunAsync()
    {
        try
        {
            _ovr = new OVR(_config, _configPath, _manifestPath, _firstLaunchFile);
            _osc = new OSC(_config, OnAvatarChange, GetServerNeeded());
            _xinput = new XInputController();

            LogStartupInfo();

            // XInput polling runs on its own thread (mirrors Python xinput thread)
            var xinputThread = new Thread(_xinput.PollLoop) { IsBackground = true, Name = "XInput" };
            xinputThread.Start();

            while (_running)
            {
                HandleInput();
                await Task.Delay(TimeSpan.FromSeconds(_pollingRateSec));
            }
        }
        catch (Exception ex)
        {
            AppLogger.Error($"Fatal error: {ex}");
            MessageBox.Show(
                $"ThumbParamsOSC encountered a fatal error:\n{ex.Message}",
                "ThumbParamsOSC",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            Stop();
        }
    }

    // ── per-frame input handler ────────────────────────────────────────────────

    private void HandleInput()
    {
        try
        {
            _ovr?.PollNextEvents();
            _osc?.RefreshTime();

            // ── ControllerType ───────────────────────────────────────────────
            if (_config["ControllerType"]?["enabled"]?.Value<bool>() == true)
            {
                double timestamp = _config["ControllerType"]!["timestamp"]?.Value<double>() ?? 0;
                int always = _config["ControllerType"]!["always"]!.Value<int>();
                bool shouldSend = _osc!.CurrTime - timestamp > 10.0 || always != 0;
                if (shouldSend)
                {
                    int ct = _ovr?.GetControllerType() ?? 0;
                    bool xinputPlugged = _xinput?.IsPlugged == true;
                    if (ct == 0 && xinputPlugged) ct = 10;
                    else if (ct != 0 && xinputPlugged) ct += 10;
                    _osc!.Send("ControllerType", ct);
                }
            }

            var actions = (JArray)_config["actions"]!;

            // ── Skeleton actions (indices 0 and 1) ───────────────────────────
            for (int i = 0; i <= 1; i++)
            {
                var action = (JObject)actions[i]!;
                object? val = _ovr?.GetValue(action);
                _osc!.Send(action, val);
            }

            // ── Touch actions (indices 2–9) ──────────────────────────────────
            string strinputs = "";
            for (int i = 2; i < 10 && i < actions.Count; i++)
            {
                var action = (JObject)actions[i]!;
                object? val = _ovr?.GetValue(action) ?? false;
                bool bval = val is bool b && b;
                strinputs += bval ? "1" : "0";
                _osc!.Send(action, bval);
            }

            // LeftThumb / RightThumb: rfind("1") + 1 on the first/last 4 chars
            string left = strinputs.Length >= 4 ? strinputs[..4] : strinputs;
            string right = strinputs.Length >= 8 ? strinputs[4..8] : (strinputs.Length > 4 ? strinputs[4..] : "");
            _osc!.Send("LeftThumb", left.LastIndexOf('1') + 1);
            _osc!.Send("RightThumb", right.LastIndexOf('1') + 1);
            _osc!.Send("LeftABButtons", strinputs.Length >= 2 && strinputs[0] == '1' && strinputs[1] == '1');
            _osc!.Send("RightABButtons", strinputs.Length >= 6 && strinputs[4] == '1' && strinputs[5] == '1');

            // ── Remaining actions (indices 10+) ──────────────────────────────
            for (int i = 10; i < actions.Count; i++)
            {
                var action = (JObject)actions[i]!;
                object? val = _ovr?.GetValue(action);
                _osc!.Send(action, val);
            }

            // ── XInput actions ───────────────────────────────────────────────
            var xinputActions = (JArray)_config["xinput_actions"]!;
            foreach (JObject action in xinputActions)
            {
                object? val = _xinput?.GetValue(action);
                _osc!.Send(action, val);
            }

            if (_debug) PrintDebugOutput();
        }
        catch (Exception ex)
        {
            AppLogger.Error($"HandleInput error: {ex.Message}");
        }
    }

    // ── avatar change ──────────────────────────────────────────────────────────

    private void OnAvatarChange(string address, object value)
    {
        string avatarId = value?.ToString() ?? "";
        if (_osc?.CurrAvatar == avatarId) return;

        AppLogger.Info($"Resending parameters to {avatarId}");
        if (_osc != null) _osc.CurrAvatar = avatarId;

        ResendParameter("ControllerType");
        ResendParameter("LeftThumb");
        ResendParameter("RightThumb");
        ResendParameter("LeftABButtons");
        ResendParameter("RightABButtons");

        var actions = (JArray)_config["actions"]!;
        foreach (JObject action in actions)
        {
            if (action["type"]!.Value<string>() == "vector2")
            {
                var oscParams = (JArray)action["osc_parameter"]!;
                var lastValues = (JArray)action["last_value"]!;
                for (int i = 0; i < oscParams.Count; i++)
                    _osc?.SendParameter(oscParams[i].Value<string>()!, lastValues[i]);
            }
            else
            {
                _osc?.SendParameter(action["osc_parameter"]!.Value<string>()!, action["last_value"]);
            }
        }
    }

    private void ResendParameter(string name)
    {
        if (_config[name]?["enabled"]?.Value<bool>() != true) return;
        _osc?.SendParameter(name, _config[name]!["last_value"]);
    }

    // ── server-needed check ────────────────────────────────────────────────────

    private bool GetServerNeeded()
    {
        static bool NeedsServer(JToken? param) =>
            param?["enabled"]?.Value<bool>() == true && param["always"]?.Value<int>() == 0;

        if (NeedsServer(_config["ControllerType"])) return true;
        if (NeedsServer(_config["LeftThumb"])) return true;
        if (NeedsServer(_config["RightThumb"])) return true;
        if (NeedsServer(_config["LeftABButtons"])) return true;
        if (NeedsServer(_config["RightABButtons"])) return true;

        foreach (JObject action in _config["actions"]!)
        {
            if (action["type"]!.Value<string>() == "vector2")
            {
                var always = (JArray)action["always"]!;
                var enabled = (JArray)action["enabled"]!;
                for (int i = 0; i < always.Count; i++)
                    if (enabled[i].Value<bool>() && always[i].Value<int>() == 0)
                        return true;
            }
            else
            {
                if (action["enabled"]!.Value<bool>() && action["always"]!.Value<int>() == 0)
                    return true;
            }
        }

        return false;
    }

    // ── debug output ───────────────────────────────────────────────────────────

    private void PrintDebugOutput()
    {
        Console.Clear();
        Console.WriteLine("=== ThumbParamsOSC Debug ===");

        void PrintParam(string name, object? value, int always)
        {
            string modeStr = always switch { 0 => "SOC", 1 => "SOP", _ => "" };
            string valStr = value is float f ? f.ToString("F4") : (value?.ToString() ?? "");
            Console.Write($"{name,-23}\t{valStr,-6}\t{modeStr}");
        }

        var names = new[] { "ControllerType", "LeftThumb", "RightThumb", "LeftABButtons", "RightABButtons" };
        int col = 0;
        foreach (string n in names)
        {
            if (_config[n]?["enabled"]?.Value<bool>() != true) continue;
            PrintParam(n, _config[n]!["last_value"], _config[n]!["always"]!.Value<int>());
            Console.Write(col % 2 == 0 ? "\t" : "\n");
            col++;
        }

        foreach (JObject action in _config["actions"]!)
        {
            if (action["type"]!.Value<string>() == "vector2")
            {
                var oscParams = (JArray)action["osc_parameter"]!;
                var lastValues = (JArray)action["last_value"]!;
                var alwaysArr = (JArray)action["always"]!;
                for (int i = 0; i < oscParams.Count; i++)
                {
                    PrintParam(oscParams[i].Value<string>()!, lastValues[i], alwaysArr[i].Value<int>());
                    Console.Write(col % 2 == 0 ? "\t" : "\n");
                    col++;
                }
            }
            else
            {
                PrintParam(
                    action["osc_parameter"]!.Value<string>()!,
                    action["last_value"],
                    action["always"]!.Value<int>());
                Console.Write(col % 2 == 0 ? "\t" : "\n");
                col++;
            }
        }
        if (col % 2 != 0) Console.WriteLine();
    }

    // ── lifecycle ──────────────────────────────────────────────────────────────

    private void Stop()
    {
        _running = false;
        if (_xinput != null) _xinput.Running = false;
        _ovr?.Shutdown();
        _osc?.Shutdown();
        AppLogger.Close();
        _trayIcon.Visible = false;
        _trayIcon.Dispose();
        Application.Exit();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _trayIcon?.Dispose();
        }
        base.Dispose(disposing);
    }

    // ── helpers ────────────────────────────────────────────────────────────────

    private void LoadConfig(string? ipOverride, string? portOverride)
    {
        _config = JObject.Parse(File.ReadAllText(_configPath));
        if (ipOverride != null) _config["IP"] = ipOverride;
        if (portOverride != null) _config["Port"] = int.Parse(portOverride, CultureInfo.InvariantCulture);
        _pollingRateSec = 1.0 / _config["PollingRate"]!.Value<double>();
    }

    private void HandleFirstLaunch()
    {
        if (!File.Exists(_firstLaunchFile)) return;

        try
        {
            MessageBox.Show(
                "ThumbParamsOSC is now running and has registered as an Overlay on Steam.\n" +
                "It will now open automatically with SteamVR.\n" +
                "Open Configurator.exe to change sent Parameters and other Settings if you haven't yet.\n" +
                "This message is only shown once.",
                "ThumbParamsOSC",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information);

            AppLogger.Info("First Launch: deleting OSC cache and registering auto-launch.");
            string? appData = Environment.GetEnvironmentVariable("APPDATA");
            if (appData != null)
            {
                string cachePath = Path.Combine(appData, "..", "LocalLow", "VRChat", "VRChat", "OSC");
                if (Directory.Exists(cachePath))
                {
                    foreach (string folder in Directory.GetDirectories(cachePath, "usr_*"))
                    {
                        try { Directory.Delete(folder, recursive: true); }
                        catch { }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            AppLogger.Error($"Error during first launch: {ex.Message}");
        }
    }

    private void LogStartupInfo()
    {
        AppLogger.Info($"ThumbParamsOSC {_version} running...");
        AppLogger.Info($"IP: {_osc?.IP}");
        AppLogger.Info($"Port: {_osc?.Port}");
        AppLogger.Info($"Server Port: {_osc?.ServerPort}");
        AppLogger.Info($"HTTP Port: {_osc?.HttpPort}");
        AppLogger.Info($"PollingRate: {_pollingRateSec:F4}s ({_config["PollingRate"]} Hz)");
        AppLogger.Info($"StickMoveTolerance: {_config["StickMoveTolerance"]}%");
        AppLogger.Info("Open Configurator.exe to change sent Parameters and other Settings.");
    }

    private string ReadVersion()
    {
        string versionFile = Path.Combine(_basePath, "VERSION");
        return File.Exists(versionFile) ? File.ReadAllText(versionFile).Trim() : "unknown";
    }
}
