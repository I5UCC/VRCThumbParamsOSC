using System;
using System.Windows;
using System.IO;
using System.Collections.ObjectModel;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System.Windows.Controls;
using System.Text.RegularExpressions;

namespace Configurator
{
    public partial class MainWindow : Window
    {
        public ObservableCollection<BoolStringClass> ParameterList { get; set; }
        private Config config;
        private string ConfigPath;
        private bool Startup;
        private string[] disabled_inputs = { "ControllerType", "LeftThumb", "RightThumb", "LeftABButtons", "RightABButtons", "LeftStickMoved", "RightStickMoved" };

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

            ParameterList.Add(new BoolStringClass("ControllerType", config.ControllerType.enabled, config.ControllerType.always, "Integer", "Unavailable"));
            ParameterList.Add(new BoolStringClass("LeftThumb", config.LeftThumb.enabled, config.LeftThumb.always, "Integer", "Influenced by bools"));
            ParameterList.Add(new BoolStringClass("RightThumb", config.RightThumb.enabled, config.RightThumb.always, "Integer", "Influenced by bools"));

            ParameterList.Add(new BoolStringClass("LeftABButtons", config.LeftABButtons.enabled, config.LeftABButtons.always, "Boolean", "Influenced by A,B"));
            ParameterList.Add(new BoolStringClass("RightABButtons", config.RightABButtons.enabled, config.RightABButtons.always, "Boolean", "Influenced by A,B"));

            foreach (Action a in config.actions) {
                if (a.type != "vector2")
                {
                    ParameterList.Add(new BoolStringClass((string)a.osc_parameter, (bool)a.enabled, (bool)a.always, a.type == "boolean" ? "Boolean" : "Float", a.floating.ToString()));
                }
                else {
                    String[] tmp = ((JArray)a.osc_parameter).ToObject<String[]>();
                    bool[] tmp2 = ((JArray)a.enabled).ToObject<bool[]>();
                    float[] tmp3 = ((JArray)a.floating).ToObject<float[]>();
                    bool[] tmp4 = ((JArray)a.always).ToObject<bool[]>();
                    for (int i = 0; i < tmp.Length; i++)
                    {
                        ParameterList.Add(new BoolStringClass(tmp[i], tmp2[i], tmp4[i], i > 1 ? "Boolean" : "Float", tmp3[i] == -100 ? "Influenced by X,Y" : tmp3[i].ToString()));
                    }
                }
            }

            this.DataContext = this;
            Startup = false;
        }

        public class BoolStringClass
        {
            public BoolStringClass(string Text, bool IsSelected, bool AlwaysSend, string Type, string Floating = "0.0")
            {
                this.Text = Text;
                this.IsSelected = IsSelected;
                this.AlwaysSend = AlwaysSend;
                this.Type = Type;
                this.Floating = Floating;
            }

            public string Text { get; set; }

            public bool IsSelected { get; set; }

            public bool AlwaysSend { get; set; }

            public string Type { get; set; }

            public string Floating { get; set; }

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


        private void CheckBox_Checked_AS(object sender, RoutedEventArgs e)
        {
            if (Startup)
                return;

            CheckBox checkBox = sender as CheckBox;

            bool check = (bool)checkBox.IsChecked;
            string name = checkBox.ToolTip.ToString();

            switch (name)
            {
                case "ControllerType":
                    config.ControllerType.always = check;
                    return;
                case "LeftThumb":
                    config.LeftThumb.always = check;
                    return;
                case "RightThumb":
                    config.RightThumb.always = check;
                    return;
                case "LeftABButtons":
                    config.LeftABButtons.always = check;
                    return;
                case "RightABButtons":
                    config.RightABButtons.always = check;
                    return;
            }

            foreach (Action a in config.actions)
            {
                if (a.type != "vector2")
                {
                    if (a.osc_parameter.ToString() == name)
                    {
                        a.always = check;
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
                            tmp2[i] = check;
                            a.always = tmp2;
                            return;
                        }
                    }
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

            config.IP = Tbx_IP.Text;
            config.Port = int.Parse(Tbx_Port.Text);
            config.Server_Port = int.Parse(Tbx_Server_Port.Text);
            config.HTTP_Port = int.Parse(Tbx_http_port.Text);
            config.PollingRate = int.Parse(Tbx_PollingRate.Text);
            config.StickMoveTolerance = int.Parse(Tbx_StickMoveTolerance.Text);
        }

        private void Button_AS_Click(object sender, RoutedEventArgs e)
        {
            bool value = ((Button)sender).Name == "TAAS";
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
                    if (((JArray)a.always).Count > 2)
                        a.always = new JArray(new bool[3]);
                    else
                        a.always = new JArray(new bool[2]);
                }
                else
                {
                    a.always = value;
                }
            }

            Lbx_Params.Items.Refresh();
        }

        private void Button_Param_Click(object sender, RoutedEventArgs e)
        {
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
                        a.enabled = new JArray(new bool[3]);
                    else
                        a.enabled = new JArray(new bool[2]);
                }
                else
                {
                    a.enabled = value;
                }
            }

            Lbx_Params.Items.Refresh();
        }

        private void Tick_all_Click(object sender, RoutedEventArgs e)
        {
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

            Lbx_Params.Items.Refresh();
        }

        private void Reset_OSC_Clicked(object sender, RoutedEventArgs e)
        {
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

        private void TextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            string text = ((TextBox)sender).Text;
            if (text == string.Empty || text == "-") { text = "0"; }
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
        }

        private void TextBox_PreviewTextInput(object sender, System.Windows.Input.TextCompositionEventArgs e)
        {
            if (Array.IndexOf(disabled_inputs, ((TextBox)sender).ToolTip.ToString()) >= 0)
            {
                e.Handled = true;
                return;
            }
            Regex regex = new Regex("[0-9,\\.-]+");
            e.Handled = !regex.IsMatch(e.Text);
        }
    }
}
