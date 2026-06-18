/**
 * Three.js humanoid renderer for .gest clips (Xbot / Mixamo-style rig).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { CCDIKSolver } from "three/addons/animation/CCDIKSolver.js";

const GEST_TO_THREE = new THREE.Vector3(1, 1, -1);

export function gestVec(x, y, z) {
  return new THREE.Vector3(x, y, z).multiply(GEST_TO_THREE);
}

export function createHumanoidStage(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x060910);
  scene.fog = new THREE.Fog(0x060910, 4, 12);

  const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 30);
  camera.position.set(0, 1.45, 2.4);

  scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x1a2030, 0.85));
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(2.2, 4.5, 1.8);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x64d8ff, 0.45);
  rim.position.set(-2.5, 2.0, -2.0);
  scene.add(rim);

  const floor = new THREE.Mesh(
    new THREE.CircleGeometry(0.85, 48),
    new THREE.MeshStandardMaterial({ color: 0x141a24, roughness: 0.92, metalness: 0.05 }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, 0.72, 0.35);
  floor.receiveShadow = true;
  scene.add(floor);

  const grid = new THREE.GridHelper(1.6, 16, 0x263149, 0x182238);
  grid.position.set(0, 0.721, 0.35);
  scene.add(grid);

  const targets = {
    left: new THREE.Object3D(),
    right: new THREE.Object3D(),
    gaze: new THREE.Object3D(),
  };
  scene.add(targets.left, targets.right, targets.gaze);

  let modelRoot = null;
  let skinned = null;
  let skeleton = null;
  let bonesByName = new Map();
  let ikSolver = null;
  let mixer = null;
  let idleAction = null;
  let loaded = false;

  function resize() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
  }

  function findBone(...names) {
    for (const n of names) {
      const b = bonesByName.get(n);
      if (b) return b;
    }
    return null;
  }

  function boneIndex(...names) {
    const b = findBone(...names);
    return b ? skeleton.bones.indexOf(b) : -1;
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

    modelRoot.scale.setScalar(0.0092);
    modelRoot.position.set(0, 0, 0);
    scene.add(modelRoot);

    const box = new THREE.Box3().setFromObject(modelRoot);
    const floorY = box.min.y;
    modelRoot.position.y -= floorY;
    floor.position.y = 0.001;
    grid.position.y = 0.002;

    modelRoot.traverse((o) => {
      if (o.isSkinnedMesh && !skinned) skinned = o;
    });
    if (!skinned) throw new Error("No skinned mesh in mannequin.glb");
    skeleton = skinned.skeleton;
    bonesByName = new Map(skeleton.bones.map((b) => [b.name, b]));

    if (gltf.animations?.length) {
      mixer = new THREE.AnimationMixer(modelRoot);
      const idleClip =
        gltf.animations.find((c) => /idle/i.test(c.name)) || gltf.animations[0];
      idleAction = mixer.clipAction(idleClip);
      idleAction.play();
      idleAction.setEffectiveWeight(0.35);
    }

    const ikLinks = [];
    const addChain = (handNames, foreNames, target) => {
      const hand = boneIndex(...handNames);
      const fore = boneIndex(...foreNames);
      if (hand < 0 || fore < 0) return;
      ikLinks.push({ index: hand, target });
      ikLinks.push({ index: fore, target });
    };
    addChain(
      ["mixamorig:LeftHand", "mixamorigLeftHand"],
      ["mixamorig:LeftForeArm", "mixamorigLeftForeArm"],
      targets.left,
    );
    addChain(
      ["mixamorig:RightHand", "mixamorigRightHand"],
      ["mixamorig:RightForeArm", "mixamorigRightForeArm"],
      targets.right,
    );

    ikSolver = new CCDIKSolver(skinned, ikLinks);
    loaded = true;
  }

  function applyRig(rig) {
    if (!loaded) return;

    targets.left.position.copy(gestVec(rig.lw[0], rig.lw[1], rig.lw[2]));
    targets.right.position.copy(gestVec(rig.rw[0], rig.rw[1], rig.rw[2]));
    targets.gaze.position.copy(gestVec(rig.gazeEnd[0], rig.gazeEnd[1], rig.gazeEnd[2]));

    const head = findBone("mixamorig:Head", "mixamorigHead");
    if (head) {
      head.lookAt(targets.gaze.position);
    }

    ikSolver?.update();
    skeleton?.update();
  }

  function render(nowMs, rig) {
    const t = nowMs * 0.00015;
    camera.position.set(Math.sin(t) * 2.15, 1.42, Math.cos(t) * 2.15 + 0.55);
    camera.lookAt(0, 1.05, 0.32);

    if (mixer) mixer.update(1 / 60);
    if (rig) applyRig(rig);
    renderer.render(scene, camera);
  }

  resize();
  return { loadModel, render, resize, isLoaded: () => loaded };
}
