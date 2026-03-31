using System;
using System.Runtime.InteropServices;
using System.Threading;
using Newtonsoft.Json.Linq;

namespace ThumbParamsOSC;

/// <summary>
/// Wraps XInput controller input via P/Invoke on xinput1_4.dll.
/// Mirrors the Python XboxController implementation.
/// </summary>
internal sealed class XInputController
{
    // XInput button bitmasks
    private const ushort DPAD_UP = 0x0001;
    private const ushort DPAD_DOWN = 0x0002;
    private const ushort DPAD_LEFT = 0x0004;
    private const ushort DPAD_RIGHT = 0x0008;
    private const ushort START = 0x0010;
    private const ushort BACK = 0x0020;
    private const ushort LEFT_THUMB = 0x0040;
    private const ushort RIGHT_THUMB = 0x0080;
    private const ushort LEFT_SHOULDER = 0x0100;
    private const ushort RIGHT_SHOULDER = 0x0200;
    private const ushort A = 0x1000;
    private const ushort B = 0x2000;
    private const ushort X = 0x4000;
    private const ushort Y = 0x8000;

    private const float MAX_TRIG_VAL = 255f;   // XInput byte range 0–255
    private const float MAX_JOY_VAL = 32768f;   // 2^15
    private const float DEADZONE = 0.2f;

    [StructLayout(LayoutKind.Sequential)]
    private struct XINPUT_GAMEPAD
    {
        public ushort wButtons;
        public byte bLeftTrigger;
        public byte bRightTrigger;
        public short sThumbLX;
        public short sThumbLY;
        public short sThumbRX;
        public short sThumbRY;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct XINPUT_STATE
    {
        public uint dwPacketNumber;
        public XINPUT_GAMEPAD Gamepad;
    }

    [DllImport("xinput1_4.dll", EntryPoint = "XInputGetState")]
    private static extern uint XInputGetState(uint dwUserIndex, out XINPUT_STATE pState);

    private uint _controllerIndex = 0;
    private bool _isPlugged = false;
    private double _leftJoyX = 0, _leftJoyY = 0;
    private double _rightJoyX = 0, _rightJoyY = 0;
    private double _leftTrigger = 0, _rightTrigger = 0;
    private bool _btnA, _btnB, _btnX, _btnY;
    private bool _btnLeftThumb, _btnRightThumb;
    private bool _btnLeftShoulder, _btnRightShoulder;
    private bool _btnBack, _btnStart;
    private bool _btnDpadLeft, _btnDpadRight, _btnDpadUp, _btnDpadDown;
    private double _lastCheck = 0;

    public volatile bool Running = true;

    public bool IsPlugged => _isPlugged;

    /// <summary>
    /// Background polling loop – mirrors XboxController.polling_loop().
    /// </summary>
    public void PollLoop()
    {
        int sleepMs = 1;  // ~1000 Hz polling
        while (Running)
        {
            Poll();
            Thread.Sleep(sleepMs);
        }
    }

    private void Poll()
    {
        double now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
        if (!_isPlugged)
        {
            if (now - _lastCheck > 1.0)
            {
                _lastCheck = now;
                TryConnectController();
            }
            return;
        }

        try
        {
            if (XInputGetState(_controllerIndex, out XINPUT_STATE state) != 0)
            {
                _isPlugged = false;
                return;
            }
            UpdateState(state.Gamepad);
        }
        catch
        {
            _isPlugged = false;
        }
    }

    private void TryConnectController()
    {
        for (uint i = 0; i < 4; i++)
        {
            if (XInputGetState(i, out _) == 0)
            {
                _controllerIndex = i;
                _isPlugged = true;
                return;
            }
        }
    }

    private void UpdateState(XINPUT_GAMEPAD gp)
    {
        _leftTrigger = gp.bLeftTrigger / MAX_TRIG_VAL;
        _rightTrigger = gp.bRightTrigger / MAX_TRIG_VAL;
        _leftJoyX = gp.sThumbLX / MAX_JOY_VAL;
        _leftJoyY = gp.sThumbLY / MAX_JOY_VAL;
        _rightJoyX = gp.sThumbRX / MAX_JOY_VAL;
        _rightJoyY = gp.sThumbRY / MAX_JOY_VAL;
        _btnA = (gp.wButtons & A) != 0;
        _btnB = (gp.wButtons & B) != 0;
        _btnX = (gp.wButtons & X) != 0;
        _btnY = (gp.wButtons & Y) != 0;
        _btnLeftThumb = (gp.wButtons & LEFT_THUMB) != 0;
        _btnRightThumb = (gp.wButtons & RIGHT_THUMB) != 0;
        _btnLeftShoulder = (gp.wButtons & LEFT_SHOULDER) != 0;
        _btnRightShoulder = (gp.wButtons & RIGHT_SHOULDER) != 0;
        _btnBack = (gp.wButtons & BACK) != 0;
        _btnStart = (gp.wButtons & START) != 0;
        _btnDpadLeft = (gp.wButtons & DPAD_LEFT) != 0;
        _btnDpadRight = (gp.wButtons & DPAD_RIGHT) != 0;
        _btnDpadUp = (gp.wButtons & DPAD_UP) != 0;
        _btnDpadDown = (gp.wButtons & DPAD_DOWN) != 0;
    }

    /// <summary>
    /// Gets the current value for a config action.  Returns bool, float, or (float,float) tuple.
    /// Mirrors XboxController.get_value().
    /// </summary>
    public object? GetValue(JObject action)
    {
        string name = action["name"]!.Value<string>()!;
        return name switch
        {
            "A" => _btnA,
            "B" => _btnB,
            "X" => _btnX,
            "Y" => _btnY,
            "LeftThumb" => _btnLeftThumb,
            "RightThumb" => _btnRightThumb,
            "LeftBumper" => _btnLeftShoulder,
            "RightBumper" => _btnRightShoulder,
            "Back" => _btnBack,
            "Start" => _btnStart,
            "LeftDPad" => _btnDpadLeft,
            "RightDPad" => _btnDpadRight,
            "UpDPad" => _btnDpadUp,
            "DownDPad" => _btnDpadDown,
            "LeftTrigger" => (float)_leftTrigger,
            "RightTrigger" => (float)_rightTrigger,
            "LeftJoystickXY" => DzScaledRadial(_leftJoyX, _leftJoyY),
            "RightJoystickXY" => DzScaledRadial(_rightJoyX, _rightJoyY),
            "DPadXY" => (
                (float)(-Convert.ToDouble(_btnDpadLeft) + Convert.ToDouble(_btnDpadRight)),
                (float)(-Convert.ToDouble(_btnDpadDown) + Convert.ToDouble(_btnDpadUp))
            ),
            _ => throw new ArgumentException($"Value for {name} not found.")
        };
    }

    /// <summary>
    /// Scales joystick input with a radial deadzone.
    /// Mirrors the Python dz_scaled_radial() function.
    /// </summary>
    private static (float, float) DzScaledRadial(double x, double y)
    {
        double magnitude = Math.Sqrt(x * x + y * y);
        if (magnitude < DEADZONE)
            return (0f, 0f);

        double xNorm = x / magnitude;
        double yNorm = y / magnitude;
        double mapped = MapRange(magnitude, DEADZONE, 1.0, 0.0, 1.0);
        return ((float)(xNorm * mapped), (float)(yNorm * mapped));
    }

    private static double MapRange(double v, double oldMin, double oldMax, double newMin, double newMax)
        => newMin + (newMax - newMin) * (v - oldMin) / (oldMax - oldMin);
}
