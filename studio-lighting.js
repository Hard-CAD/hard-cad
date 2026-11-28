// Studio light-tent reflections and procedural machined-metal maps for CAD display meshes.
// The CAD checks themselves use archived B-Rep evidence.
window.HardCadStudio = {
  background: 0xdde2e6,
  _brushedMaps: null,

  createEnvironment(renderer) {
    const room = new THREE.Scene();
    // High-contrast studio light tent: dark negative-fill walls + bright softbox strips
    // give machined metallic surfaces crisp specular roll-off instead of flat gray clay.
    room.background = new THREE.Color(0x1e2730);

    const panels = [
      // Primary overhead softbox (cool daylight)
      { position: [0, 12, 5], size: [18, 7], color: 0xffffff },
      // Broad upper-left key strip (slightly warm studio tungsten)
      { position: [-11, 5, 8], size: [8, 12], color: 0xfff6eb },
      // Right-hand cool fill reflector card
      { position: [12, -2, 6], size: [7, 11], color: 0xdbe9f6 },
      // High rim accent behind part to catch bevels and bore lips
      { position: [4, -12, 9], size: [14, 4.5], color: 0xeef5fc },
      // Lower studio bounce card (soft mid-gray floor reflection)
      { position: [0, 0, -11], size: [22, 22], color: 0x525d66 },
      // Dark negative-fill baffles on opposing mid-walls to sharpen metallic contrast
      { position: [-11, -9, -1], size: [10, 7], color: 0x10161c },
      { position: [11, 9, -1], size: [10, 7], color: 0x141b22 },
    ];

    for (const { position, size, color } of panels) {
      const light = new THREE.Mesh(
        new THREE.PlaneGeometry(...size),
        new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide }),
      );
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

  createBrushedMetalMaps() {
    if (this._brushedMaps) return this._brushedMaps;
    if (typeof document === 'undefined') return null;

    const size = 256;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, size, size);

    // Deterministic pseudo-random fine machined streaks
    let seed = 1337;
    const rand = () => {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };

    for (let y = 0; y < size; y++) {
      const band = Math.floor(116 + rand() * 26);
      ctx.fillStyle = `rgb(${band},${band},${band})`;
      ctx.fillRect(0, y, size, 1);
    }
    for (let i = 0; i < 420; i++) {
      const y = Math.floor(rand() * size);
      const x = Math.floor(rand() * size);
      const len = 30 + Math.floor(rand() * 140);
      const v = Math.floor(102 + rand() * 52);
      ctx.fillStyle = `rgba(${v},${v},${v},0.35)`;
      ctx.fillRect(x, y, len, 1);
      if (x + len > size) ctx.fillRect(0, y, x + len - size, 1);
    }

    const bumpMap = new THREE.CanvasTexture(canvas);
    bumpMap.wrapS = THREE.RepeatWrapping;
    bumpMap.wrapT = THREE.RepeatWrapping;
    bumpMap.repeat.set(3, 3);

    this._brushedMaps = { bumpMap };
    return this._brushedMaps;
  },
};
