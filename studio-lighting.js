// High-contrast KeyShot-style Z-up studio light-tent reflections, triplanar UVs,
// and brushed CNC stainless-steel PBR maps for WebGL CAD display meshes.
// The CAD checks themselves use archived B-Rep evidence.
window.HardCadStudio = {
  background: 0x162229,
  _brushedMaps: null,
  _softboxTex: null,

  _createSoftboxTexture() {
    if (this._softboxTex) return this._softboxTex;
    if (typeof document === 'undefined') return null;
    const w = 256, h = 256;
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    if (!ctx) return null;
    // Smooth optical diffuser gradient so flat milled faces reflect liquid-metal sheen
    const grad = ctx.createRadialGradient(w * 0.5, h * 0.5, w * 0.06, w * 0.5, h * 0.5, w * 0.52);
    grad.addColorStop(0.0, 'rgba(255,255,255,1.0)');
    grad.addColorStop(0.45, 'rgba(242,247,252,0.88)');
    grad.addColorStop(0.78, 'rgba(175,192,208,0.38)');
    grad.addColorStop(1.0, 'rgba(18,28,36,0.0)');
    ctx.fillStyle = '#0d151b';
    ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
    const tex = new THREE.CanvasTexture(c);
    this._softboxTex = tex;
    return tex;
  },

  createEnvironment(renderer) {
    const room = new THREE.Scene();
    // Deep studio negative-fill chamber: metal reads as realistic CNC steel only
    // when bright feathered softbox strips contrast sharply against dark studio flags.
    room.background = new THREE.Color(0x0b1218);
    const softTex = this._createSoftboxTexture();

    // Positioned in Z-up CAD coordinates (part top normal = +Z, side bore = -X)
    const panels = [
      // Primary angled overhead studio bank (feathered gradient prevents white clipping on +Z)
      { position: [-9, -8, 15], size: [17, 10], color: 0xfff8f0, soft: true },
      // Sleek cool-daylight grazing rim strip along back-right top edge
      { position: [13, 11, 10], size: [18, 6.5], color: 0xd8ecff, soft: true },
      // Warm champagne accent card catching milled bore chamfers and side walls
      { position: [12, -11, 3], size: [11, 9], color: 0xffe4c8, soft: true },
      // Cool steel-blue left fill reflector sculpting shadow faces
      { position: [-14, 7, 2.5], size: [12, 9], color: 0x79a4c6, soft: true },
      // Subtle low studio bench reflection
      { position: [0, 0, -13], size: [26, 26], color: 0x22303a, soft: false },
      // Explicit black negative-fill flags opposite key lights for crisp dark metallic roll-off
      { position: [6, -13, 8], size: [12, 8], color: 0x05090d, soft: false },
      { position: [-13, -10, -2], size: [12, 8], color: 0x060a0e, soft: false },
    ];

    for (const { position, size, color, soft } of panels) {
      const mat = new THREE.MeshBasicMaterial({
        color,
        map: soft ? softTex : null,
        side: THREE.DoubleSide,
      });
      const light = new THREE.Mesh(new THREE.PlaneGeometry(...size), mat);
      light.position.set(...position);
      light.lookAt(0, 0, 0);
      room.add(light);
    }

    const target = new THREE.WebGLCubeRenderTarget(256, {
      generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter,
    });
    new THREE.CubeCamera(0.1, 60, target).update(renderer, room);

    for (const panel of room.children) {
      panel.geometry.dispose();
      panel.material.dispose();
    }

    if (!THREE.PMREMGenerator) return target.texture;
    const generator = new THREE.PMREMGenerator(renderer);
    const environment = generator.fromCubemap(target.texture);
    generator.dispose();
    target.dispose();
    return environment.texture;
  },

  // STLLoader geometries ship without UV coordinates; generate clean triplanar box UVs
  // so brushed CNC steel roughness/bump maps visibly render on every milled face.
  computeBoxUVs(geometry, tileSize) {
    const pos = geometry.attributes.position;
    if (!pos) return geometry;
    if (!geometry.attributes.normal) geometry.computeVertexNormals();
    const norm = geometry.attributes.normal;
    if (!geometry.boundingBox) geometry.computeBoundingBox();
    const size = geometry.boundingBox.getSize(new THREE.Vector3());
    const scale = tileSize || Math.max(size.x, size.y, size.z, 1) * 0.65;
    const uvs = new Float32Array(pos.count * 2);

    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
      const ax = Math.abs(norm.getX(i));
      const ay = Math.abs(norm.getY(i));
      const az = Math.abs(norm.getZ(i));
      let u, v;
      if (az >= ax && az >= ay) {
        u = x / scale; v = y / scale;
      } else if (ax >= ay && ax >= az) {
        u = y / scale; v = z / scale;
      } else {
        u = x / scale; v = z / scale;
      }
      uvs[i * 2] = u;
      uvs[i * 2 + 1] = v;
    }
    geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
    return geometry;
  },

  createBrushedMetalMaps() {
    if (this._brushedMaps) return this._brushedMaps;
    if (typeof document === 'undefined') return null;

    const size = 512;
    const bumpCanvas = document.createElement('canvas');
    bumpCanvas.width = size; bumpCanvas.height = size;
    const bCtx = bumpCanvas.getContext('2d');

    const roughCanvas = document.createElement('canvas');
    roughCanvas.width = size; roughCanvas.height = size;
    const rCtx = roughCanvas.getContext('2d');
    if (!bCtx || !rCtx) return null;

    bCtx.fillStyle = '#808080';
    bCtx.fillRect(0, 0, size, size);
    rCtx.fillStyle = '#5a5a5a'; // base ~0.35 roughness
    rCtx.fillRect(0, 0, size, size);

    // Deterministic CNC directional brushed streaks + subtle fly-cutter variation
    let seed = 4219;
    const rand = () => {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };

    for (let y = 0; y < size; y++) {
      const bv = Math.floor(114 + rand() * 28);
      bCtx.fillStyle = `rgb(${bv},${bv},${bv})`;
      bCtx.fillRect(0, y, size, 1);

      const rv = Math.floor(68 + rand() * 44);
      rCtx.fillStyle = `rgb(${rv},${rv},${rv})`;
      rCtx.fillRect(0, y, size, 1);
    }

    for (let i = 0; i < 900; i++) {
      const y = Math.floor(rand() * size);
      const x = Math.floor(rand() * size);
      const len = 40 + Math.floor(rand() * 220);
      const bv = Math.floor(96 + rand() * 64);
      bCtx.fillStyle = `rgba(${bv},${bv},${bv},0.34)`;
      bCtx.fillRect(x, y, len, 1);
      if (x + len > size) bCtx.fillRect(0, y, x + len - size, 1);

      const rv = Math.floor(54 + rand() * 68);
      rCtx.fillStyle = `rgba(${rv},${rv},${rv},0.32)`;
      rCtx.fillRect(x, y, len, 1);
      if (x + len > size) rCtx.fillRect(0, y, x + len - size, 1);
    }

    const bumpMap = new THREE.CanvasTexture(bumpCanvas);
    bumpMap.wrapS = bumpMap.wrapT = THREE.RepeatWrapping;
    bumpMap.repeat.set(2.5, 2.5);

    const roughnessMap = new THREE.CanvasTexture(roughCanvas);
    roughnessMap.wrapS = roughnessMap.wrapT = THREE.RepeatWrapping;
    roughnessMap.repeat.set(2.5, 2.5);

    this._brushedMaps = { bumpMap, roughnessMap };
    return this._brushedMaps;
  },

  createSteelMaterial(opts) {
    const maps = this.createBrushedMetalMaps();
    const MatCtor = THREE.MeshPhysicalMaterial || THREE.MeshStandardMaterial;
    const cfg = {
      color: opts.color ?? 0x9aa9b6,
      metalness: opts.metalness ?? 0.90,
      roughness: opts.roughness ?? 0.85, // multiplied by roughnessMap (~0.24..0.44 effective)
      envMap: opts.envMap || null,
      envMapIntensity: opts.envMapIntensity ?? 1.55,
      bumpMap: maps ? maps.bumpMap : null,
      bumpScale: opts.bumpScale ?? 0.04,
      roughnessMap: maps ? maps.roughnessMap : null,
      wireframe: !!opts.wireframe,
      transparent: !!opts.transparent,
      opacity: opts.opacity ?? 1,
      depthWrite: opts.depthWrite ?? !opts.transparent,
      side: opts.side ?? THREE.FrontSide,
    };
    if (opts.clippingPlanes) cfg.clippingPlanes = opts.clippingPlanes;
    if (MatCtor === THREE.MeshPhysicalMaterial) {
      cfg.clearcoat = opts.clearcoat ?? 0.22;
      cfg.clearcoatRoughness = opts.clearcoatRoughness ?? 0.24;
    }
    return new MatCtor(cfg);
  },
};
