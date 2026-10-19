import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
import {TransformControls} from 'three/addons/controls/TransformControls.js';

const viewport = document.querySelector('#viewport');
const status = document.querySelector('#status');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111827);
const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 100000);
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
viewport.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2);
keyLight.position.set(1, 2, 3);
scene.add(keyLight);
scene.add(new THREE.GridHelper(10, 10, 0x475569, 0x334155));

let mesh;
let selectedVertex;
const vertexRaycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const vertexHandle = new THREE.Mesh(
    new THREE.SphereGeometry(1, 12, 8),
    new THREE.MeshBasicMaterial({color: 0xfbbf24})
);
vertexHandle.name = 'vertex-gizmo';
vertexHandle.visible = false;
scene.add(vertexHandle);
const vertexGizmo = new TransformControls(camera, renderer.domElement);
vertexGizmo.setMode('translate');
scene.add(vertexGizmo);

function resize() {
    const width = viewport.clientWidth;
    const height = viewport.clientHeight;
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
}

function fitCamera() {
    if (!mesh) return;
    const box = new THREE.Box3().setFromObject(mesh);
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    const distance = sphere.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2));
    camera.position.set(sphere.center.x + distance, sphere.center.y + distance * 0.6, sphere.center.z + distance);
    camera.near = Math.max(distance / 1000, 0.001);
    camera.far = Math.max(distance * 100, 1000);
    camera.updateProjectionMatrix();
    controls.target.copy(sphere.center);
    controls.update();
}

function inputValue(selector) {
    return Number(document.querySelector(selector).value) || 0;
}

function applyTransform() {
    if (!mesh) return;
    mesh.position.set(inputValue('#position-x'), inputValue('#position-y'), inputValue('#position-z'));
    mesh.rotation.set(
        THREE.MathUtils.degToRad(inputValue('#rotation-x')),
        THREE.MathUtils.degToRad(inputValue('#rotation-y')),
        THREE.MathUtils.degToRad(inputValue('#rotation-z'))
    );
    mesh.scale.setScalar(Math.max(inputValue('#scale'), 0.001));
}

function clearVertexSelection() {
    selectedVertex = null;
    vertexHandle.visible = false;
    vertexGizmo.detach();
    document.querySelector('#vertex-status').textContent = 'Select vertex: click a vertex on model.';
}

function selectVertex(event) {
    if (vertexGizmo.dragging || !mesh) return;
    const bounds = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    vertexRaycaster.setFromCamera(pointer, camera);
    const hit = vertexRaycaster.intersectObject(mesh, false)[0];
    if (!hit || hit.faceIndex === undefined) return;
    const positions = mesh.geometry.getAttribute('position');
    const localPoint = mesh.worldToLocal(hit.point.clone());
    const triangleStart = hit.faceIndex * 3;
    let nearestIndex = triangleStart;
    let nearestDistance = Infinity;
    for (let index = triangleStart; index < triangleStart + 3; index += 1) {
        const candidate = new THREE.Vector3().fromBufferAttribute(positions, index);
        const distance = candidate.distanceToSquared(localPoint);
        if (distance < nearestDistance) {
            nearestDistance = distance;
            nearestIndex = index;
        }
    }
    const selectedPosition = new THREE.Vector3().fromBufferAttribute(positions, nearestIndex);
    const radius = mesh.geometry.boundingSphere?.radius || 1;
    const epsilon = Math.max(radius * 0.00001, 0.000001);
    const indices = [];
    for (let index = 0; index < positions.count; index += 1) {
        const candidate = new THREE.Vector3().fromBufferAttribute(positions, index);
        if (candidate.distanceTo(selectedPosition) <= epsilon) indices.push(index);
    }
    selectedVertex = {indices, position: selectedPosition.clone()};
    vertexHandle.position.copy(mesh.localToWorld(selectedPosition.clone()));
    vertexHandle.scale.setScalar(Math.max(radius * 0.025, 0.1));
    vertexHandle.visible = true;
    vertexGizmo.attach(vertexHandle);
    document.querySelector('#vertex-status').textContent = `Selected vertex: ${indices.length} connected triangles. Drag axis gizmo.`;
}

function updateSelectedVertex() {
    if (!selectedVertex) return;
    const positions = mesh.geometry.getAttribute('position');
    const nextPosition = mesh.worldToLocal(vertexHandle.position.clone());
    const delta = nextPosition.clone().sub(selectedVertex.position);
    if (delta.lengthSq() === 0) return;
    selectedVertex.indices.forEach((index) => {
        const current = new THREE.Vector3().fromBufferAttribute(positions, index).add(delta);
        positions.setXYZ(index, current.x, current.y, current.z);
    });
    selectedVertex.position.copy(nextPosition);
    positions.needsUpdate = true;
    mesh.geometry.computeVertexNormals();
}

function reset() {
    document.querySelectorAll('input').forEach((input) => {
        input.value = input.id === 'scale' ? '1' : '0';
    });
    applyTransform();
    clearVertexSelection();
    fitCamera();
}

function downloadEditedStl() {
    mesh.updateMatrixWorld(true);
    const positions = mesh.geometry.getAttribute('position');
    const triangleCount = Math.floor(positions.count / 3);
    const buffer = new ArrayBuffer(84 + triangleCount * 50);
    const view = new DataView(buffer);
    new Uint8Array(buffer, 0, 24).set(new TextEncoder().encode('Edited by STL HTML Viewer'));
    view.setUint32(80, triangleCount, true);
    const first = new THREE.Vector3();
    const second = new THREE.Vector3();
    const third = new THREE.Vector3();
    const normal = new THREE.Vector3();
    for (let triangle = 0; triangle < triangleCount; triangle += 1) {
        const offset = 84 + triangle * 50;
        first.fromBufferAttribute(positions, triangle * 3).applyMatrix4(mesh.matrixWorld);
        second.fromBufferAttribute(positions, triangle * 3 + 1).applyMatrix4(mesh.matrixWorld);
        third.fromBufferAttribute(positions, triangle * 3 + 2).applyMatrix4(mesh.matrixWorld);
        normal.subVectors(second, first).cross(new THREE.Vector3().subVectors(third, first)).normalize();
        [normal, first, second, third].forEach((vector, index) => {
            view.setFloat32(offset + index * 12, vector.x, true);
            view.setFloat32(offset + 4 + index * 12, vector.y, true);
            view.setFloat32(offset + 8 + index * 12, vector.z, true);
        });
    }
    const filename = window.STL_SOURCE_NAME.replace(/\.stl$/i, '') + '-edited.stl';
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([buffer], {type: 'model/stl'}));
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

mesh = new THREE.Mesh(new STLLoader().parse(Uint8Array.from(atob(window.STL_MODEL_DATA.split(',')[1]), (character) => character.charCodeAt(0)).buffer), new THREE.MeshStandardMaterial({
    color: 0x60a5fa,
    roughness: 0.65,
    metalness: 0.05
}));
scene.add(mesh);
document.querySelector('#viewport-message').hidden = true;
mesh.geometry.computeVertexNormals();
renderer.domElement.addEventListener('pointerdown', selectVertex);
vertexGizmo.addEventListener('dragging-changed', (event) => {
    controls.enabled = !event.value;
});
vertexGizmo.addEventListener('objectChange', updateSelectedVertex);
document.querySelectorAll('input').forEach((input) => input.addEventListener('input', applyTransform));
document.querySelector('#reset').addEventListener('click', reset);
document.querySelector('#reset-vertices').addEventListener('click', clearVertexSelection);
document.querySelector('#save').addEventListener('click', downloadEditedStl);
document.querySelector('#help').addEventListener('click', () => {
    const panel = document.querySelector('#controls-legend');
    panel.hidden = false;
    panel.scrollIntoView({behavior: 'smooth', block: 'start'});
});
status.textContent = `${mesh.geometry.getAttribute('position').count / 3} triangles`;
window.addEventListener('resize', resize);
resize();
fitCamera();
renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
});
