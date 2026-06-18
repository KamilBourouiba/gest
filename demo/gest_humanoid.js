/**
 * Three.js humanoid renderer for .gest clips (Xbot / Mixamo-style rig).
 * Body: static skinned mesh. Arms: procedural capsules driven by .gest wrists.
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const GEST_TO_THREE = new THREE.Vector3(1, 1, -1);
const _a = new THREE.Vector3();
const _b = new THREE.Vector3();
const _c = new THREE.Vector3();
const _d = new THREE.Vector3();
const _dir = new THREE.Vector3();
const _up = new THREE.Vector3(0, 1, 0);

const loader = new GLTFLoader();

function gestVecInto(x, y, z, out) {
  return out.set(x, y, z).multiply(GEST_TO_THREE);
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

function disposeObject3D(root) {
  root.traverse((obj) => {
    if (obj.geometry) obj.geometry.dispose();
    if (obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const mat of mats) mat?.dispose?.();
    }
  });
}

export function createHumanoidStage(canvas) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "low-power",
    stencil: false,
    depth: true,
  });
  renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio || 1));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = false;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a1018);
  scene.fog = new THREE.Fog(0x0a1018, 8, 18);

  const camera = new THREE.PerspectiveCamera(38, 1, 0.05, 40);
  camera.position.set(0.35, 1.42, 2.55);

  scene.add(new THREE.AmbientLight(0x6a7a9a, 0.55));
  scene.add(new THREE.HemisphereLight(0xd8e8ff, 0x243044, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 1.65);
  key.position.set(2.2, 4.5, 2.4);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0x9fd0ff, 0.75);
  fill.position.set(-2.8, 2.4, 1.6);
  scene.add(fill);

  const floorGeo = new THREE.CircleGeometry(1.1, 32);
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x1c2432, roughness: 0.88, metalness: 0.08 });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);

  const grid = new THREE.GridHelper(2.2, 16, 0x3a4d6a, 0x243044);
  grid.position.y = 0.001;
  scene.add(grid);

  const armCapGeo = new THREE.CapsuleGeometry(0.04, 0.18, 4, 8);
  const gazeCapGeo = new THREE.CapsuleGeometry(0.012, 0.2, 4, 6);
  const wristGeo = new THREE.SphereGeometry(0.045, 12, 12);

  let modelRoot = null;
  let loaded = false;
  let shoulderL = null;
  let shoulderR = null;
  let elbowL = null;
  let elbowR = null;
  let headBone = null;
  let arms = null;
  let wrists = null;
  let gazeLine = null;
  let disposed = false;

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

  function mkCapsule(geo, color) {
    const mesh = new THREE.Mesh(
      geo,
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

  function mkSphere(geo, color) {
    const mesh = new THREE.Mesh(
      geo,
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.4, depthTest: false }),
    );
    mesh.renderOrder = 3;
    return mesh;
  }

  async function loadModel(url) {
    const gltf = await loader.loadAsync(url);
    if (disposed) return;

    modelRoot = gltf.scene;
    modelRoot.traverse((obj) => {
      if (obj.isMesh) {
        if (obj.name === "Beta_Joints") {
          obj.visible = false;
          return;
        }
        obj.castShadow = false;
        obj.receiveShadow = false;
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
    headBone = findBone(modelRoot, "mixamorig:Head", "mixamorigHead");

    gltf.animations.length = 0;

    arms = {
      lUpper: mkCapsule(armCapGeo, 0x3aa0e0),
      lFore: mkCapsule(armCapGeo, 0x5ec8ff),
      rUpper: mkCapsule(armCapGeo, 0xe08040),
      rFore: mkCapsule(armCapGeo, 0xffa060),
    };
    wrists = {
      left: mkSphere(wristGeo, 0x64d8ff),
      right: mkSphere(wristGeo, 0xff9f64),
    };
    gazeLine = mkCapsule(
      gazeCapGeo,
      0x9fffc0,
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
    return out.setFromMatrixPosition(bone.matrixWorld);
  }

  function applyRig(rig) {
    if (!loaded || !modelRoot) return;

    modelRoot.updateMatrixWorld(true);

    gestVecInto(rig.lw[0], rig.lw[1], rig.lw[2], _c);
    gestVecInto(rig.rw[0], rig.rw[1], rig.rw[2], _d);
    gestVecInto(rig.gazeEnd[0], rig.gazeEnd[1], rig.gazeEnd[2], _dir);

    wrists.left.position.copy(_c);
    wrists.right.position.copy(_d);

    if (shoulderL && elbowL) {
      boneWorld(shoulderL, _a);
      boneWorld(elbowL, _b);
      placeCapsule(arms.lUpper, _a, _b);
      placeCapsule(arms.lFore, _b, _c);
    }
    if (shoulderR && elbowR) {
      boneWorld(shoulderR, _a);
      boneWorld(elbowR, _b);
      placeCapsule(arms.rUpper, _a, _b);
      placeCapsule(arms.rFore, _b, _d);
    }

    if (headBone) {
      boneWorld(headBone, _a);
      placeCapsule(gazeLine, _a, _dir);
    }
  }

  function render(nowMs, rig) {
    if (disposed) return;
    const t = nowMs * 0.00012;
    camera.position.set(0.35 + Math.sin(t) * 0.25, 1.38, 2.55 + Math.cos(t) * 0.18);
    camera.lookAt(0, 1.02, 0);

    if (rig) applyRig(rig);
    renderer.render(scene, camera);
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    loaded = false;

    if (modelRoot) {
      scene.remove(modelRoot);
      disposeObject3D(modelRoot);
      modelRoot = null;
    }

    for (const mesh of [arms?.lUpper, arms?.lFore, arms?.rUpper, arms?.rFore, wrists?.left, wrists?.right, gazeLine]) {
      if (!mesh) continue;
      scene.remove(mesh);
      mesh.material?.dispose?.();
    }

    floorGeo.dispose();
    floorMat.dispose();
    armCapGeo.dispose();
    gazeCapGeo.dispose();
    wristGeo.dispose();
    grid.geometry?.dispose?.();
    if (Array.isArray(grid.material)) grid.material.forEach((m) => m.dispose?.());
    else grid.material?.dispose?.();

    renderer.dispose();
    scene.clear();
  }

  resize();
  return { loadModel, render, resize, dispose, isLoaded: () => loaded };
}
