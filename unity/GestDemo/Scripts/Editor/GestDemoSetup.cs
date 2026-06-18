#if UNITY_EDITOR
using Gest.Runtime;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class GestDemoSetup
{
    const string ScenePath = "Assets/Scenes/SampleScene.unity";

    [MenuItem("Gest/Setup Demo Scene")]
    public static void SetupDemoScene()
    {
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            return;

        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        ConfigureScene();
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        Debug.Log("[Gest] Demo scene ready. Press Play to run the mannequin + SGM playback.");
    }

    public static void SetupDemoSceneBatch()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        ConfigureScene();
        EditorSceneManager.SaveScene(scene);
        EditorApplication.Exit(0);
    }

    static void ConfigureScene()
    {
        var existing = GameObject.Find("GestDemo");
        if (existing != null)
            Object.DestroyImmediate(existing);

        var demo = new GameObject("GestDemo");
        demo.AddComponent<GestPlayer>();
        demo.AddComponent<GestHumanoidVisualizer>();
        demo.AddComponent<GestDemoHud>();

        GestDemoEnvironment.Ensure();

        var light = Object.FindFirstObjectByType<Light>();
        if (light != null)
        {
            light.type = LightType.Directional;
            light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            light.intensity = 1.1f;
        }
    }
}
#endif
