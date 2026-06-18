using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Loads a rigged humanoid (Xbot) and retargets .gest channels via Humanoid IK.
    /// Falls back to procedural capsules when no prefab is available.
    /// </summary>
    [RequireComponent(typeof(GestPlayer))]
    public sealed class GestHumanoidVisualizer : MonoBehaviour
    {
        [Tooltip("Optional. If unset, tries Resources/GestXbot.prefab (create via Gest → Build Mannequin Prefab).")]
        public GameObject humanoidPrefab;

        public float modelScale = 0.95f;
        public Vector3 modelEuler = new Vector3(0f, 180f, 0f);

        GestPlayer _player;
        Transform _leftTarget;
        Transform _rightTarget;
        Transform _gazeTarget;
        GestMannequinVisualizer _fallback;

        void Awake()
        {
            _player = GetComponent<GestPlayer>();
            var prefab = humanoidPrefab != null ? humanoidPrefab : Resources.Load<GameObject>("GestXbot");
            if (prefab == null)
            {
                _fallback = gameObject.AddComponent<GestMannequinVisualizer>();
                Debug.LogWarning("[Gest] No GestXbot prefab found — using procedural mannequin. Run Gest → Build Mannequin Prefab.");
                return;
            }

            var instance = Instantiate(prefab, transform);
            instance.name = "GestXbot";
            instance.transform.localPosition = Vector3.zero;
            instance.transform.localRotation = Quaternion.Euler(modelEuler);
            instance.transform.localScale = Vector3.one * modelScale;

            var animator = instance.GetComponentInChildren<Animator>();
            if (animator == null || !animator.isHuman)
            {
                Destroy(instance);
                _fallback = gameObject.AddComponent<GestMannequinVisualizer>();
                Debug.LogWarning("[Gest] Mannequin prefab is not a Humanoid — procedural fallback.");
                return;
            }

            animator.applyRootMotion = false;

            _leftTarget = new GameObject("LeftHandTarget").transform;
            _rightTarget = new GameObject("RightHandTarget").transform;
            _gazeTarget = new GameObject("GazeTarget").transform;
            _leftTarget.SetParent(transform, false);
            _rightTarget.SetParent(transform, false);
            _gazeTarget.SetParent(transform, false);

            var ik = animator.gameObject.AddComponent<GestHumanoidIkDriver>();
            ik.leftHandTarget = _leftTarget;
            ik.rightHandTarget = _rightTarget;
            ik.gazeTarget = _gazeTarget;
        }

        void OnEnable()
        {
            if (_player != null)
                _player.FrameChanged += OnFrame;
        }

        void OnDisable()
        {
            if (_player != null)
                _player.FrameChanged -= OnFrame;
        }

        void OnFrame(GestFrame frame)
        {
            if (_fallback != null || frame == null)
                return;

            var skel = GestRigPose.FromFrame(frame);
            _leftTarget.position = skel.LeftWrist;
            _rightTarget.position = skel.RightWrist;
            _gazeTarget.position = skel.GazeEnd;
        }
    }
}
