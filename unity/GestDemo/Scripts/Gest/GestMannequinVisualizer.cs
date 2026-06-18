using System.Collections.Generic;
using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Procedural mannequin (capsules + spheres) driven by .gest hand and gaze channels.
    /// </summary>
    [RequireComponent(typeof(GestPlayer))]
    public sealed class GestMannequinVisualizer : MonoBehaviour
    {
        [Header("Colors")]
        public Color bodyColor = new Color(0.88f, 0.92f, 0.98f);
        public Color leftColor = new Color(0.32f, 0.63f, 1f);
        public Color rightColor = new Color(1f, 0.54f, 0.30f);
        public Color gazeColor = new Color(0.62f, 1f, 0.75f);

        [Header("Proportions")]
        public float torsoRadius = 0.11f;
        public float limbRadius = 0.045f;
        public float fingerRadius = 0.014f;
        public float headRadius = 0.095f;

        GestPlayer _player;
        Transform _root;
        Material _bodyMat;
        Material _leftMat;
        Material _rightMat;
        Material _gazeMat;

        readonly List<Limb> _limbs = new List<Limb>();

        sealed class Limb
        {
            public Transform Transform;
            public bool Sphere;
        }

        void Awake()
        {
            _player = GetComponent<GestPlayer>();
            BuildMannequin();
        }

        void OnEnable()
        {
            _player.FrameChanged += OnFrame;
        }

        void OnDisable()
        {
            _player.FrameChanged -= OnFrame;
        }

        void BuildMannequin()
        {
            _root = new GameObject("GestMannequin").transform;
            _root.SetParent(transform, false);

            _bodyMat = CreateMaterial(bodyColor, 0.42f);
            _leftMat = CreateMaterial(leftColor, 0.55f);
            _rightMat = CreateMaterial(rightColor, 0.55f);
            _gazeMat = CreateMaterial(gazeColor, 0.75f);

            // Torso + legs (static lower body)
            AddCapsule("torso", _bodyMat);
            AddCapsule("chest", _bodyMat);
            AddCapsule("neck", _bodyMat);
            AddSphere("head", _bodyMat);
            AddCapsule("shoulders", _bodyMat);
            AddCapsule("l_thigh", _bodyMat);
            AddCapsule("r_thigh", _bodyMat);
            AddCapsule("l_shin", _bodyMat);
            AddCapsule("r_shin", _bodyMat);

            // Arms
            AddCapsule("l_upper_arm", _leftMat);
            AddCapsule("l_forearm", _leftMat);
            AddCapsule("r_upper_arm", _rightMat);
            AddCapsule("r_forearm", _rightMat);

            // Fingers (4 per hand)
            for (var i = 0; i < 4; i++)
            {
                AddCapsule($"l_finger_{i}", _leftMat);
                AddCapsule($"r_finger_{i}", _rightMat);
            }

            AddCapsule("gaze", _gazeMat);
            AddSphere("gaze_tip", _gazeMat);
        }

        void OnFrame(GestFrame frame)
        {
            if (frame == null || _limbs.Count == 0)
                return;

            var skel = GestRigPose.FromFrame(frame);
            var i = 0;

            PlaceCapsule(_limbs[i++], skel.Pelvis, skel.Chest, torsoRadius);
            PlaceCapsule(_limbs[i++], skel.Chest, skel.Neck, torsoRadius * 0.88f);
            PlaceCapsule(_limbs[i++], skel.Neck, skel.Head, torsoRadius * 0.55f);
            PlaceSphere(_limbs[i++], skel.Head, headRadius);
            PlaceCapsule(_limbs[i++], skel.LeftShoulder, skel.RightShoulder, torsoRadius * 0.42f);
            PlaceCapsule(_limbs[i++], skel.LeftHip, skel.LeftKnee, limbRadius * 1.15f);
            PlaceCapsule(_limbs[i++], skel.RightHip, skel.RightKnee, limbRadius * 1.15f);
            PlaceCapsule(_limbs[i++], skel.LeftKnee, skel.LeftAnkle, limbRadius);
            PlaceCapsule(_limbs[i++], skel.RightKnee, skel.RightAnkle, limbRadius);

            PlaceCapsule(_limbs[i++], skel.LeftShoulder, skel.LeftElbow, limbRadius);
            PlaceCapsule(_limbs[i++], skel.LeftElbow, skel.LeftWrist, limbRadius * 0.92f);
            PlaceCapsule(_limbs[i++], skel.RightShoulder, skel.RightElbow, limbRadius);
            PlaceCapsule(_limbs[i++], skel.RightElbow, skel.RightWrist, limbRadius * 0.92f);

            for (var f = 0; f < 4; f++)
            {
                var hasFinger = skel.LeftHand.Count > f + 1;
                if (hasFinger)
                    PlaceCapsule(_limbs[i], skel.LeftWrist, skel.LeftHand[f + 1], fingerRadius);
                else
                    HideLimb(_limbs[i]);
                i++;

                hasFinger = skel.RightHand.Count > f + 1;
                if (hasFinger)
                    PlaceCapsule(_limbs[i], skel.RightWrist, skel.RightHand[f + 1], fingerRadius);
                else
                    HideLimb(_limbs[i]);
                i++;
            }

            PlaceCapsule(_limbs[i++], skel.Head, skel.GazeEnd, fingerRadius * 0.85f);
            PlaceSphere(_limbs[i], skel.GazeEnd, fingerRadius * 1.6f);
        }

        void AddCapsule(string name, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            go.name = name;
            go.transform.SetParent(_root, false);
            DestroyCollider(go);
            go.GetComponent<Renderer>().sharedMaterial = mat;
            _limbs.Add(new Limb { Transform = go.transform, Sphere = false });
        }

        void AddSphere(string name, Material mat)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            go.name = name;
            go.transform.SetParent(_root, false);
            DestroyCollider(go);
            go.GetComponent<Renderer>().sharedMaterial = mat;
            _limbs.Add(new Limb { Transform = go.transform, Sphere = true });
        }

        static void DestroyCollider(GameObject go)
        {
            var col = go.GetComponent<Collider>();
            if (col != null)
                Destroy(col);
        }

        static void PlaceCapsule(Limb limb, Vector3 a, Vector3 b, float radius)
        {
            var t = limb.Transform;
            var dir = b - a;
            var len = dir.magnitude;
            if (len < 1e-4f)
            {
                t.gameObject.SetActive(false);
                return;
            }

            t.gameObject.SetActive(true);
            t.position = (a + b) * 0.5f;
            t.rotation = Quaternion.FromToRotation(Vector3.up, dir / len);
            t.localScale = new Vector3(radius * 2f, len * 0.5f, radius * 2f);
        }

        static void PlaceSphere(Limb limb, Vector3 center, float radius)
        {
            var t = limb.Transform;
            t.gameObject.SetActive(true);
            t.position = center;
            t.rotation = Quaternion.identity;
            t.localScale = Vector3.one * radius * 2f;
        }

        static void HideLimb(Limb limb)
        {
            limb.Transform.gameObject.SetActive(false);
        }

        static Material CreateMaterial(Color color, float smoothness)
        {
            var shader = Shader.Find("Universal Render Pipeline/Lit")
                ?? Shader.Find("Standard")
                ?? Shader.Find("Diffuse");
            var mat = new Material(shader);
            if (mat.HasProperty("_BaseColor"))
                mat.SetColor("_BaseColor", color);
            if (mat.HasProperty("_Color"))
                mat.SetColor("_Color", color);
            if (mat.HasProperty("_Smoothness"))
                mat.SetFloat("_Smoothness", smoothness);
            return mat;
        }
    }
}
