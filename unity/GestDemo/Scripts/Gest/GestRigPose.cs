using System.Collections.Generic;
using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Canonical humanoid landmarks derived from .gest hand and gaze channels.
    /// </summary>
    public sealed class GestRigSkeleton
    {
        public Vector3 Pelvis;
        public Vector3 Chest;
        public Vector3 Neck;
        public Vector3 Head;
        public Vector3 LeftShoulder;
        public Vector3 RightShoulder;
        public Vector3 LeftHip;
        public Vector3 RightHip;
        public Vector3 LeftKnee;
        public Vector3 RightKnee;
        public Vector3 LeftAnkle;
        public Vector3 RightAnkle;
        public List<Vector3> LeftHand = new List<Vector3>();
        public List<Vector3> RightHand = new List<Vector3>();
        public Vector3 GazeDir;

        public Vector3 LeftElbow =>
            LeftHand.Count > 0 ? Vector3.Lerp(LeftShoulder, LeftHand[0], 0.55f) : LeftShoulder;

        public Vector3 RightElbow =>
            RightHand.Count > 0 ? Vector3.Lerp(RightShoulder, RightHand[0], 0.55f) : RightShoulder;

        public Vector3 LeftWrist => LeftHand.Count > 0 ? LeftHand[0] : LeftElbow;
        public Vector3 RightWrist => RightHand.Count > 0 ? RightHand[0] : RightElbow;
        public Vector3 GazeEnd => Head + GazeDir.normalized * 0.55f;
    }

    public static class GestRigPose
    {
        public static GestRigSkeleton FromFrame(GestFrame frame)
        {
            var skel = new GestRigSkeleton
            {
                Pelvis = GestSpace.ToUnity(0f, 0.92f, 0.05f),
                Chest = GestSpace.ToUnity(0f, 1.28f, 0.08f),
                Neck = GestSpace.ToUnity(0f, 1.50f, 0.05f),
                Head = GestSpace.ToUnity(0f, 1.64f, 0.03f),
                LeftShoulder = GestSpace.ToUnity(-0.22f, 1.42f, 0.08f),
                RightShoulder = GestSpace.ToUnity(0.22f, 1.42f, 0.08f),
            };

            skel.LeftHip = skel.Pelvis + new Vector3(-0.10f, -0.02f, 0.01f);
            skel.RightHip = skel.Pelvis + new Vector3(0.10f, -0.02f, 0.01f);
            skel.LeftKnee = skel.LeftHip + new Vector3(0f, -0.42f, 0.03f);
            skel.RightKnee = skel.RightHip + new Vector3(0f, -0.42f, 0.03f);
            skel.LeftAnkle = skel.LeftKnee + new Vector3(0f, -0.42f, 0f);
            skel.RightAnkle = skel.RightKnee + new Vector3(0f, -0.42f, 0f);

            if (frame?.pose != null)
            {
                skel.LeftHand = GestClip.JointPoints(frame.pose.left_hand);
                skel.RightHand = GestClip.JointPoints(frame.pose.right_hand);
                var gaze = frame.pose.gaze?.dir ?? new float[] { 0f, 0f, 1f };
                skel.GazeDir = GestSpace.ToUnity(gaze[0], gaze[1], gaze[2]).normalized;
            }
            else
            {
                skel.GazeDir = GestSpace.ToUnity(0f, 0f, 1f);
            }

            return skel;
        }
    }
}
