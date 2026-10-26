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
let rulersGroup = new THREE.Group();
scene.add(rulersGroup);

let measureGroup = new THREE.Group();
scene.add(measureGroup);
let measureMode = false;
let measurePoints = [];
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

function createTextSprite(text, color = '#38bdf8') {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.font = 'bold 28px monospace';
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 128, 32);
    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({map: texture, depthTest: false});
    const sprite = new THREE.Sprite(spriteMat);
    sprite.renderOrder = 999;
    return sprite;
}

function updateRulers() {
    while (rulersGroup.children.length > 0) {
        const obj = rulersGroup.children[0];
        rulersGroup.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
            if (obj.material.map) obj.material.map.dispose();
            obj.material.dispose();
        }
    }

    const showRulers = document.querySelector('#toggle-rulers')?.checked ?? true;
    if (!showRulers || !mesh) return;

    mesh.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(mesh);
    if (box.isEmpty()) return;

    const unitScale = Number(document.querySelector('#unit-scale')?.value) || 0.1;
    const min = box.min;
    const max = box.max;
    const size = new THREE.Vector3();
    box.getSize(size);

    const stepWorld = 1 / unitScale;
    const tickLen = Math.max(Math.min(size.x, size.y, size.z) * 0.04, 0.5);
    const spriteScale = Math.max(Math.max(size.x, size.y, size.z) * 0.25, 2.0);

    const linePositions = [];

    // X ruler along (min.y, min.z)
    linePositions.push(min.x, min.y, min.z, max.x, min.y, min.z);
    for (let x = min.x; x <= max.x + 0.001; x += stepWorld) {
        linePositions.push(x, min.y, min.z, x, min.y - tickLen, min.z);
    }
    const spriteX = createTextSprite(`${(size.x * unitScale).toFixed(1)} cm`, '#38bdf8');
    spriteX.position.set((min.x + max.x) / 2, min.y - tickLen * 2.5, min.z);
    spriteX.scale.set(spriteScale, spriteScale * 0.25, 1);
    rulersGroup.add(spriteX);

    // Y ruler along (min.x, min.z)
    linePositions.push(min.x, min.y, min.z, min.x, max.y, min.z);
    for (let y = min.y; y <= max.y + 0.001; y += stepWorld) {
        linePositions.push(min.x, y, min.z, min.x - tickLen, y, min.z);
    }
    const spriteY = createTextSprite(`${(size.y * unitScale).toFixed(1)} cm`, '#38bdf8');
    spriteY.position.set(min.x - tickLen * 2.5, (min.y + max.y) / 2, min.z);
    spriteY.scale.set(spriteScale, spriteScale * 0.25, 1);
    rulersGroup.add(spriteY);

    // Z ruler along (max.x, min.y)
    linePositions.push(max.x, min.y, min.z, max.x, min.y, max.z);
    for (let z = min.z; z <= max.z + 0.001; z += stepWorld) {
        linePositions.push(max.x, min.y, z, max.x + tickLen, min.y, z);
    }
    const spriteZ = createTextSprite(`${(size.z * unitScale).toFixed(1)} cm`, '#38bdf8');
    spriteZ.position.set(max.x + tickLen * 2.5, min.y, (min.z + max.z) / 2);
    spriteZ.scale.set(spriteScale, spriteScale * 0.25, 1);
    rulersGroup.add(spriteZ);

    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    const lineMat = new THREE.LineBasicMaterial({color: 0x38bdf8, depthTest: false, transparent: true, opacity: 0.85});
    const rulerLines = new THREE.LineSegments(lineGeom, lineMat);
    rulerLines.renderOrder = 998;
    rulersGroup.add(rulerLines);
}

function clearMeasurement() {
    measurePoints = [];
    while (measureGroup.children.length > 0) {
        const obj = measureGroup.children[0];
        measureGroup.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
            if (obj.material.map) obj.material.map.dispose();
            obj.material.dispose();
        }
    }
    const distEl = document.querySelector('#measure-dist');
    if (distEl) distEl.textContent = '-';
    const statusEl = document.querySelector('#measure-status');
    if (statusEl) {
        statusEl.textContent = measureMode
            ? 'Measure active: click point A on model.'
            : 'Click two points on model to measure distance.';
    }
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
    updateRulers();
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

function handlePointerDown(event) {
    if (measureMode) {
        handleMeasureClick(event);
        return;
    }
    selectVertex(event);
}

function handleMeasureClick(event) {
    const bounds = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    vertexRaycaster.setFromCamera(pointer, camera);
    const hit = vertexRaycaster.intersectObject(mesh, false)[0];
    if (!hit) return;

    const unitScale = Number(document.querySelector('#unit-scale')?.value) || 0.1;
    const clickedPoint = hit.point.clone();

    if (measurePoints.length >= 2) {
        clearMeasurement();
    }

    const box = new THREE.Box3().setFromObject(mesh);
    const size = new THREE.Vector3();
    box.getSize(size);
    const markerRadius = Math.max(Math.max(size.x, size.y, size.z) * 0.015, 0.2);

    const marker = new THREE.Mesh(
        new THREE.SphereGeometry(1, 12, 8),
        new THREE.MeshBasicMaterial({color: 0xf59e0b, depthTest: false})
    );
    marker.renderOrder = 1000;
    marker.scale.setScalar(markerRadius);
    marker.position.copy(clickedPoint);
    measureGroup.add(marker);
    measurePoints.push(clickedPoint);

    const statusEl = document.querySelector('#measure-status');
    const distEl = document.querySelector('#measure-dist');

    if (measurePoints.length === 1) {
        if (statusEl) statusEl.textContent = 'Point A set. Click point B on model.';
    } else if (measurePoints.length === 2) {
        const p1 = measurePoints[0];
        const p2 = measurePoints[1];
        const dist = p1.distanceTo(p2) * unitScale;

        if (distEl) distEl.textContent = dist.toFixed(2);
        if (statusEl) statusEl.textContent = `Measured: ${dist.toFixed(2)} cm. Click again to measure new pair.`;

        const lineGeom = new THREE.BufferGeometry().setFromPoints([p1, p2]);
        const lineMat = new THREE.LineBasicMaterial({color: 0xf59e0b, depthTest: false});
        const line = new THREE.Line(lineGeom, lineMat);
        line.renderOrder = 1000;
        measureGroup.add(line);

        const midPoint = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const sprite = createTextSprite(`${dist.toFixed(2)} cm`, '#f59e0b');
        sprite.position.copy(midPoint);
        const spriteScale = Math.max(Math.max(size.x, size.y, size.z) * 0.2, 1.5);
        sprite.scale.set(spriteScale, spriteScale * 0.25, 1);
        measureGroup.add(sprite);
    }
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
renderer.domElement.addEventListener('pointerdown', handlePointerDown);
vertexGizmo.addEventListener('dragging-changed', (event) => {
    controls.enabled = !event.value;
});
vertexGizmo.addEventListener('objectChange', updateSelectedVertex);
document.querySelectorAll('input').forEach((input) => input.addEventListener('input', applyTransform));
const unitScaleSelect = document.querySelector('#unit-scale');
if (unitScaleSelect) unitScaleSelect.addEventListener('change', updateDimensions);
const toggleRulersCheckbox = document.querySelector('#toggle-rulers');
if (toggleRulersCheckbox) toggleRulersCheckbox.addEventListener('change', updateRulers);

const toggleMeasureButton = document.querySelector('#toggle-measure');
if (toggleMeasureButton) {
    toggleMeasureButton.addEventListener('click', () => {
        measureMode = !measureMode;
        toggleMeasureButton.textContent = measureMode ? 'Exit measure tool' : 'Start measuring';
        toggleMeasureButton.className = measureMode ? '' : 'secondary';
        clearMeasurement();
    });
}

const clearMeasureButton = document.querySelector('#clear-measure');
if (clearMeasureButton) clearMeasureButton.addEventListener('click', clearMeasurement);

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
