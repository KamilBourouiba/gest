using System.Collections.Generic;
using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Draws a lightweight humanoid rig driven by .gest hand and gaze channels.
    /// </summary>
    [RequireComponent(typeof(GestPlayer))]
    public sealed class GestRigVisualizer : MonoBehaviour
    {
        [Header("Style")]
        public Color bodyColor = new Color(0.88f, 0.92f, 0.98f);
        public Color leftColor = new Color(0.32f, 0.63f, 1f);
        public Color rightColor = new Color(1f, 0.54f, 0.30f);
        public Color gazeColor = new Color(0.62f, 1f, 0.75f);
        public float lineWidth = 0.01f;
        public float jointSize = 0.02f;

        GestPlayer _player;
        readonly List<LineRenderer> _lines = new List<LineRenderer>();
        readonly List<Transform> _joints = new List<Transform>();

        void Awake()
        {
            _player = GetComponent<GestPlayer>();
        }

        void OnEnable()
        {
            _player.FrameChanged += OnFrame;
        }

        void OnDisable()
        {
            _player.FrameChanged -= OnFrame;
        }

        void OnFrame(GestFrame frame)
        {
            if (frame?.pose == null)
                return;

            var skel = GestRigPose.FromFrame(frame);

            var segments = new List<(Vector3 a, Vector3 b, Color c)>
            {
                (skel.Pelvis, skel.Chest, bodyColor),
                (skel.Chest, skel.Neck, bodyColor),
                (skel.Neck, skel.Head, bodyColor),
                (skel.LeftShoulder, skel.RightShoulder, bodyColor),
            };

            if (skel.LeftHand.Count > 0)
            {
                segments.Add((skel.LeftShoulder, skel.LeftElbow, leftColor));
                segments.Add((skel.LeftElbow, skel.LeftWrist, leftColor));
                for (var i = 1; i < skel.LeftHand.Count; i++)
                    segments.Add((skel.LeftWrist, skel.LeftHand[i], leftColor));
            }

            if (skel.RightHand.Count > 0)
            {
                segments.Add((skel.RightShoulder, skel.RightElbow, rightColor));
                segments.Add((skel.RightElbow, skel.RightWrist, rightColor));
                for (var i = 1; i < skel.RightHand.Count; i++)
                    segments.Add((skel.RightWrist, skel.RightHand[i], rightColor));
            }

            segments.Add((skel.Head, skel.GazeEnd, gazeColor));
            EnsureLineCount(segments.Count);

            for (var i = 0; i < segments.Count; i++)
            {
                var seg = segments[i];
                var lr = _lines[i];
                lr.positionCount = 2;
                lr.SetPosition(0, seg.a);
                lr.SetPosition(1, seg.b);
                lr.startColor = seg.c;
                lr.endColor = seg.c;
            }

            var jointPoints = new List<Vector3> { skel.Pelvis, skel.Chest, skel.Neck, skel.Head };
            jointPoints.AddRange(skel.LeftHand);
            jointPoints.AddRange(skel.RightHand);
            jointPoints.Add(skel.GazeEnd);
            EnsureJointCount(jointPoints.Count);

            for (var i = 0; i < jointPoints.Count; i++)
                _joints[i].localPosition = jointPoints[i];
        }

        void EnsureLineCount(int count)
        {
            while (_lines.Count < count)
            {
                var go = new GameObject($"gest_line_{_lines.Count}");
                go.transform.SetParent(transform, false);
                var lr = go.AddComponent<LineRenderer>();
                lr.useWorldSpace = true;
                lr.widthMultiplier = lineWidth;
                lr.material = new Material(Shader.Find("Sprites/Default"));
                lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                lr.receiveShadows = false;
                _lines.Add(lr);
            }

            for (var i = 0; i < _lines.Count; i++)
                _lines[i].gameObject.SetActive(i < count);
        }

        void EnsureJointCount(int count)
        {
            while (_joints.Count < count)
            {
                var sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                sphere.name = $"gest_joint_{_joints.Count}";
                sphere.transform.SetParent(transform, false);
                sphere.transform.localScale = Vector3.one * jointSize;
                var col = sphere.GetComponent<Collider>();
                if (col != null)
                    Destroy(col);
                _joints.Add(sphere.transform);
            }

            for (var i = 0; i < _joints.Count; i++)
                _joints[i].gameObject.SetActive(i < count);
        }
    }
}
