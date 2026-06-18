using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Drives Humanoid IK goals from .gest hand targets and gaze.
    /// </summary>
    [RequireComponent(typeof(Animator))]
    public sealed class GestHumanoidIkDriver : MonoBehaviour
    {
        public Transform leftHandTarget;
        public Transform rightHandTarget;
        public Transform gazeTarget;

        Animator _animator;

        void Awake()
        {
            _animator = GetComponent<Animator>();
        }

        void OnAnimatorIK(int layerIndex)
        {
            if (_animator == null || !_animator.isHuman)
                return;

            ApplyHand(AvatarIKGoal.LeftHand, leftHandTarget);
            ApplyHand(AvatarIKGoal.RightHand, rightHandTarget);

            if (gazeTarget != null)
            {
                _animator.SetLookAtWeight(0.85f, 0.2f, 1f, 1f, 0.5f);
                _animator.SetLookAtPosition(gazeTarget.position);
            }
        }

        void ApplyHand(AvatarIKGoal goal, Transform target)
        {
            if (target == null)
                return;
            _animator.SetIKPositionWeight(goal, 1f);
            _animator.SetIKRotationWeight(goal, 0.35f);
            _animator.SetIKPosition(goal, target.position);
            _animator.SetIKRotation(goal, target.rotation);
        }
    }
}
