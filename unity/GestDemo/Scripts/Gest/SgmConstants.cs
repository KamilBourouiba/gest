namespace Gest.Runtime
{
    /// <summary>
    /// SGM v1 wire constants. Must stay aligned with include/sgm_v1.h and sgm_constants.py.
    /// </summary>
    public static class SgmConstants
    {
        public const byte Magic0 = 0x53; // S
        public const byte Magic1 = 0x47; // G
        public const byte Magic2 = 0x4D; // M
        public const byte Magic3 = 0x01;

        public const ushort FormatVersion = 1;

        public const byte KindArticulated = 1;
        public const byte KindDirection = 2;

        public const byte OpFrame = 0x30;
        public const byte OpJointsF32 = 0x31;
        public const byte OpState = 0x32;
        public const byte OpDirF32 = 0x33;
        public const byte OpEnd = 0xFF;
    }
}
