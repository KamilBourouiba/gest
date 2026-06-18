/**
 * Xbot skinned mesh driven by .gest wrist/gaze channels (CCD IK on real bones).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const GEST_TO_THREE = new THREE.Vector3(1, 1, -1);
const _p0 = new THREE.Vector3();
const _p1 = new THREE.Vector3();
const _invQ = new THREE.Quaternion();
const _scale = new THREE.Vector3();
const _eff = new THREE.Vector3();
const _tgt = new THREE.Vector3();
const _axis = new THREE.Vector3();
const _dq = new THREE.Quaternion();
const _lw = new THREE.Vector3();
const _rw = new THREE.Vector3();
const _gaze = new THREE.Vector3();

const loader = new GLTFLoader();

function gestVecInto(x, y, z, out) {
  return out.set(x, y, z).multiply(GEST_TO_THREE);
}

function ccdArmIk(effector, links, targetWorld, iterations = 10) {
  for (let iter = 0; iter < iterations; iter++) {
    let rotated = false;
    for (let j = 0; j < links.length; j++) {
      const link = links[j];
      link.updateWorldMatrix(true, false);
      effector.updateWorldMatrix(true, false);
      link.matrixWorld.decompose(_p0, _invQ, _scale);
      _invQ.invert();
      _p1.setFromMatrixPosition(effector.matrixWorld);
      _eff.subVectors(_p1, _p0).applyQuaternion(_invQ).normalize();
      _tgt.subVectors(targetWorld, _p0).applyQuaternion(_invQ).normalize();
      let dot = Math.max(-1, Math.min(1, _eff.dot(_tgt)));
      const angle = Math.acos(dot);
      if (angle < 1e-5) continue;
      _axis.crossVectors(_eff, _tgt);
      if (_axis.lengthSq() < 1e-8) continue;
      _axis.normalize();
      _dq.setFromAxisAngle(_axis, angle);
      link.quaternion.multiply(_dq);
      rotated = true;
    }
    if (!rotated) break;
  }
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
  });
  renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio || 1));
  renderer.outputColorSpace = THREE.SRGBColorSpace;

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

  let modelRoot = null;
  let skinned = null;
  let skeleton = null;
  let loaded = false;
  let disposed = false;
  let bindPose = null;
  let leftHand = null;
  let rightHand = null;
  let leftFore = null;
  let rightFore = null;
  let leftArm = null;
  let rightArm = null;
  let headBone = null;

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
        if (obj.isSkinnedMesh) {
          obj.frustumCulled = false;
          if (!skinned) skinned = obj;
        }
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        for (const mat of mats) {
          if (mat) mat.side = THREE.DoubleSide;
        }
      }
    });
    if (!skinned) throw new Error("No skinned mesh in mannequin.glb");
    skeleton = skinned.skeleton;

    modelRoot.scale.setScalar(1);
    scene.add(modelRoot);

    const box = new THREE.Box3().setFromObject(modelRoot);
    modelRoot.position.y -= box.min.y;

    leftHand = findBone(modelRoot, "mixamorig:LeftHand", "mixamorigLeftHand");
    rightHand = findBone(modelRoot, "mixamorig:RightHand", "mixamorigRightHand");
    leftFore = findBone(modelRoot, "mixamorig:LeftForeArm", "mixamorigLeftForeArm");
    rightFore = findBone(modelRoot, "mixamorig:RightForeArm", "mixamorigRightForeArm");
    leftArm = findBone(modelRoot, "mixamorig:LeftArm", "mixamorigLeftArm");
    rightArm = findBone(modelRoot, "mixamorig:RightArm", "mixamorigRightArm");
    headBone = findBone(modelRoot, "mixamorig:Head", "mixamorigHead");

    bindPose = new Map();
    for (const bone of [leftFore, leftArm, rightFore, rightArm, headBone]) {
      if (bone) bindPose.set(bone, bone.quaternion.clone());
    }

    gltf.animations.length = 0;
    loaded = true;
  }

  function applyRig(rig) {
    if (!loaded || !skeleton) return;

    for (const [bone, quat] of bindPose) bone.quaternion.copy(quat);

    gestVecInto(rig.lw[0], rig.lw[1], rig.lw[2], _lw);
    gestVecInto(rig.rw[0], rig.rw[1], rig.rw[2], _rw);
    gestVecInto(rig.gazeEnd[0], rig.gazeEnd[1], rig.gazeEnd[2], _gaze);

    if (leftHand && leftFore && leftArm) ccdArmIk(leftHand, [leftFore, leftArm], _lw, 10);
    if (rightHand && rightFore && rightArm) ccdArmIk(rightHand, [rightFore, rightArm], _rw, 10);
    if (headBone) headBone.lookAt(_gaze);

    modelRoot.updateMatrixWorld(true);
    skeleton.update();
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
    floorGeo.dispose();
    floorMat.dispose();
    grid.geometry?.dispose?.();
    if (Array.isArray(grid.material)) grid.material.forEach((m) => m.dispose?.());
    else grid.material?.dispose?.();
    renderer.dispose();
    scene.clear();
  }

  resize();
  return { loadModel, render, resize, dispose, isLoaded: () => loaded };
}
