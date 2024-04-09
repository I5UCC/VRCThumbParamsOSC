using System;
using System.Windows;
using System.IO;
using System.Collections.ObjectModel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Windows.Controls;
using System.Text.RegularExpressions;
using System.Security.RightsManagement;

namespace Configurator
{
    public partial class MainWindow : Window
    {
        public ObservableCollection<BoolStringClass> ParameterList { get; set; }
        private Config config;
        private string ConfigPath;
        private bool Startup;

        public MainWindow()
        {
            Startup = true;
            InitializeComponent();
            ParameterList = new ObservableCollection<BoolStringClass>();

            ConfigPath = AppDomain.CurrentDomain.BaseDirectory + "config.json";
            config = JsonConvert.DeserializeObject<Config>(File.ReadAllText(ConfigPath));

            Tbx_IP.Text = config.IP;
            Tbx_Port.Text = config.Port.ToString();
            Tbx_Server_Port.Text = config.Server_Port.ToString();
            Tbx_http_port.Text = config.HTTP_Port.ToString();
            Tbx_PollingRate.Text = config.PollingRate.ToString();
            Tbx_StickMoveTolerance.Text = config.StickMoveTolerance.ToString();
            Tbx_Binary.Text = config.Binary_bits.ToString();

            ParameterList.Add(new BoolStringClass("ControllerType", config.ControllerType.enabled, config.ControllerType.always, "Integer", "Unavailable", false, false, false, "Hidden"));
            ParameterList.Add(new BoolStringClass("LeftThumb", config.LeftThumb.enabled, config.LeftThumb.always, "Integer", "Infl. by bools", false, false, false, "Hidden"));
            ParameterList.Add(new BoolStringClass("RightThumb", config.RightThumb.enabled, config.RightThumb.always, "Integer", "Infl. by bools", false, false, false, "Hidden"));

            ParameterList.Add(new BoolStringClass("LeftABButtons", config.LeftABButtons.enabled, config.LeftABButtons.always, "Boolean", "Infl. by A,B", false, false, false, "Hidden"));
            ParameterList.Add(new BoolStringClass("RightABButtons", config.RightABButtons.enabled, config.RightABButtons.always, "Boolean", "Infl. by A,B", false, false, false, "Hidden"));

            foreach (Action a in config.ConcatenateActions()) {
                if (a.type != "vector2")
                {
                    ParameterList.Add(new BoolStringClass((string)a.osc_parameter, (bool)a.enabled, int.Parse(a.always.ToString()), a.type == "boolean" ? "Boolean" : "Float", a.floating.ToString(), true, false, (bool)a.binary, "Hidden"));
                }
                else {
                    String[] tmp = ((JArray)a.osc_parameter).ToObject<String[]>();
                    bool[] tmp2 = ((JArray)a.enabled).ToObject<bool[]>();
                    float[] tmp3 = ((JArray)a.floating).ToObject<float[]>();
                    int[] tmp4 = ((JArray)a.always).ToObject<int[]>();
                    bool[] tmp5 = ((JArray)a.unsigned).ToObject<bool[]>();
                    bool[] tmp6 = ((JArray)a.binary).ToObject<bool[]>();
                    for (int i = 0; i < tmp.Length; i++)
                    {
                        ParameterList.Add(new BoolStringClass(tmp[i], tmp2[i], tmp4[i], i > 1 ? "Boolean" : "Float", tmp3[i] == -100 ? "Infl. by X,Y" : tmp3[i].ToString(), tmp3[i] != -100, i < 2 ? tmp5[i] : true, i < 2 ? tmp6[i] : true, i >= 2 ? "Hidden" : "Visible"));
                    }
                }
            }

            this.DataContext = this;
            Startup = false;
        }

        public class BoolStringClass
        {
            public BoolStringClass(string Text, bool IsSelected, int AlwaysSend, string Type, string Floating = "0.0", bool isEnabled = true, bool Unsigned = true, bool Binary = true, string Unsigned_Visibility = "Visible")
            {
                this.Text = Text;
                this.IsSelected = IsSelected;
                this.AlwaysSend = AlwaysSend;
                this.Type = Type;
                this.Floating = Floating;
                this.isEnabled = isEnabled;
                this.Unsigned = Unsigned;
                this.Binary = Binary;
                this.Unsigned_Visibility = Unsigned_Visibility;
                this.Binary_Visibility = this.Type == "Float" ? "Visible" : "Hidden";
            }

            public string Text { get; set; }

            public bool IsSelected { get; set; }

            public int AlwaysSend { get; set; }

            public string Type { get; set; }

            public string Floating { get; set; }

            public bool isEnabled { get; set; }

            public bool Unsigned { get; set; }

            public bool Binary { get; set; }

            public string Unsigned_Visibility { get; set; }

            public string Binary_Visibility { get; set; }

            public string DisplayString
            {
                get { return String.Format("{0,-25}\t{1}\t", Text, Type); }
            }

        }

        private void Save_Clicked(object sender, RoutedEventArgs e)
        {
            File.WriteAllText(ConfigPath, JsonConvert.SerializeObject(config, Formatting.Indented));
            Close();
        }


        private void CheckBox_Checked_Unsigned(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;

            CheckBox checkBox = sender as CheckBox;

            bool check = (bool)checkBox.IsChecked;
            string name = checkBox.ToolTip.ToString();

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.unsigned);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.unsigned = tmp2;
                            return;
                        }
                    }
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.unsigned);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.unsigned = tmp2;
                            return;
                        }
                    }
                }
            }

        }

        private void CheckBox_Checked_Binary(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;

            CheckBox checkBox = sender as CheckBox;

            bool check = (bool)checkBox.IsChecked;
            string name = checkBox.ToolTip.ToString();

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.binary);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.binary = tmp2;
                            return;
                        }
                    }
                }
                else
                {
                    if (a.osc_parameter.ToString() == name)
                        a.binary = check;
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.binary);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.binary = tmp2;
                            return;
                        }
                    }
                }
                else
                {
                    if (a.osc_parameter.ToString() == name)
                        a.binary = check;
                }
            }

        }


        private void CheckBox_Checked(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;

            CheckBox checkBox = sender as CheckBox;

            bool check = (bool)checkBox.IsChecked;
            string content = checkBox.Content.ToString();
            string name = content.Substring(0, content.IndexOf(" "));

            switch (name)
            {
                case "ControllerType":
                    config.ControllerType.enabled = check;
                    return;
                case "LeftThumb":
                    config.LeftThumb.enabled = check;
                    return;
                case "RightThumb":
                    config.RightThumb.enabled = check;
                    return;
                case "LeftABButtons":
                    config.LeftABButtons.enabled = check;
                    return;
                case "RightABButtons":
                    config.RightABButtons.enabled = check;
                    return;
            }

            foreach (Action a in config.actions)
            {
                if (a.type != "vector2")
                {
                    if (a.osc_parameter.ToString() == name)
                    {
                        a.enabled = check;
                        return;
                    }
                }
                else
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.enabled);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.enabled = tmp2;
                            return;
                        }
                    }
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type != "vector2")
                {
                    if (a.osc_parameter.ToString() == name)
                    {
                        a.enabled = check;
                        return;
                    }
                }
                else
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.enabled);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = check;
                            a.enabled = tmp2;
                            return;
                        }
                    }
                }
            }

        }

        private void TextChanged(object sender, TextChangedEventArgs e)
        {
            if (Startup)
                return;

            Tbx_Port.Text = Regex.Replace(Tbx_Port.Text, "[^0-9]", "");
            Tbx_Port.SelectionStart = Tbx_Port.Text.Length;
            Tbx_Server_Port.Text = Regex.Replace(Tbx_Server_Port.Text, "[^0-9]", "");
            Tbx_Server_Port.SelectionStart = Tbx_Server_Port.Text.Length;
            Tbx_http_port.Text = Regex.Replace(Tbx_http_port.Text, "[^0-9]", "");
            Tbx_http_port.SelectionStart = Tbx_http_port.Text.Length;
            Tbx_PollingRate.Text = Regex.Replace(Tbx_PollingRate.Text, "[^0-9]", "");
            Tbx_PollingRate.SelectionStart = Tbx_PollingRate.Text.Length;
            Tbx_StickMoveTolerance.Text = Regex.Replace(Tbx_StickMoveTolerance.Text, "[^0-9]", "");
            Tbx_StickMoveTolerance.SelectionStart = Tbx_StickMoveTolerance.Text.Length;
            Tbx_Binary.Text = Regex.Replace(Tbx_Binary.Text, "[^0-9]", "");
            Tbx_Binary.SelectionStart = Tbx_Binary.Text.Length;

            config.IP = Tbx_IP.Text;
            config.Port = Tbx_Port.Text != "" ? int.Parse(Tbx_Port.Text) : 0;
            config.Server_Port = Tbx_Server_Port.Text != "" ? int.Parse(Tbx_Server_Port.Text) : 0;
            config.HTTP_Port = Tbx_http_port.Text != "" ? int.Parse(Tbx_http_port.Text) : 0;
            config.PollingRate = Tbx_PollingRate.Text != "" ? int.Parse(Tbx_PollingRate.Text) : 0;
            config.StickMoveTolerance = Tbx_StickMoveTolerance.Text != "" ? int.Parse(Tbx_StickMoveTolerance.Text) : 0;
            config.Binary_bits = Tbx_Binary.Text != "" ? int.Parse(Tbx_Binary.Text) : 0;
        }

        private void Button_Param_Click(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            Startup = true;
            bool value = ((Button)sender).Name == "TAP";
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                item.IsSelected = value;
            }

            config.ControllerType.enabled = value;
            config.LeftThumb.enabled = value;
            config.RightThumb.enabled = value;
            config.LeftABButtons.enabled = value;
            config.RightABButtons.enabled = value;

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { value, value, value });
                    else
                        a.enabled = new JArray(new bool[2] { value, value });
                }
                else
                {
                    a.enabled = value;
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { value, value, value });
                    else
                        a.enabled = new JArray(new bool[2] { value, value });
                }
                else
                {
                    a.enabled = value;
                }
            }

            Lbx_Params.Items.Refresh();
            Startup = false;
        }

        private void Tick_all_Click(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            Startup = true;
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                item.IsSelected = true;
            }

            config.ControllerType.enabled = true;
            config.LeftThumb.enabled = true;
            config.RightThumb.enabled = true;
            config.LeftABButtons.enabled = true;
            config.RightABButtons.enabled = true;

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { true, true, true });
                    else
                        a.enabled = new JArray(new bool[2] { true, true });
                }
                else
                {
                    a.enabled = true;
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { true, true, true });
                    else
                        a.enabled = new JArray(new bool[2] { true, true });
                }
                else
                {
                    a.enabled = true;
                }
            }
            Startup = false;
            Lbx_Params.Items.Refresh();
        }

        private void Reset_OSC_Clicked(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            string appdata = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string[] folders = Directory.GetDirectories(appdata + "\\..\\LocalLow\\VRChat\\VRChat\\OSC");
            foreach (string folder in folders)
            {
                string foldername = folder.Substring(folder.LastIndexOf("\\") + 1);
                if (foldername.Contains("usr_"))
                {
                    DirectoryInfo dir = new DirectoryInfo(folder);
                    dir.Delete(true);
                }
            }
            MessageBox.Show("OSC cache cleared!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void Mode_Click(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            Startup = true;
            Button button = sender as Button;
            int value = button.Name == "ASP" ? 1 : button.Name == "AS" ? 2 : 0;

            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                item.AlwaysSend = value;
            }

            config.ControllerType.always = value;
            config.LeftThumb.always = value;
            config.RightThumb.always = value;
            config.LeftABButtons.always = value;
            config.RightABButtons.always = value;

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.always = new JArray(new int[3] { value, value, value });
                    else
                        a.always = new JArray(new int[2] { value, value });
                }
                else
                {
                    a.always = value;
                }
            }
            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.always = new JArray(new int[3] { value, value, value });
                    else
                        a.always = new JArray(new int[2] { value, value });
                }
                else
                {
                    a.always = value;
                }
            }
            Startup = false;
            Lbx_Params.Items.Refresh();
        }

        private void TextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (Startup)
                return;
            string text = ((TextBox)sender).Text;
            if (text == string.Empty || text == "-") 
                text = "0";

            for (int i = 0; i < config.actions.Count; i++)
            {
                Action a = config.actions[i];
                if (a.osc_parameter is string)
                {
                    if (a.osc_parameter.ToString() == ((TextBox)sender).ToolTip.ToString())
                    {
                        a.floating = float.Parse(text.Replace(".", ","));
                        return;
                    }
                }
                else
                {
                    string[] temp = ((JArray)a.osc_parameter).ToObject<string[]>();
                    float[] floats = null;
                    
                    if (a.floating is Single[])
                        floats = (Single[])a.floating;
                    else
                        floats = ((JArray)a.floating).ToObject<float[]>();

                    for (int j = 0; j < temp.Length; j++)
                    {
                        if (temp[j].ToString() == ((TextBox)sender).ToolTip.ToString())
                        {
                            floats[j] = float.Parse(text.Replace(".", ","));
                            config.actions[i].floating = floats;
                        }
                    }
                }

            }
            for (int i = 0; i < config.xinput_actions.Count; i++)
            {
                Action a = config.xinput_actions[i];
                if (a.osc_parameter is string)
                {
                    if (a.osc_parameter.ToString() == ((TextBox)sender).ToolTip.ToString())
                    {
                        a.floating = float.Parse(text.Replace(".", ","));
                        return;
                    }
                }
                else
                {
                    string[] temp = ((JArray)a.osc_parameter).ToObject<string[]>();
                    float[] floats = null;

                    if (a.floating is Single[])
                        floats = (Single[])a.floating;
                    else
                        floats = ((JArray)a.floating).ToObject<float[]>();

                    for (int j = 0; j < temp.Length; j++)
                    {
                        if (temp[j].ToString() == ((TextBox)sender).ToolTip.ToString())
                        {
                            floats[j] = float.Parse(text.Replace(".", ","));
                            config.xinput_actions[i].floating = floats;
                        }
                    }
                }

            }
        }

        private void TextBox_PreviewTextInput(object sender, System.Windows.Input.TextCompositionEventArgs e)
        {
            if (Startup)
                return;
            Regex regex = new Regex("[0-9,\\.-]+");
            e.Handled = !regex.IsMatch(e.Text);
        }

        private void ComboBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (Startup)
                return;
            ComboBox box = sender as ComboBox;
            string name = box.ToolTip.ToString();
            int value = box.SelectedIndex;

            switch (name)
            {
                case "ControllerType":
                    config.ControllerType.always = value;
                    return;
                case "LeftThumb":
                    config.LeftThumb.always = value;
                    return;
                case "RightThumb":
                    config.RightThumb.always = value;
                    return;
                case "LeftABButtons":
                    config.LeftABButtons.always = value;
                    return;
                case "RightABButtons":
                    config.RightABButtons.always = value;
                    return;
            }

            foreach (Action a in config.actions)
            {
                if (a.type != "vector2")
                {
                    if (a.osc_parameter.ToString() == name)
                    {
                        a.always = value;
                        return;
                    }
                }
                else
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.always);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = value;
                            a.always = tmp2;
                            return;
                        }
                    }
                }
            }

            foreach (Action a in config.xinput_actions)
            {
                if (a.type != "vector2")
                {
                    if (a.osc_parameter.ToString() == name)
                    {
                        a.always = value;
                        return;
                    }
                }
                else
                {
                    JArray tmp = ((JArray)a.osc_parameter);
                    JArray tmp2 = ((JArray)a.always);

                    for (int i = 0; i < tmp.Count; i++)
                    {
                        if (tmp[i].ToString() == name)
                        {
                            tmp2[i] = value;
                            a.always = tmp2;
                            return;
                        }
                    }
                }
            }
        }

        private void Untick_SteamVR_Parameters(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            Startup = true;
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                if (!item.Text.Contains("XInput") && item.Text != "ControllerType")
                {
                    item.IsSelected = false;
                }
            }

            config.LeftThumb.enabled = false;
            config.RightThumb.enabled = false;
            config.LeftABButtons.enabled = false;
            config.RightABButtons.enabled = false;

            foreach (Action a in config.actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { false, false, false });
                    else
                        a.enabled = new JArray(new bool[2] { false, false });
                }
                else
                {
                    a.enabled = false;
                }
            } 

            Lbx_Params.Items.Refresh();
            Startup = false;
        }

        private void Untick_XInput_Parameters(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;
            Startup = true;
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                if (item.Text.Contains("XInput"))
                {
                    item.IsSelected = false;
                }
            }

            foreach (Action a in config.xinput_actions)
            {
                if (a.type == "vector2")
                {
                    if (((JArray)a.enabled).Count > 2)
                        a.enabled = new JArray(new bool[3] { false, false, false });
                    else
                        a.enabled = new JArray(new bool[2] { false, false });
                }
                else
                {
                    a.enabled = false;
                }
            } 

            Lbx_Params.Items.Refresh();
            Startup = false;
        }
    }
}
