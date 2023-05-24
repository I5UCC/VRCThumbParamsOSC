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

            ParameterList.Add(new BoolStringClass("ControllerType", config.ControllerType, "Integer"));
            ParameterList.Add(new BoolStringClass("LeftThumb", config.LeftThumb, "Integer"));
            ParameterList.Add(new BoolStringClass("RightThumb", config.RightThumb, "Integer"));
            ParameterList.Add(new BoolStringClass("LeftABButtons", config.RightThumb, "Boolean"));
            ParameterList.Add(new BoolStringClass("RightABButtons", config.RightThumb, "Boolean"));

            foreach (Action a in config.actions) {
                if (a.type != "vector2")
                {
                    ParameterList.Add(new BoolStringClass((string)a.osc_parameter, (bool)a.enabled, a.type == "boolean" ? "Boolean" : "Float"));
                }
                else {
                    String[] tmp = ((JArray)a.osc_parameter).ToObject<String[]>();
                    bool[] tmp2 = ((JArray)a.enabled).ToObject<bool[]>();
                    for (int i = 0; i < tmp.Length; i++)
                    {
                        ParameterList.Add(new BoolStringClass(tmp[i], tmp2[i], i > 1 ? "Boolean" : "Float"));
                    }
                }
            }

            this.DataContext = this;
            Startup = false;
        }

        public class BoolStringClass
        {
            public BoolStringClass(string Text, bool IsSelected, string Type)
            {
                this.Text = Text;
                this.IsSelected = IsSelected;
                this.Type = Type;
            }

            public string Text { get; set; }

            public bool IsSelected { get; set; }

            public string Type { get; set; }

            public string DisplayString
            {
                get { return String.Format("{0,-23}", Text) + "\t" + Type; }
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
                    config.ControllerType = check;
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
                    String[] tmp = ((JArray)a.osc_parameter).ToObject<string[]>();
                    bool[] tmp2 = ((JArray)a.enabled).ToObject<bool[]>();

                    for (int i = 0; i < tmp.Length; i++)
                    {
                        if (tmp[i] == name)
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

            config.ControllerType = false;
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

            config.ControllerType = true;
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
    }
}
