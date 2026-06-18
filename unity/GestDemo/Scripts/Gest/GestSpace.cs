using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// Convert .gest spatial samples (right-handed Y-up) into Unity world space.
    /// </summary>
    public static class GestSpace
    {
        public static Vector3 ToUnity(float x, float y, float z)
        {
            // Mirror Z to move from right-handed .gest space into Unity's left-handed frame.
            return new Vector3(x, y, -z);
        }

        public static Vector3 ToUnity(Vector3 gest)
        {
            return ToUnity(gest.x, gest.y, gest.z);
        }
    }
}
