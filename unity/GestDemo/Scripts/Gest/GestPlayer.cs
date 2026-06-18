using System;
using System.Diagnostics;
using System.IO;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace Gest.Runtime
{
    public enum GestSourceMode
    {
        SgmBytecode,
        GestJson,
    }

    /// <summary>
    /// Loads a .gest clip (JSON or SGM bytecode) and exposes sampled poses over time.
    /// </summary>
    public sealed class GestPlayer : MonoBehaviour
    {
        [Header("Source")]
        public GestSourceMode source = GestSourceMode.SgmBytecode;
        public int clipIndex;
        public string sgmAsset = "xr_pinch_grasp";
        public string gestJsonAsset = "xr_pinch_grasp.gest";

        [Header("Playback")]
        public bool playOnStart = true;
        public bool loop = true;
        public float playbackSpeed = 1f;
        public float timeOffset;

        public GestClip Clip { get; private set; }
        public GestFrame CurrentFrame { get; private set; }
        public float CurrentTime { get; private set; }
        public bool IsPlaying { get; private set; }

        public int SourceBytes { get; private set; }
        public int CompareJsonBytes { get; private set; }
        public long DecodeMicroseconds { get; private set; }
        public string SourceLabel { get; private set; }
        public string ClipLabel { get; private set; }

        public event Action<GestFrame> FrameChanged;

        void Start()
        {
            LoadClip();
            if (playOnStart)
                Play();
        }

        void Update()
        {
            if (!IsPlaying || Clip == null)
                return;

            CurrentTime += Time.deltaTime * playbackSpeed;
            var frame = Clip.Sample(CurrentTime + timeOffset, loop);
            if (!ReferenceEquals(frame, CurrentFrame))
            {
                CurrentFrame = frame;
                FrameChanged?.Invoke(frame);
            }
        }

        public void Play()
        {
            IsPlaying = true;
        }

        public void Pause()
        {
            IsPlaying = false;
        }

        public void TogglePlay()
        {
            IsPlaying = !IsPlaying;
        }

        public void Reload()
        {
            LoadClip();
        }

        public void NextClip()
        {
            clipIndex = (clipIndex + 1) % GestDemoClips.All.Length;
            ApplyClipEntry(GestDemoClips.All[clipIndex]);
            LoadClip();
        }

        public void LoadClipByIndex(int index)
        {
            clipIndex = Mathf.Clamp(index, 0, GestDemoClips.All.Length - 1);
            ApplyClipEntry(GestDemoClips.All[clipIndex]);
            LoadClip();
        }

        void ApplyClipEntry(GestDemoClips.Entry entry)
        {
            sgmAsset = entry.Id;
            gestJsonAsset = entry.JsonAsset;
            ClipLabel = entry.Label;
        }

        void LoadClip()
        {
            if (GestDemoClips.All.Length > 0)
            {
                clipIndex = Mathf.Clamp(clipIndex, 0, GestDemoClips.All.Length - 1);
                ApplyClipEntry(GestDemoClips.All[clipIndex]);
            }
            var jsonPath = Path.Combine(Application.streamingAssetsPath, gestJsonAsset + ".json");
            CompareJsonBytes = File.Exists(jsonPath) ? (int)new FileInfo(jsonPath).Length : 0;

            var sw = Stopwatch.StartNew();
            try
            {
                if (source == GestSourceMode.SgmBytecode)
                {
                    var sgmPath = Path.Combine(Application.streamingAssetsPath, sgmAsset + ".sgm");
                    var bytes = File.ReadAllBytes(sgmPath);
                    SourceBytes = bytes.Length;
                    SourceLabel = ".sgm v1 bytecode";

                    var decoder = new SgmDecoder();
                    Clip = decoder.DecodeToClip(bytes);
                }
                else
                {
                    var json = File.ReadAllText(jsonPath);
                    SourceBytes = json.Length;
                    SourceLabel = ".gest JSON";
                    Clip = GestJsonLoader.Load(json);
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[GestPlayer] Failed to load clip: {ex.Message}");
                enabled = false;
                return;
            }
            finally
            {
                sw.Stop();
                DecodeMicroseconds = sw.ElapsedTicks * 1_000_000 / Stopwatch.Frequency;
            }

            CurrentTime = 0f;
            CurrentFrame = Clip.Sample(0f, false);
            FrameChanged?.Invoke(CurrentFrame);

            Debug.Log(
                $"[GestPlayer] Loaded {SourceLabel} ({SourceBytes} bytes) in {DecodeMicroseconds} µs, " +
                $"{Clip.Frames.Count} frames @ {Clip.Fps:0.#} fps.");
        }
    }
}
