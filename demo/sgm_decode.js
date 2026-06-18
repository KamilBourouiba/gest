/**
 * SGM v1 decoder for browser — aligned with include/sgm_v1.h and src/gest/sgm_decode.py
 */
(function (global) {
  const SGM_MAGIC = [0x53, 0x47, 0x4d, 0x01];
  const SGM_OP_FRAME = 0x30;
  const SGM_OP_JOINTS_F32 = 0x31;
  const SGM_OP_STATE = 0x32;
  const SGM_OP_DIR_F32 = 0x33;
  const SGM_OP_END = 0xff;
  const SGM_KIND_ARTICULATED = 1;
  const SGM_KIND_DIRECTION = 2;

  function decodeSgmBytes(buffer) {
    const bytes = buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer;
    const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    let pos = 0;
    const need = (n) => {
      if (pos + n > bytes.length) throw new Error(`SGM EOF at ${pos}`);
    };

    need(4);
    for (let i = 0; i < 4; i++) {
      if (bytes[pos + i] !== SGM_MAGIC[i]) throw new Error("Bad SGM magic");
    }
    pos += 4;

    need(8);
    const formatVersion = dv.getUint16(pos, true); pos += 2;
    if (formatVersion !== 1) throw new Error(`Unsupported format_version ${formatVersion}`);
    const fps = dv.getFloat32(pos, true); pos += 4;
    const nCh = dv.getUint16(pos, true); pos += 2;

    const channels = [];
    for (let c = 0; c < nCh; c++) {
      need(2);
      const kind = dv.getUint8(pos);
      const nlen = dv.getUint8(pos + 1);
      pos += 2;
      need(nlen);
      const name = new TextDecoder().decode(bytes.subarray(pos, pos + nlen));
      pos += nlen;
      if (kind === SGM_KIND_ARTICULATED) {
        need(4);
        channels.push({
          name,
          kind: "articulated",
          jointCount: dv.getUint16(pos, true),
          stateCount: dv.getUint16(pos + 2, true),
        });
        pos += 4;
      } else if (kind === SGM_KIND_DIRECTION) {
        channels.push({ name, kind: "direction" });
      } else {
        throw new Error(`Unknown channel kind ${kind}`);
      }
    }

    const ops = [];
    while (pos < bytes.length) {
      need(1);
      const op = dv.getUint8(pos); pos += 1;
      if (op === SGM_OP_END) {
        if (pos !== bytes.length) throw new Error("Trailing data after OP_END");
        break;
      }
      if (op === SGM_OP_FRAME) {
        need(8);
        ops.push({ kind: "frame", t: dv.getFloat64(pos, true) });
        pos += 8;
      } else if (op === SGM_OP_JOINTS_F32) {
        need(6);
        const channelId = dv.getUint16(pos, true);
        const nFloats = dv.getUint32(pos + 2, true);
        pos += 6;
        need(nFloats * 4);
        const values = [];
        for (let i = 0; i < nFloats; i++) {
          values.push(dv.getFloat32(pos, true));
          pos += 4;
        }
        ops.push({ kind: "joints_f32", channelId, values });
      } else if (op === SGM_OP_STATE) {
        need(4);
        ops.push({
          kind: "state_index",
          channelId: dv.getUint16(pos, true),
          stateIndex: dv.getUint16(pos + 2, true),
        });
        pos += 4;
      } else if (op === SGM_OP_DIR_F32) {
        need(14);
        const channelId = dv.getUint16(pos, true); pos += 2;
        ops.push({
          kind: "direction_f32",
          channelId,
          values: [dv.getFloat32(pos, true), dv.getFloat32(pos + 4, true), dv.getFloat32(pos + 8, true)],
        });
        pos += 12;
      } else {
        throw new Error(`Unknown opcode 0x${op.toString(16)} at ${pos - 1}`);
      }
    }

    return { formatVersion, fps, channels, ops, bytes };
  }

  function decodedToTimeline(decoded) {
    const idToName = Object.fromEntries(decoded.channels.map((ch, i) => [i, ch.name]));
    const timeline = [];
    let currentT = null;
    let currentPose = {};

    const flush = () => {
      if (currentT !== null) timeline.push({ t: currentT, pose: { ...currentPose } });
      currentPose = {};
    };

    for (const op of decoded.ops) {
      if (op.kind === "frame") {
        flush();
        currentT = op.t ?? 0;
      } else if (op.channelId === undefined) {
        continue;
      } else {
        const name = idToName[op.channelId];
        if (!name) throw new Error(`Unknown channel_id ${op.channelId}`);
        if (op.kind === "joints_f32") {
          const entry = currentPose[name] ?? (currentPose[name] = {});
          entry.joints = { format: "raw_float32", values: op.values.slice() };
        } else if (op.kind === "state_index") {
          const entry = currentPose[name] ?? (currentPose[name] = {});
          entry.state_index = op.stateIndex;
        } else if (op.kind === "direction_f32") {
          currentPose[name] = { dir: op.values.slice() };
        }
      }
    }
    flush();
    return timeline;
  }

  function formatBytecodeHex(bytes, pulseIndex = 0) {
    const parts = [];
    for (let i = 0; i < bytes.length; i++) {
      const hex = bytes[i].toString(16).padStart(2, "0");
      parts.push(i === pulseIndex ? `<mark>${hex}</mark>` : hex);
      if ((i + 1) % 16 === 0) parts.push("<br>");
      else if ((i + 1) % 4 === 0) parts.push(" ");
    }
    return parts.join("");
  }

  global.GestSgm = { decodeSgmBytes, decodedToTimeline, formatBytecodeHex };
})(typeof window !== "undefined" ? window : globalThis);
