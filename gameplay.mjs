// Shared gameplay math; kept independent of the renderer for regression checks.
export function pavilionScale(horizontalRadius, { roomSize, wallThick, playerRad }) {
  // Keep a full player width plus 65 cm of passing space inside every wall.
  // A radius bound stays valid for every rotation, including the stairs.
  const passageWidth = playerRad * 2 + 0.65;
  const availableRadius = roomSize / 2 - wallThick / 2 - passageWidth;
  return Math.max(0, Math.min(1, 3.2 / horizontalRadius, availableRadius / horizontalRadius));
}

export function convexFootprint(points) {
  const sorted = points.slice().sort((a, b) => a.x - b.x || a.z - b.z)
    .filter((p, i, all) => i === 0 || p.x !== all[i - 1].x || p.z !== all[i - 1].z);
  if (sorted.length < 3) return null;
  const cross = (a, b, c) => (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
  const lower = [], upper = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower.at(-2), lower.at(-1), p) <= 0) lower.pop();
    lower.push(p);
  }
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper.at(-2), upper.at(-1), p) <= 0) upper.pop();
    upper.push(p);
  }
  const polygon = lower.slice(0, -1).concat(upper.slice(0, -1));
  if (polygon.length < 3) return null;
  return {
    polygon,
    minX: sorted[0].x, maxX: sorted.at(-1).x,
    minZ: Math.min(...polygon.map(p => p.z)), maxZ: Math.max(...polygon.map(p => p.z))
  };
}

export function circleIntersectsCollider(px, pz, radius, collider) {
  const cx = Math.max(collider.minX, Math.min(px, collider.maxX));
  const cz = Math.max(collider.minZ, Math.min(pz, collider.maxZ));
  if ((px - cx) ** 2 + (pz - cz) ** 2 >= radius ** 2) return false;
  if (!collider.polygon) return true;

  // The broad phase still uses the AABB; the narrow phase follows the platform.
  const points = collider.polygon;
  let inside = false;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    const a = points[j], b = points[i];
    if ((a.z > pz) !== (b.z > pz) && px < (b.x - a.x) * (pz - a.z) / (b.z - a.z) + a.x) {
      inside = !inside;
    }
    const dx = b.x - a.x, dz = b.z - a.z;
    const lengthSq = dx * dx + dz * dz;
    const t = lengthSq ? Math.max(0, Math.min(1, ((px - a.x) * dx + (pz - a.z) * dz) / lengthSq)) : 0;
    if ((px - a.x - t * dx) ** 2 + (pz - a.z - t * dz) ** 2 < radius ** 2) return true;
  }
  return inside;
}

export class LandingFeedback {
  offset = 0;

  impact(speed) {
    this.offset = speed > 2.5 ? -Math.min(0.06, speed * 0.012) : 0;
  }

  update(dt) {
    this.offset *= Math.exp(-14 * dt);
    if (Math.abs(this.offset) < 0.0001) this.offset = 0;
  }

  reset() { this.offset = 0; }

  render(camera, renderFrame) {
    // A brief vertical dip only affects this frame. Never alter the look
    // rotation or feed the visual offset back into jump/collision physics.
    const y = camera.position.y;
    camera.position.y = y + this.offset;
    try { renderFrame(); }
    finally { camera.position.y = y; }
  }
}

export function renderPixelRatio(quality, devicePixelRatio = 1) {
  const native = Math.max(0.8, devicePixelRatio || 1);
  return quality === 'ultra' ? native : Math.min(native, 1.5);
}
