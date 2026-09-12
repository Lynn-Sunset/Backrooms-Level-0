import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const catalog = {
  pavilion: ['Garden pavilion', 'Carved timber braces, lotus column bases, patterned stone paving and scalloped clay tiles. Weathered bronze accents and a framed 听雨亭 plaque complete the open garden structure.'],
  almond_water: ['Almond water', 'Thick refractive glass, an inner wall and liquid meniscus, textured paper, a ribbed closure and a raised cap emblem. Built at handheld bottle scale.'],
  exit_door: ['Walnut exit door', 'Shaped ogee moldings and narrow brass inlay frame the walnut panels. Directional timber grain, patinated hardware and slotted fasteners reward a closer look.'],
  door_industrial: ['Industrial door', 'Textured powder coating, brushed kickplates, closer mechanisms and articulated arms. The wired glass opening, panic bars and louvers reveal how the door is assembled.'],
  light_panel: ['Fluorescent fixture', 'Folded reflectors, tube endcaps and contact pins sit inside an enamel tray with a ballast cover, service clips, sockets and wiring. Shown from below.'],
  pillar: ['Fluted column', 'A continuous carved shaft with recessed flutes and stepped molding. Fine limestone pores, mineral variation and relief maps add natural surface detail.'],
};
const $ = id => document.getElementById(id);
const stage = $('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.domElement.setAttribute('aria-label', 'Drag to rotate the selected 3D model');
stage.prepend(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color('#202720');
const room = new RoomEnvironment();
const pmrem = new THREE.PMREMGenerator(renderer);
const environment = pmrem.fromScene(room, .04);
scene.environment = environment.texture;
room.dispose();
pmrem.dispose();
scene.add(new THREE.HemisphereLight('#e7ecd9', '#323b30', 1.1));
const keyLight = new THREE.DirectionalLight('#fff3d8', 3);
keyLight.position.set(4, 6, 5);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
Object.assign(keyLight.shadow.camera, { left: -2, right: 2, top: 3, bottom: -2, near: .1, far: 20 });
keyLight.shadow.bias = -.0002;
keyLight.shadow.normalBias = .004;
keyLight.shadow.radius = 3;
keyLight.shadow.camera.updateProjectionMatrix();
scene.add(keyLight);
const fill = new THREE.DirectionalLight('#c1d3dc', 1.6);
fill.position.set(-4, 2, -3);
scene.add(fill);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ opacity: .23 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
ground.position.y = -.005;
scene.add(ground);
const camera = new THREE.PerspectiveCamera(36, 1, .01, 100);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = .075;
controls.autoRotateSpeed = .6;
controls.minDistance = .7;
controls.maxDistance = 12;
controls.maxPolarAngle = Math.PI * .94;
const loader = new GLTFLoader();
const cache = new Map();
const assetRoot = new THREE.Group();
scene.add(assetRoot);
let selected = '', token = 0, wired = false;
let resetPosition = new THREE.Vector3(), resetTarget = new THREE.Vector3();
let modelSize = null;

function fitView() {
  if (!modelSize) return;
  const size = modelSize;
  const direction = (selected === 'light_panel' ? new THREE.Vector3(.3, -.8, 1) : new THREE.Vector3(.34, .24, 1)).normalize();
  const right = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), direction).normalize();
  const up = new THREE.Vector3().crossVectors(direction, right);
  const tanV = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  const tanH = tanV * camera.aspect;
  let distance = 0;
  resetTarget.set(0, size.y * .49, 0);
  for (const x of [-size.x / 2, size.x / 2]) {
    for (const y of [0, size.y]) for (const z of [-size.z / 2, size.z / 2]) {
      const p = new THREE.Vector3(x, y, z).sub(resetTarget);
      distance = Math.max(distance, p.dot(direction) + 1.14 * Math.max(Math.abs(p.dot(right)) / tanH, Math.abs(p.dot(up)) / tanV));
    }
  }
  resetPosition.copy(resetTarget).addScaledVector(direction, distance);
  controls.maxDistance = Math.max(12, distance * 2);
  resetView();
}

function resetView() {
  camera.position.copy(resetPosition);
  controls.target.copy(resetTarget);
  controls.update();
}

async function selectModel(name) {
  if (!catalog[name]) return;
  const request = ++token;
  selected = name;
  stage.setAttribute('aria-busy', 'true');
  $('status').textContent = 'Loading model…';
  for (const button of document.querySelectorAll('[data-model]')) button.setAttribute('aria-pressed', String(button.dataset.model === name));
  try {
    if (!cache.has(name)) cache.set(name, loader.loadAsync(`models/${name}.glb`));
    const gltf = await cache.get(name);
    if (request !== token) return;
    assetRoot.clear();
    const object = gltf.scene;
    object.position.set(0, 0, 0);
    object.scale.setScalar(1);
    object.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(object);
    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    const scale = 2.5 / Math.max(size.x, size.y, size.z);
    object.scale.setScalar(scale);
    object.position.set(-center.x * scale, -bounds.min.y * scale, -center.z * scale);
    let triangles = 0;
    const materials = new Set();
    object.traverse(o => {
      if (!o.isMesh) return;
      o.castShadow = o.receiveShadow = true;
      triangles += (o.geometry.index?.count ?? o.geometry.attributes.position.count) / 3;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        materials.add(m.uuid);
        m.wireframe = wired;
        m.envMapIntensity = .8;
        if (m.transparent) { m.depthWrite = false; o.castShadow = false; }
        for (const slot of ['map', 'normalMap', 'roughnessMap']) {
          if (m[slot]) m[slot].anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        }
      }
    });
    assetRoot.add(object);
    modelSize = size.clone().multiplyScalar(scale);
    ground.visible = name !== 'light_panel';
    fitView();
    $('model-title').textContent = catalog[name][0];
    $('description').textContent = catalog[name][1];
    $('asset-code').textContent = name.replaceAll('_', ' ').toUpperCase();
    $('dimensions').textContent = [size.x, size.y, size.z].map(n => n.toFixed(2)).join(' × ');
    $('triangles').textContent = triangles.toLocaleString('en-US');
    $('materials').textContent = String(materials.size);
    $('download').href = `models/${name}.glb`;
    $('status').textContent = '';
    stage.setAttribute('aria-busy', 'false');
    stage.dataset.loaded = name;
    history.replaceState(null, '', `?model=${name}`);
    console.log(`[MODEL] READY ${name} triangles=${triangles} materials=${materials.size}`);
  } catch (error) {
    if (request !== token) return;
    cache.delete(name);
    $('status').textContent = 'Model could not load. Select it again to retry.';
    stage.setAttribute('aria-busy', 'false');
    console.error('Model load failed:', name, error);
  }
}

for (const button of document.querySelectorAll('[data-model]')) button.addEventListener('click', () => selectModel(button.dataset.model));
$('reset').addEventListener('click', resetView);
$('rotate').addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate;
  $('rotate').setAttribute('aria-pressed', String(controls.autoRotate));
});
$('wireframe').addEventListener('click', () => {
  wired = !wired;
  $('wireframe').setAttribute('aria-pressed', String(wired));
  assetRoot.traverse(o => { if (o.isMesh) for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.wireframe = wired; });
});
new ResizeObserver(() => {
  const { width, height } = stage.getBoundingClientRect();
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  fitView();
}).observe(stage);
const { width, height } = stage.getBoundingClientRect();
renderer.setSize(width, height, false);
camera.aspect = width / height;
camera.updateProjectionMatrix();
selectModel(new URLSearchParams(location.search).get('model') || 'pavilion');
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
