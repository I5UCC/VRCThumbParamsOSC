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
            Tbx_PollingRate.Text = config.PollingRate.ToString();
            Tbx_StickMoveTolerance.Text = config.StickMoveTolerance.ToString();

            ParameterList.Add(new BoolStringClass("ControllerType", config.ControllerType.enabled, "Integer", "Unavailable"));
            ParameterList.Add(new BoolStringClass("LeftThumb", config.LeftThumb, "Integer", "Influenced by bools"));
            ParameterList.Add(new BoolStringClass("RightThumb", config.RightThumb, "Integer", "Influenced by bools"));

            ParameterList.Add(new BoolStringClass("LeftABButtons", config.LeftABButtons, "Boolean", "Influenced by A,B"));
            ParameterList.Add(new BoolStringClass("RightABButtons", config.RightABButtons, "Boolean", "Influenced by A,B"));

            foreach (Action a in config.actions) {
                if (a.type != "vector2")
                {
                    ParameterList.Add(new BoolStringClass((string)a.osc_parameter, (bool)a.enabled, a.type == "boolean" ? "Boolean" : "Float", a.floating.ToString()));
                }
                else {
                    String[] tmp = ((JArray)a.osc_parameter).ToObject<String[]>();
                    bool[] tmp2 = ((JArray)a.enabled).ToObject<bool[]>();
                    float[] tmp3 = ((JArray)a.floating).ToObject<float[]>();
                    for (int i = 0; i < tmp.Length; i++)
                    {
                        ParameterList.Add(new BoolStringClass(tmp[i], tmp2[i], i > 1 ? "Boolean" : "Float", tmp3[i] == -100 ? "Influenced by X,Y" : tmp3[i].ToString()));
                    }
                }
            }

            this.DataContext = this;
            Startup = false;
        }

        public class BoolStringClass
        {
            public BoolStringClass(string Text, bool IsSelected, string Type, string Floating = "0.0")
            {
                this.Text = Text;
                this.IsSelected = IsSelected;
                this.Type = Type;
                this.Floating = Floating;
            }

            public string Text { get; set; }

            public bool IsSelected { get; set; }

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
                    config.LeftThumb = check;
                    return;
                case "RightThumb":
                    config.RightThumb = check;
                    return;
                case "LeftABButtons":
                    config.LeftABButtons = check;
                    return;
                case "RightABButtons":
                    config.RightABButtons = check;
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
            Tbx_PollingRate.Text = Regex.Replace(Tbx_PollingRate.Text, "[^0-9]", "");
            Tbx_PollingRate.SelectionStart = Tbx_PollingRate.Text.Length;
            Tbx_StickMoveTolerance.Text = Regex.Replace(Tbx_StickMoveTolerance.Text, "[^0-9]", "");
            Tbx_StickMoveTolerance.SelectionStart = Tbx_StickMoveTolerance.Text.Length;

            config.IP = Tbx_IP.Text;
            config.Port = int.Parse(Tbx_Port.Text);
            config.PollingRate = int.Parse(Tbx_PollingRate.Text);
            config.StickMoveTolerance = int.Parse(Tbx_StickMoveTolerance.Text);
        }

        private void Untick_all_Click(object sender, RoutedEventArgs e)
        {
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                item.IsSelected = false;
            }

            config.ControllerType.enabled = false;
            config.LeftThumb = false;
            config.RightThumb = false;
            config.LeftABButtons = false;
            config.RightABButtons = false;

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
                    a.enabled = false;
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
            config.LeftThumb = true;
            config.RightThumb = true;
            config.LeftABButtons = true;
            config.RightABButtons = true;

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

        private void Untick_Click_Click(object sender, RoutedEventArgs e)
        {
            for (int i = 10; i < 18 ; i++)
            {
                (Lbx_Params.Items[i + 3] as BoolStringClass).IsSelected = false;
                config.actions[i].enabled = false;
            }
            Lbx_Params.Items.Refresh();
        }

        private void Untick_Touch_Click(object sender, RoutedEventArgs e)
        {
            for (int i = 0; i < 10; i++)
            {
                (Lbx_Params.Items[i + 3] as BoolStringClass).IsSelected = false;
                config.actions[i].enabled = false;
            }
            Lbx_Params.Items.Refresh();
        }

        private void Untick_Position_Click(object sender, RoutedEventArgs e)
        {
            foreach (BoolStringClass item in Lbx_Params.Items)
            {
                if (item.Type == "Float")
                {
                    item.IsSelected = false;
                }
            }

            foreach (Action a in config.actions)
            {
                if (a.type == "boolean")
                    continue;

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
            if (text == string.Empty || text == "-") { return; }
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
