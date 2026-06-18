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
            new Entry("xr_pinch_grasp", "XR pinch & grasp", "xr_pinch_grasp.gest"),
            new Entry("assembly_pick_place", "Assembly pick & place", "assembly_pick_place.gest"),
            new Entry("presentation_sweep", "Presentation sweep", "presentation_sweep.gest"),
            new Entry("robot_teleop_reach", "Robot teleop reach", "robot_teleop_reach.gest"),
            new Entry("xr_dual_hand_arc", "XR legacy alias", "xr_dual_hand_arc.gest"),
        };
    }
}
