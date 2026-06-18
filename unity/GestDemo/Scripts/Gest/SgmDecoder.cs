using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace Gest.Runtime
{
    public sealed class SgmDecodeException : Exception
    {
        public SgmDecodeException(string message) : base(message) { }
    }

    public enum SgmChannelKind
    {
        Articulated,
        Direction,
    }

    public sealed class SgmChannelInfo
    {
        public string Name;
        public SgmChannelKind Kind;
        public int JointCount;
        public int StateCount;
    }

    public sealed class SgmDecoder
    {
        public float Fps { get; private set; }
        public List<SgmChannelInfo> Channels { get; } = new List<SgmChannelInfo>();

        public GestClip DecodeToClip(byte[] data)
        {
            using var stream = new MemoryStream(data);
            using var reader = new BinaryReader(stream, Encoding.UTF8, leaveOpen: true);

            var magic = reader.ReadBytes(4);
            if (magic.Length != 4 ||
                magic[0] != SgmConstants.Magic0 ||
                magic[1] != SgmConstants.Magic1 ||
                magic[2] != SgmConstants.Magic2 ||
                magic[3] != SgmConstants.Magic3)
            {
                throw new SgmDecodeException("Bad SGM magic header.");
            }

            var version = reader.ReadUInt16();
            if (version != SgmConstants.FormatVersion)
                throw new SgmDecodeException($"Unsupported SGM version {version}.");

            Fps = reader.ReadSingle();
            var channelCount = reader.ReadUInt16();
            Channels.Clear();

            for (var i = 0; i < channelCount; i++)
            {
                var kindByte = reader.ReadByte();
                var nameLen = reader.ReadByte();
                var name = Encoding.UTF8.GetString(reader.ReadBytes(nameLen));
                var info = new SgmChannelInfo { Name = name };

                if (kindByte == SgmConstants.KindArticulated)
                {
                    info.Kind = SgmChannelKind.Articulated;
                    info.JointCount = reader.ReadUInt16();
                    info.StateCount = reader.ReadUInt16();
                }
                else if (kindByte == SgmConstants.KindDirection)
                {
                    info.Kind = SgmChannelKind.Direction;
                }
                else
                {
                    throw new SgmDecodeException($"Unknown channel kind {kindByte} for {name}.");
                }

                Channels.Add(info);
            }

            var frames = BuildTimeline(reader);
            return new GestClip(Fps, frames);
        }

        List<GestFrame> BuildTimeline(BinaryReader reader)
        {
            var timeline = new List<GestFrame>();
            GestFrame current = null;

            void Flush()
            {
                if (current != null)
                    timeline.Add(current);
                current = null;
            }

            while (reader.BaseStream.Position < reader.BaseStream.Length)
            {
                var op = reader.ReadByte();
                switch (op)
                {
                    case SgmConstants.OpEnd:
                        Flush();
                        return timeline;

                    case SgmConstants.OpFrame:
                        Flush();
                        current = new GestFrame { t = (float)reader.ReadDouble(), pose = new GestPose() };
                        break;

                    case SgmConstants.OpJointsF32:
                    {
                        var channelId = reader.ReadUInt16();
                        var floatCount = reader.ReadUInt32();
                        var values = new float[floatCount];
                        for (var i = 0; i < floatCount; i++)
                            values[i] = reader.ReadSingle();
                        ApplyJoints(current, channelId, values);
                        break;
                    }

                    case SgmConstants.OpState:
                    {
                        var channelId = reader.ReadUInt16();
                        var stateIndex = reader.ReadUInt16();
                        ApplyState(current, channelId, stateIndex);
                        break;
                    }

                    case SgmConstants.OpDirF32:
                    {
                        var channelId = reader.ReadUInt16();
                        var dir = new[] { reader.ReadSingle(), reader.ReadSingle(), reader.ReadSingle() };
                        ApplyDirection(current, channelId, dir);
                        break;
                    }

                    default:
                        throw new SgmDecodeException($"Unknown opcode 0x{op:X2}.");
                }
            }

            Flush();
            return timeline;
        }

        void ApplyJoints(GestFrame frame, int channelId, float[] values)
        {
            if (frame == null || channelId < 0 || channelId >= Channels.Count)
                return;

            var hand = GetOrCreateHand(frame.pose, Channels[channelId].Name);
            hand.joints = new JointBlock { values = values };
        }

        void ApplyState(GestFrame frame, int channelId, int stateIndex)
        {
            if (frame == null || channelId < 0 || channelId >= Channels.Count)
                return;

            var hand = GetOrCreateHand(frame.pose, Channels[channelId].Name);
            hand.state_index = stateIndex;
        }

        void ApplyDirection(GestFrame frame, int channelId, float[] dir)
        {
            if (frame == null || channelId < 0 || channelId >= Channels.Count)
                return;

            if (Channels[channelId].Name == "gaze")
                frame.pose.gaze = new GazeChannel { dir = dir };
        }

        static HandChannel GetOrCreateHand(GestPose pose, string channelName)
        {
            switch (channelName)
            {
                case "left_hand":
                    pose.left_hand ??= new HandChannel();
                    return pose.left_hand;
                case "right_hand":
                    pose.right_hand ??= new HandChannel();
                    return pose.right_hand;
                default:
                    pose.left_hand ??= new HandChannel();
                    return pose.left_hand;
            }
        }
    }
}
