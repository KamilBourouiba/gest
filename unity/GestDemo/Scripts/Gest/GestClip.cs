using System;
using System.Collections.Generic;
using UnityEngine;

namespace Gest.Runtime
{
    [Serializable]
    public sealed class GestFrame
    {
        public float t;
        public GestPose pose = new GestPose();
    }

    [Serializable]
    public sealed class GestPose
    {
        public HandChannel left_hand = new HandChannel();
        public HandChannel right_hand = new HandChannel();
        public GazeChannel gaze = new GazeChannel();
    }

    [Serializable]
    public sealed class HandChannel
    {
        public JointBlock joints = new JointBlock();
        public int state_index;
    }

    [Serializable]
    public sealed class JointBlock
    {
        public float[] values = Array.Empty<float>();
    }

    [Serializable]
    public sealed class GazeChannel
    {
        public float[] dir = new float[] { 0f, 0f, 1f };
    }

    public sealed class GestClip
    {
        public float Fps { get; }
        public float Duration { get; }
        public IReadOnlyList<GestFrame> Frames { get; }

        public GestClip(float fps, IList<GestFrame> frames)
        {
            if (frames == null || frames.Count == 0)
                throw new ArgumentException("Gesture clip must contain at least one frame.");

            Fps = fps;
            Frames = new List<GestFrame>(frames);
            Duration = frames[frames.Count - 1].t;
        }

        public GestFrame Sample(float time, bool loop = true)
        {
            var frames = Frames;
            if (loop && Duration > 0f)
                time = Mathf.Repeat(time, Duration);

            if (time <= frames[0].t)
                return frames[0];
            if (time >= frames[frames.Count - 1].t)
                return frames[frames.Count - 1];

            for (var i = 0; i < frames.Count - 1; i++)
            {
                var a = frames[i];
                var b = frames[i + 1];
                if (a.t <= time && time <= b.t)
                    return LerpFrame(a, b, Mathf.InverseLerp(a.t, b.t, time));
            }

            return frames[0];
        }

        static GestFrame LerpFrame(GestFrame a, GestFrame b, float u)
        {
            return new GestFrame
            {
                t = Mathf.Lerp(a.t, b.t, u),
                pose = new GestPose
                {
                    left_hand = LerpHand(a.pose.left_hand, b.pose.left_hand, u),
                    right_hand = LerpHand(a.pose.right_hand, b.pose.right_hand, u),
                    gaze = LerpGaze(a.pose.gaze, b.pose.gaze, u),
                },
            };
        }

        static HandChannel LerpHand(HandChannel a, HandChannel b, float u)
        {
            return new HandChannel
            {
                state_index = u < 0.5f ? a.state_index : b.state_index,
                joints = new JointBlock
                {
                    values = LerpValues(a.joints.values, b.joints.values, u),
                },
            };
        }

        static GazeChannel LerpGaze(GazeChannel a, GazeChannel b, float u)
        {
            var av = a.dir ?? new float[] { 0f, 0f, 1f };
            var bv = b.dir ?? new float[] { 0f, 0f, 1f };
            return new GazeChannel
            {
                dir = new[]
                {
                    Mathf.Lerp(av[0], bv[0], u),
                    Mathf.Lerp(av[1], bv[1], u),
                    Mathf.Lerp(av[2], bv[2], u),
                },
            };
        }

        static float[] LerpValues(float[] a, float[] b, float u)
        {
            if (a == null || b == null || a.Length == 0)
                return b ?? Array.Empty<float>();
            if (a.Length != b.Length)
                return a;

            var outVals = new float[a.Length];
            for (var i = 0; i < a.Length; i++)
                outVals[i] = Mathf.Lerp(a[i], b[i], u);
            return outVals;
        }

        public static List<Vector3> JointPoints(HandChannel hand)
        {
            var vals = hand?.joints?.values ?? Array.Empty<float>();
            var pts = new List<Vector3>(vals.Length / 3);
            for (var i = 0; i + 2 < vals.Length; i += 3)
                pts.Add(GestSpace.ToUnity(vals[i], vals[i + 1], vals[i + 2]));
            return pts;
        }
    }
}
