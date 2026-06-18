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
            demo.AddComponent<GestMannequinVisualizer>();
            demo.AddComponent<GestDemoHud>();

            GestDemoEnvironment.Ensure();

            Debug.Log("[Gest] Auto-bootstrapped GestDemo with mannequin. SGM bytecode playback is ready.");
        }
    }
}
