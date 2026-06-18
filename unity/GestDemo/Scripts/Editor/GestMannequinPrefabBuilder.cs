#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

public static class GestMannequinPrefabBuilder
{
    const string ModelPath = "Assets/GestDemo/Models/mannequin.glb";
    const string PrefabPath = "Assets/Resources/GestXbot.prefab";
    const string ControllerPath = "Assets/Resources/GestXbotIdle.controller";

    [MenuItem("Gest/Build Mannequin Prefab")]
    public static void BuildMannequinPrefab()
    {
        if (!File.Exists(ModelPath))
        {
            Debug.LogError($"[Gest] Missing model at {ModelPath}. Copy demo/assets/mannequin.glb into the Unity project.");
            return;
        }

        var source = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        if (source == null)
        {
            Debug.LogError("[Gest] Could not load mannequin.glb — wait for import or reimport the model.");
            return;
        }

        Directory.CreateDirectory("Assets/Resources");

        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        if (controller == null)
        {
            controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            controller.layers[0].iKPass = true;
        }

        var instance = Object.Instantiate(source);
        instance.name = "GestXbot";
        var animator = instance.GetComponentInChildren<Animator>();
        if (animator != null)
        {
            animator.applyRootMotion = false;
            animator.runtimeAnimatorController = controller;
        }

        PrefabUtility.SaveAsPrefabAsset(instance, PrefabPath);
        Object.DestroyImmediate(instance);
        AssetDatabase.SaveAssets();
        Debug.Log($"[Gest] Wrote {PrefabPath}. Press Play for Humanoid IK driven by .gest.");
    }
}
#endif
