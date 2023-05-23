using System.Collections.Generic;

namespace Configurator
{
    public class Action
    {
        public string name { get; set; }
        public string type { get; set; }
        public object osc_parameter { get; set; }
        public object enabled { get; set; }
    }

    public class DefaultBinding
    {
        public string controller_type { get; set; }
        public string binding_url { get; set; }
    }

    public class Config
    {
        public string IP { get; set; }
        public int Port { get; set; }
        public int PollingRate { get; set; }
        public int StickMoveTolerance { get; set; }
        public bool ControllerType { get; set; }
        public bool LeftThumb { get; set; }
        public bool RightThumb { get; set; }
        public List<DefaultBinding> default_bindings { get; set; }
        public List<Action> actions { get; set; }
    }

}