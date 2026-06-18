namespace Gest.Runtime
{
    /// <summary>
    /// Built-in demo clips shipped in StreamingAssets (measured in multi_demos.py).
    /// </summary>
    public static class GestDemoClips
    {
        public readonly struct Entry
        {
            public readonly string Id;
            public readonly string Label;
            public readonly string JsonAsset;

            public Entry(string id, string label, string jsonAsset)
            {
                Id = id;
                Label = label;
                JsonAsset = jsonAsset;
            }
        }

        public static readonly Entry[] All =
        {
            new Entry("xr_dual_hand_arc", "XR dual-hand arc", "xr_dual_hand_arc.gest"),
            new Entry("robot_teleop_reach", "Robot teleop reach", "robot_teleop_reach.gest"),
        };
    }
}
