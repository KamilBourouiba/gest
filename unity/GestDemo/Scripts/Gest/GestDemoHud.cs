using UnityEngine;

namespace Gest.Runtime
{
    /// <summary>
    /// On-screen panel showing decode performance and measured artifact comparison.
    /// </summary>
    [RequireComponent(typeof(GestPlayer))]
    public sealed class GestDemoHud : MonoBehaviour
    {
        public KeyCode togglePlayKey = KeyCode.Space;
        public KeyCode switchSourceKey = KeyCode.Tab;
        public KeyCode nextClipKey = KeyCode.N;

        GestPlayer _player;
        GUIStyle _box;
        GUIStyle _title;
        GUIStyle _body;

        void Awake()
        {
            _player = GetComponent<GestPlayer>();
        }

        void Update()
        {
            if (Input.GetKeyDown(togglePlayKey))
                _player.TogglePlay();

            if (Input.GetKeyDown(switchSourceKey))
            {
                _player.source = _player.source == GestSourceMode.SgmBytecode
                    ? GestSourceMode.GestJson
                    : GestSourceMode.SgmBytecode;
                _player.Reload();
            }

            if (Input.GetKeyDown(nextClipKey))
                _player.NextClip();
        }

        void OnGUI()
        {
            EnsureStyles();

            var ratio = _player.CompareJsonBytes > 0 && _player.SourceBytes > 0
                ? (float)_player.CompareJsonBytes / _player.SourceBytes
                : 0f;

            var rect = new Rect(16f, 16f, 400f, 248f);
            GUI.Box(rect, GUIContent.none, _box);

            var y = rect.y + 12f;
            GUI.Label(new Rect(rect.x + 14f, y, rect.width - 28f, 24f), ".gest Mannequin Demo", _title);
            y += 28f;

            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Clip: {_player.ClipLabel}");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Source: {_player.SourceLabel}");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Loaded bytes: {_player.SourceBytes:N0}");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Decode time: {_player.DecodeMicroseconds:N0} µs");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Compact JSON: {_player.CompareJsonBytes:N0} B ({ratio:0.00}x vs current)");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Frames: {_player.Clip?.Frames.Count ?? 0} @ {_player.Clip?.Fps:0.#} fps");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, $"Time: {_player.CurrentTime:0.000}s");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, _player.IsPlaying ? "Status: playing" : "Status: paused");
            y += 8f;
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, "[Space] play/pause  [Tab] SGM/JSON  [N] next clip");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, "github.com/KamilBourouiba/gest");
            DrawLine(ref y, rect.x + 14f, rect.width - 28f, "github.com/KamilBourouiba/testgest");
        }

        void DrawLine(ref float y, float x, float width, string text)
        {
            GUI.Label(new Rect(x, y, width, 20f), text, _body);
            y += 20f;
        }

        void EnsureStyles()
        {
            if (_box != null)
                return;

            _box = new GUIStyle(GUI.skin.box)
            {
                normal = { background = MakeTex(new Color(0.04f, 0.06f, 0.10f, 0.88f)) },
            };
            _title = new GUIStyle(GUI.skin.label)
            {
                fontStyle = FontStyle.Bold,
                fontSize = 15,
                normal = { textColor = new Color(0.62f, 1f, 0.75f) },
            };
            _body = new GUIStyle(GUI.skin.label)
            {
                fontSize = 12,
                normal = { textColor = new Color(0.84f, 0.90f, 0.97f) },
            };
        }

        static Texture2D MakeTex(Color color)
        {
            var tex = new Texture2D(1, 1);
            tex.SetPixel(0, 0, color);
            tex.Apply();
            return tex;
        }
    }
}
