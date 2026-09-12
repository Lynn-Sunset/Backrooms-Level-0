import test from 'node:test';
import assert from 'node:assert/strict';
import { pavilionScale, convexFootprint, circleIntersectsCollider, LandingFeedback, renderPixelRatio } from '../gameplay.mjs';

const garden = { roomSize: 9, wallThick: 0.3, playerRad: 0.32 };

test('all pavilion rotations preserve a continuous route between all four doorways', () => {
  // Include the hexagonal platform and protruding staircase, not just a box.
  const footprint = Array.from({ length: 6 }, (_, i) => ({
    x: 3.07 * Math.cos(i * Math.PI / 3), z: 3.07 * Math.sin(i * Math.PI / 3)
  })).concat([{ x: -0.945, z: 3.524 }, { x: 0.945, z: 3.524 }]);
  const sourceRadius = 3.75;
  const scale = pavilionScale(sourceRadius, garden);
  assert.ok(garden.roomSize / 2 - garden.wallThick / 2 - sourceRadius * scale >= 1.29 - 1e-9);
  for (let degree = 0; degree < 360; degree++) {
    const a = degree * Math.PI / 180;
    const shape = convexFootprint(footprint.map(p => ({
      x: scale * (p.x * Math.cos(a) - p.z * Math.sin(a)),
      z: scale * (p.x * Math.sin(a) + p.z * Math.cos(a))
    })));
    const r = 3.88;
    for (let i = 0; i <= 160; i++) {
      const t = -r + i / 160 * r * 2;
      for (const [x, z] of [[t, -r], [t, r], [-r, t], [r, t]]) {
        assert.equal(circleIntersectsCollider(x, z, garden.playerRad, shape), false, `rotation ${degree}, route ${x},${z}`);
      }
    }
    for (const [dx, dz] of [[0, -1], [0, 1], [-1, 0], [1, 0]]) {
      for (let d = r; d <= 5; d += 0.05) {
        assert.equal(circleIntersectsCollider(dx * d, dz * d, garden.playerRad, shape), false);
      }
    }
    assert.equal(circleIntersectsCollider(0, 0, garden.playerRad, shape), true, 'platform remains solid');
  }
});

test('polygon collisions free empty bounding-box corners but stop at edges and steps', () => {
  const shape = convexFootprint([{ x: 0, z: -2 }, { x: 2, z: 0 }, { x: 0, z: 2 }, { x: -2, z: 0 },
    { x: 0, z: 0 }, { x: 0, z: -2 }]);
  assert.equal(circleIntersectsCollider(1.7, 1.7, 0.32, shape), false);
  assert.equal(circleIntersectsCollider(1.05, 1.05, 0.32, shape), true);
  assert.equal(circleIntersectsCollider(2.2, 0, 0.32, shape), true);
  assert.equal(circleIntersectsCollider(2.4, 0, 0.32, shape), false);
  const steps = convexFootprint([{ x: -1, z: -1 }, { x: 1, z: -1 }, { x: 1, z: 1 }, { x: -1, z: 1 },
    { x: -0.5, z: 2 }, { x: 0.5, z: 2 }]);
  assert.equal(circleIntersectsCollider(0, 2.15, 0.32, steps), true);
  assert.equal(circleIntersectsCollider(0.9, 2.2, 0.32, steps), false);
});

test('ordinary wall collisions retain their behavior', () => {
  const wall = { minX: -2, maxX: 2, minZ: -0.15, maxZ: 0.15 };
  assert.equal(circleIntersectsCollider(0, 0, 0.32, wall), true);
  assert.equal(circleIntersectsCollider(0, 0.46, 0.32, wall), true);
  assert.equal(circleIntersectsCollider(0, 0.5, 0.32, wall), false);
  assert.equal(circleIntersectsCollider(2.2, 0.35, 0.32, wall), true);
  assert.equal(circleIntersectsCollider(2.3, 0.45, 0.32, wall), false);
});

test('repeated landings never change look direction or physics position at different frame rates', () => {
  for (const fps of [5, 30, 60, 144]) {
    const feedback = new LandingFeedback();
    // Frozen orientations make accidental writes fail, including at steep pitch.
    const camera = { position: { x: 12, y: 1.7, z: 25 },
      rotation: Object.freeze({ x: 1.2, y: 2.7, z: 0 }),
      quaternion: Object.freeze({ x: 0.3, y: 0.6, z: -0.2, w: 0.7 }) };
    const original = structuredClone(camera);
    for (let jump = 0; jump < 100; jump++) {
      feedback.impact(jump % 2 ? 4.8 : 20);
      for (let frame = 0; frame < fps; frame++) {
        feedback.render(camera, () => {
          assert.ok(camera.position.y >= original.position.y - 0.06 - 1e-9);
          assert.ok(camera.position.y <= original.position.y);
          assert.deepEqual(camera.rotation, original.rotation);
          assert.deepEqual(camera.quaternion, original.quaternion);
        });
        assert.deepEqual(camera, original, 'render must restore the exact physics position');
        feedback.update(1 / fps);
      }
      assert.equal(feedback.offset, 0, 'landing must settle within one second');
    }
  }
});

test('landing restores position even if rendering fails, and resets at a new jump or level', () => {
  const feedback = new LandingFeedback();
  const camera = { position: { y: 1.65 } };
  feedback.impact(5);
  assert.throws(() => feedback.render(camera, () => { throw new Error('context lost'); }), /context lost/);
  assert.equal(camera.position.y, 1.65);
  feedback.reset();
  assert.equal(feedback.offset, 0);
  feedback.impact(1);
  assert.equal(feedback.offset, 0);
});

test('Ultra preserves native display pixels while Auto retains its performance cap', () => {
  for (const dpr of [1, 1.25, 1.5, 2, 2.5, 3]) {
    assert.equal(renderPixelRatio('ultra', dpr), dpr);
    assert.equal(renderPixelRatio('auto', dpr), Math.min(dpr, 1.5));
    assert.equal(renderPixelRatio('high', dpr), Math.min(dpr, 1.5));
  }
});
