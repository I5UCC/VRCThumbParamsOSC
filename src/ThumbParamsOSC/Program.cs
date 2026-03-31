using System;
using System.Windows.Forms;

namespace ThumbParamsOSC;

internal static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        Application.SetHighDpiMode(HighDpiMode.SystemAware);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        bool debug = false;
        string? ip = null;
        string? port = null;

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-d":
                case "--debug":
                    debug = true;
                    break;
                case "-i":
                case "--ip":
                    if (i + 1 < args.Length) ip = args[++i];
                    break;
                case "-p":
                case "--port":
                    if (i + 1 < args.Length) port = args[++i];
                    break;
            }
        }

        Application.Run(new TrayApplicationContext(debug, ip, port));
    }
}
