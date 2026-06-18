/**
 * Three.js humanoid renderer for .gest clips (Xbot / Mixamo-style rig).
 * Body: static skinned mesh. Arms: procedural capsules driven by .gest wrists.
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const GEST_TO_THREE = new THREE.Vector3(1, 1, -1);
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();
const _dir = new THREE.Vector3();
const _up = new THREE.Vector3(0, 1, 0);

export function gestVec(x, y, z) {
  return new THREE.Vector3(x, y, z).multiply(GEST_TO_THREE);
}

function placeCapsule(mesh, from, to) {
  _dir.subVectors(to, from);
  const len = _dir.length();
  if (len < 0.02) {
    mesh.visible = false;
    return;
  }
  mesh.visible = true;
  mesh.position.copy(from).addScaledVector(_dir, 0.5);
  mesh.scale.set(1, len, 1);
  mesh.quaternion.setFromUnitVectors(_up, _dir.normalize());
}

export function createHumanoidStage(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a1018);
  scene.fog = new THREE.Fog(0x0a1018, 8, 18);

  const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 40);
  camera.position.set(0.35, 1.42, 2.55);

  scene.add(new THREE.AmbientLight(0x6a7a9a, 0.55));
  scene.add(new THREE.HemisphereLight(0xd8e8ff, 0x243044, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 1.65);
  key.position.set(2.2, 4.5, 2.4);
  key.castShadow = true;
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9fd0ff, 0.75);
  fill.position.set(-2.8, 2.4, 1.6);
  scene.add(fill);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(1.1, 48),
    new THREE.MeshStandardMaterial({ color: 0x1c2432, roughness: 0.88, metalness: 0.08 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  scene.add(floor);

  const grid = new THREE.GridHelper(2.2, 22, 0x3a4d6a, 0x243044);
  grid.position.y = 0.001;
  scene.add(grid);

  let modelRoot = null;
  let mixer = null;
  let idleAction = null;
  let loaded = false;
  let shoulderL = null;
  let shoulderR = null;
  let elbowL = null;
  let elbowR = null;
  let arms = null;
  let wrists = null;
  let gazeLine = null;

  function resize() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
  }

  function findBone(root, ...names) {
    let found = null;
    root.traverse((o) => {
      if (found || !o.isBone) return;
      if (names.includes(o.name)) found = o;
    });
    return found;
  }

  function mkCapsule(color) {
    const mesh = new THREE.Mesh(
      new THREE.CapsuleGeometry(0.04, 0.18, 6, 12),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.28,
        roughness: 0.45,
        metalness: 0.05,
        depthTest: false,
      }),
    );
    mesh.renderOrder = 2;
    return mesh;
  }

  function mkSphere(color) {
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.045, 16, 16),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.4, depthTest: false }),
    );
    mesh.renderOrder = 3;
    return mesh;
  }

  async function loadModel(url) {
    const gltf = await new GLTFLoader().loadAsync(url);
    modelRoot = gltf.scene;
    modelRoot.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
      }
    });

    modelRoot.scale.setScalar(1);
    scene.add(modelRoot);

    const box = new THREE.Box3().setFromObject(modelRoot);
    modelRoot.position.y -= box.min.y;

    shoulderL = findBone(modelRoot, "mixamorig:LeftArm", "mixamorigLeftArm");
    shoulderR = findBone(modelRoot, "mixamorig:RightArm", "mixamorigRightArm");
    elbowL = findBone(modelRoot, "mixamorig:LeftForeArm", "mixamorigLeftForeArm");
    elbowR = findBone(modelRoot, "mixamorig:RightForeArm", "mixamorigRightForeArm");

    if (gltf.animations?.length) {
      mixer = new THREE.AnimationMixer(modelRoot);
      const idleClip = gltf.animations.find((c) => /idle/i.test(c.name)) || gltf.animations[0];
      idleAction = mixer.clipAction(idleClip);
      idleAction.play();
      idleAction.setEffectiveWeight(0.22);
    }

    arms = {
      lUpper: mkCapsule(0x3aa0e0),
      lFore: mkCapsule(0x5ec8ff),
      rUpper: mkCapsule(0xe08040),
      rFore: mkCapsule(0xffa060),
    };
    wrists = { left: mkSphere(0x64d8ff), right: mkSphere(0xff9f64) };
    gazeLine = new THREE.Mesh(
      new THREE.CapsuleGeometry(0.012, 0.2, 4, 8),
      new THREE.MeshStandardMaterial({ color: 0x9fffc0, emissive: 0x4dffb0, emissiveIntensity: 0.35 }),
    );

    scene.add(
      arms.lUpper,
      arms.lFore,
      arms.rUpper,
      arms.rFore,
      wrists.left,
      wrists.right,
      gazeLine,
    );

    loaded = true;
  }

  function boneWorld(bone, out) {
    bone.updateWorldMatrix(true, false);
    return out.setFromMatrixPosition(bone.matrixWorld);
  }

  function midPoint(a, b, out) {
    return out.copy(a).add(b).multiplyScalar(0.5);
  }

  function applyRig(rig) {
    if (!loaded) return;

    const leftWrist = gestVec(rig.lw[0], rig.lw[1], rig.lw[2]);
    const rightWrist = gestVec(rig.rw[0], rig.rw[1], rig.rw[2]);
    const gazeEnd = gestVec(rig.gazeEnd[0], rig.gazeEnd[1], rig.gazeEnd[2]);

    wrists.left.position.copy(leftWrist);
    wrists.right.position.copy(rightWrist);

    if (shoulderL && elbowL) {
      const s = boneWorld(shoulderL, _a);
      const e = boneWorld(elbowL, _b);
      placeCapsule(arms.lUpper, s, e);
      placeCapsule(arms.lFore, e, leftWrist);
    }
    if (shoulderR && elbowR) {
      const s = boneWorld(shoulderR, _a);
      const e = boneWorld(elbowR, _b);
      placeCapsule(arms.rUpper, s, e);
      placeCapsule(arms.rFore, e, rightWrist);
    }

    const head = findBone(modelRoot, "mixamorig:Head", "mixamorigHead");
    if (head) {
      const headPos = boneWorld(head, _a);
      placeCapsule(gazeLine, headPos, gazeEnd);
    }
  }

  function render(nowMs, rig) {
    const t = nowMs * 0.00012;
    camera.position.set(0.35 + Math.sin(t) * 0.25, 1.38, 2.55 + Math.cos(t) * 0.18);
    camera.lookAt(0, 1.02, 0);

    if (mixer) mixer.update(1 / 60);
    if (rig) applyRig(rig);
    renderer.render(scene, camera);
  }

  resize();
  return { loadModel, render, resize, isLoaded: () => loaded };
}
