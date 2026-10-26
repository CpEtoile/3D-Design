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
let bboxHelper;
let initialPositions;
let selectedVertex;
let addVertexMode = false;
let connectPendingVertices = [];
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

function updateDimensions() {
    if (!mesh) return;
    if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
    const box = mesh.geometry.boundingBox.clone();
    const size = new THREE.Vector3();
    box.getSize(size);
    const scale = Math.max(inputValue('#scale'), 0.001);
    const unitScale = Number(document.querySelector('#unit-scale')?.value) || 0.1;

    const cmX = size.x * scale * unitScale;
    const cmY = size.y * scale * unitScale;
    const cmZ = size.z * scale * unitScale;

    const elX = document.querySelector('#dim-x');
    const elY = document.querySelector('#dim-y');
    const elZ = document.querySelector('#dim-z');
    if (elX) elX.textContent = cmX.toFixed(2);
    if (elY) elY.textContent = cmY.toFixed(2);
    if (elZ) elZ.textContent = cmZ.toFixed(2);

    const hud = document.querySelector('#viewport-hud');
    if (hud) {
        hud.textContent = `Size: ${cmX.toFixed(2)} × ${cmY.toFixed(2)} × ${cmZ.toFixed(2)} cm (W × D × H)`;
    }
    if (bboxHelper) bboxHelper.update();
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
    updateDimensions();
}

function clearVertexSelection() {
    selectedVertex = null;
    vertexHandle.visible = false;
    vertexGizmo.detach();
    connectPendingVertices = [];
    document.querySelector('#vertex-status').textContent = 'Select vertex: click a vertex on model.';
}

function selectVertexAtPosition(selectedPosition) {
    const positions = mesh.geometry.getAttribute('position');
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

function addVertex(point, faceIndex) {
    const positions = mesh.geometry.getAttribute('position');
    const oldArray = positions.array;
    const offset = faceIndex * 9;
    const newArray = new Float32Array(oldArray.length + 18);
    newArray.set(oldArray.subarray(0, offset), 0);
    const a = [oldArray[offset], oldArray[offset + 1], oldArray[offset + 2]];
    const b = [oldArray[offset + 3], oldArray[offset + 4], oldArray[offset + 5]];
    const c = [oldArray[offset + 6], oldArray[offset + 7], oldArray[offset + 8]];
    const p = [point.x, point.y, point.z];
    const splitTriangles = [
        ...a, ...b, ...p,
        ...b, ...c, ...p,
        ...c, ...a, ...p
    ];
    newArray.set(splitTriangles, offset);
    newArray.set(oldArray.subarray(offset + 9), offset + 27);
    mesh.geometry.setAttribute('position', new THREE.BufferAttribute(newArray, 3));
    mesh.geometry.computeVertexNormals();
    if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
    if (mesh.geometry.computeBoundingSphere) mesh.geometry.computeBoundingSphere();
    status.textContent = `${mesh.geometry.getAttribute('position').count / 3} triangles`;
    return point;
}

function connectVertices(newVertex, vertex1, vertex2) {
    const positions = mesh.geometry.getAttribute('position');
    const oldArray = positions.array;
    const newArray = new Float32Array(oldArray.length + 9);
    newArray.set(oldArray, 0);
    newArray.set([
        newVertex.x, newVertex.y, newVertex.z,
        vertex1.x, vertex1.y, vertex1.z,
        vertex2.x, vertex2.y, vertex2.z
    ], oldArray.length);
    mesh.geometry.setAttribute('position', new THREE.BufferAttribute(newArray, 3));
    mesh.geometry.computeVertexNormals();
    if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
    if (mesh.geometry.computeBoundingSphere) mesh.geometry.computeBoundingSphere();
    status.textContent = `${mesh.geometry.getAttribute('position').count / 3} triangles`;
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
    const nearestPosition = new THREE.Vector3().fromBufferAttribute(positions, nearestIndex);

    if (addVertexMode) {
        if (event.shiftKey && selectedVertex) {
            connectPendingVertices.push(nearestPosition);
            if (connectPendingVertices.length === 2) {
                connectVertices(selectedVertex.position, connectPendingVertices[0], connectPendingVertices[1]);
                connectPendingVertices = [];
                document.querySelector('#vertex-status').textContent = 'Connected new triangle to chosen vertices.';
            } else {
                document.querySelector('#vertex-status').textContent = 'Selected 1 vertex to connect. Shift-click 1 more vertex.';
            }
        } else {
            addVertex(localPoint, hit.faceIndex);
            selectVertexAtPosition(localPoint);
            document.querySelector('#vertex-status').textContent = 'Added vertex: split triangle into 3 triangles. Drag axis gizmo or Shift-click to connect.';
        }
        return;
    }

    selectVertexAtPosition(nearestPosition);
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
    if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
    if (mesh.geometry.computeBoundingSphere) mesh.geometry.computeBoundingSphere();
    updateDimensions();
}

function resetVertices() {
    if (!mesh || !initialPositions) return;
    mesh.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(initialPositions), 3));
    mesh.geometry.computeVertexNormals();
    if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
    if (mesh.geometry.computeBoundingSphere) mesh.geometry.computeBoundingSphere();
    clearVertexSelection();
    connectPendingVertices = [];
    status.textContent = `${mesh.geometry.getAttribute('position').count / 3} triangles`;
    updateDimensions();
}

function reset() {
    document.querySelectorAll('input').forEach((input) => {
        input.value = input.id === 'scale' ? '1' : '0';
    });
    applyTransform();
    resetVertices();
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
mesh.frustumCulled = false;
scene.add(mesh);

bboxHelper = new THREE.BoxHelper(mesh, 0x38bdf8);
scene.add(bboxHelper);
document.querySelector('#viewport-message').hidden = true;
mesh.geometry.computeVertexNormals();
if (mesh.geometry.computeBoundingBox) mesh.geometry.computeBoundingBox();
if (mesh.geometry.computeBoundingSphere) mesh.geometry.computeBoundingSphere();
initialPositions = new Float32Array(mesh.geometry.getAttribute('position').array);
renderer.domElement.addEventListener('pointerdown', selectVertex);
vertexGizmo.addEventListener('dragging-changed', (event) => {
    controls.enabled = !event.value;
});
vertexGizmo.addEventListener('objectChange', updateSelectedVertex);
document.querySelectorAll('input').forEach((input) => input.addEventListener('input', applyTransform));
const unitScaleSelect = document.querySelector('#unit-scale');
if (unitScaleSelect) unitScaleSelect.addEventListener('change', updateDimensions);
document.querySelector('#reset').addEventListener('click', reset);
document.querySelector('#reset-vertices').addEventListener('click', resetVertices);
const addVertexButton = document.querySelector('#add-vertex');
if (addVertexButton) {
    addVertexButton.addEventListener('click', () => {
        addVertexMode = !addVertexMode;
        connectPendingVertices = [];
        addVertexButton.textContent = addVertexMode ? 'Exit add vertex' : 'Add vertex';
        document.querySelector('#vertex-status').textContent = addVertexMode
            ? 'Add vertex active: click triangle to split, or Shift-click to connect chosen vertices.'
            : 'Select vertex: click a vertex on model.';
    });
}
document.querySelector('#save').addEventListener('click', downloadEditedStl);
const showControl = document.querySelector('#show-control');
showControl.addEventListener('click', () => {
    const panel = document.querySelector('#controls-legend');
    panel.hidden = !panel.hidden;
    showControl.textContent = panel.hidden ? 'Show controls' : 'Hide controls';
});
status.textContent = `${mesh.geometry.getAttribute('position').count / 3} triangles`;
window.addEventListener('resize', resize);
resize();
fitCamera();
updateDimensions();
renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
});
