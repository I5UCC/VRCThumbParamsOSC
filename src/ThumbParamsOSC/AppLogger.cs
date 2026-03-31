using System;
using System.IO;

namespace ThumbParamsOSC;

/// <summary>
/// Minimal logger that writes to console and a log file.
/// Mirrors Python's logging.basicConfig setup in main.py.
/// </summary>
internal static class AppLogger
{
    private static StreamWriter? _logFile;
    private static readonly object _lock = new();
    private static bool _debug;

    public static void Initialize(string logPath, bool debug)
    {
        _debug = debug;
        try
        {
            _logFile = new StreamWriter(logPath, append: false) { AutoFlush = true };
        }
        catch { }
    }

    public static void Info(string message) => Log("INFO", message);
    public static void Debug(string message) { if (_debug) Log("DEBUG", message); }
    public static void Error(string message) => Log("ERROR", message);

    private static void Log(string level, string message)
    {
        string line = $"{DateTime.Now:dd-MMM-yy HH:mm:ss} - {level} - {message}";
        lock (_lock)
        {
            Console.WriteLine(line);
            try { _logFile?.WriteLine(line); }
            catch { }
        }
    }

    public static void Close()
    {
        lock (_lock)
        {
            try { _logFile?.Close(); }
            catch { }
            _logFile = null;
        }
    }
}
