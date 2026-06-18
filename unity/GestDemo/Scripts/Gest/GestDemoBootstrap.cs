using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Ensures the gesture demo exists when you press Play in any scene.
    /// </summary>
    public static class GestDemoBootstrap
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void EnsureDemo()
        {
            if (Object.FindFirstObjectByType<GestPlayer>() != null)
                return;

            var demo = new GameObject("GestDemo");
            demo.AddComponent<GestPlayer>();
            demo.AddComponent<GestHumanoidVisualizer>();
            demo.AddComponent<GestDemoHud>();

            GestDemoEnvironment.Ensure();

            Debug.Log("[Gest] Auto-bootstrapped GestDemo with humanoid IK (or procedural fallback).");
        }
    }
}
