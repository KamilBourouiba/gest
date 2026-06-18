using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Adds a simple ground and camera framing for the mannequin demo.
    /// </summary>
    public static class GestDemoEnvironment
    {
        public static void Ensure()
        {
            if (GameObject.Find("GestGround") == null)
            {
                var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
                ground.name = "GestGround";
                ground.transform.position = new Vector3(0f, 0.72f, 0.35f);
                ground.transform.localScale = new Vector3(0.35f, 1f, 0.35f);
                var renderer = ground.GetComponent<Renderer>();
                if (renderer != null)
                {
                    var mat = renderer.sharedMaterial;
                    if (mat != null && mat.HasProperty("_BaseColor"))
                        mat.SetColor("_BaseColor", new Color(0.08f, 0.10f, 0.14f));
                    else if (mat != null && mat.HasProperty("_Color"))
                        mat.SetColor("_Color", new Color(0.08f, 0.10f, 0.14f));
                }

                var col = ground.GetComponent<Collider>();
                if (col != null)
                    Object.Destroy(col);
            }

            var camera = Camera.main;
            if (camera != null)
            {
                camera.transform.position = new Vector3(0f, 1.35f, -2.2f);
                camera.transform.rotation = Quaternion.Euler(12f, 0f, 0f);
                camera.backgroundColor = new Color(0.03f, 0.05f, 0.08f);
            }
        }
    }
}
