// Reflection cards for the display meshes. The CAD checks use archived evidence.
window.HardCadStudio = {
  background: 0xe2e5e7,

  createEnvironment(renderer) {
    const room = new THREE.Scene();
    room.background = new THREE.Color(0x9fa4a9);
    const panels = [
      { position: [0, 8, 3], size: [10, 4], color: 0xffffff },
      { position: [-9, -3, 4], size: [7, 5], color: 0xf4f7fb },
      { position: [9, -1, 6], size: [5, 7], color: 0xe6e7e9 },
      { position: [0, -9, 2], size: [12, 3], color: 0xc2cbd2 },
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
    const target = new THREE.WebGLCubeRenderTarget(128, {
      generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter,
    });
    new THREE.CubeCamera(0.1, 50, target).update(renderer, room);
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
};
