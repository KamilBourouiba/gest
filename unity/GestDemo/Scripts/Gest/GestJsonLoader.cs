using System;
using UnityEngine;

namespace Gest.Runtime
{
    [Serializable]
    public sealed class GestJsonDocument
    {
        public float fps = 60f;
        public GestFrame[] timeline = Array.Empty<GestFrame>();
    }

    public static class GestJsonLoader
    {
        public static GestClip Load(string json)
        {
            var doc = JsonUtility.FromJson<GestJsonDocument>(json);
            if (doc?.timeline == null || doc.timeline.Length == 0)
                throw new InvalidOperationException("Gesture JSON has no timeline frames.");

            return new GestClip(doc.fps, doc.timeline);
        }
    }
}
