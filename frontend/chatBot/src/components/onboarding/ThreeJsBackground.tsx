'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeJsBackgroundProps {
  darkMode: boolean;
}

export default function ThreeJsBackground({ darkMode }: ThreeJsBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      alpha: true,
      antialias: true,
    });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    camera.position.z = 15;

    // DNA Helix
    // const helixParticles: THREE.Points[] = [];
    // for (let strand = 0; strand < 2; strand++) {
    //   const particleCount = 200;
    //   const geometry = new THREE.BufferGeometry();
    //   const positions = new Float32Array(particleCount * 3);
      
    //   for (let i = 0; i < particleCount; i++) {
    //     const angle = (i / particleCount) * Math.PI * 8 + strand * Math.PI;
    //     const radius = 4;
    //     positions[i * 3] = Math.cos(angle) * radius;
    //     positions[i * 3 + 1] = (i / particleCount) * 30 - 15;
    //     positions[i * 3 + 2] = Math.sin(angle) * radius;
    //   }
      
    //   geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      
    //   const material = new THREE.PointsMaterial({
    //     color: strand === 0 ? (darkMode ? 0x60a5fa : 0x6366f1) : (darkMode ? 0x8b5cf6 : 0x06b6d4),
    //     size: 0.2,
    //     transparent: true,
    //     opacity: 0.8,
    //     blending: THREE.AdditiveBlending,
    //   });
      
    //   const points = new THREE.Points(geometry, material);
    //   helixParticles.push(points);
    //   scene.add(points);
    // }

    // Central Sphere
    // const sphereGeometry = new THREE.IcosahedronGeometry(4, 4);
    // const vertexCount = sphereGeometry.attributes.position.count;
    // const displacement = new Float32Array(vertexCount);
    // for (let i = 0; i < vertexCount; i++) {
    //   displacement[i] = Math.random() * 0.5;
    // }
    // sphereGeometry.setAttribute('displacement', new THREE.BufferAttribute(displacement, 1));

    // const sphereMaterial = new THREE.ShaderMaterial({
    //   uniforms: {
    //     time: { value: 0 },
    //     colorA: { value: new THREE.Color(darkMode ? 0x6366f1 : 0x6366f1) },
    //     colorB: { value: new THREE.Color(darkMode ? 0x8b5cf6 : 0x06b6d4) },
    //   },
    //   vertexShader: `
    //     uniform float time;
    //     attribute float displacement;
    //     varying vec3 vNormal;
    //     varying vec3 vPosition;
        
    //     void main() {
    //       vNormal = normal;
    //       vPosition = position;
    //       vec3 newPosition = position + normal * (displacement * sin(time + position.y * 2.0) * 0.3);
    //       gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    //     }
    //   `,
    //   fragmentShader: `
    //     uniform vec3 colorA;
    //     uniform vec3 colorB;
    //     varying vec3 vNormal;
    //     varying vec3 vPosition;
        
    //     void main() {
    //       float mixValue = (vPosition.y + 4.0) / 8.0;
    //       vec3 color = mix(colorA, colorB, mixValue);
    //       float alpha = 0.6 + abs(vNormal.z) * 0.4;
    //       gl_FragColor = vec4(color, alpha);
    //     }
    //   `,
    //   transparent: true,
    //   wireframe: false,
    //   side: THREE.DoubleSide,
    // });

    // const centralSphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    // scene.add(centralSphere);

    // Star Constellation
    const constellationGeometry = new THREE.BufferGeometry();
    const constellationPositions = new Float32Array(2000 * 3);
    const constellationSizes = new Float32Array(2000);

    for (let i = 0; i < 2000; i++) {
      constellationPositions[i * 3] = (Math.random() - 0.5) * 50;
      constellationPositions[i * 3 + 1] = (Math.random() - 0.5) * 50;
      constellationPositions[i * 3 + 2] = (Math.random() - 0.5) * 35;
      constellationSizes[i] = Math.random() * 0.08 + 0.03;
    }

    constellationGeometry.setAttribute('position', new THREE.BufferAttribute(constellationPositions, 3));
    constellationGeometry.setAttribute('size', new THREE.BufferAttribute(constellationSizes, 1));

    const constellationMaterial = new THREE.PointsMaterial({
      color: darkMode ? 0x60a5fa : 0x6366f1,
      size: 0.08,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
    
    const constellation = new THREE.Points(constellationGeometry, constellationMaterial);
    scene.add(constellation);

    // Energy Beams
    const beams: THREE.Line[] = [];
    for (let i = 0; i < 15; i++) {
      const beamGeometry = new THREE.BufferGeometry();
      const beamPositions = new Float32Array(6);
      beamGeometry.setAttribute('position', new THREE.BufferAttribute(beamPositions, 3));
      
      const beamMaterial = new THREE.LineBasicMaterial({
        color: darkMode ? 0x60a5fa : 0x06b6d4,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending,
        linewidth: 2,
      });
      
      const beam = new THREE.Line(beamGeometry, beamMaterial);
      beams.push(beam);
      scene.add(beam);
    }

    // Rings
    // const rings: THREE.Mesh[] = [];
    // for (let i = 0; i < 8; i++) {
    //   const ringGeometry = new THREE.TorusGeometry(5 + i * 1.2, 0.1, 16, 100);
    //   const ringMaterial = new THREE.MeshPhysicalMaterial({
    //     color: i % 2 === 0 ? (darkMode ? 0x6366f1 : 0x6366f1) : (darkMode ? 0x8b5cf6 : 0x06b6d4),
    //     emissive: i % 2 === 0 ? (darkMode ? 0x4338ca : 0x4f46e5) : (darkMode ? 0x6366f1 : 0x0891b2),
    //     emissiveIntensity: 0.5,
    //     transparent: true,
    //     opacity: 0.15,
    //     metalness: 0.9,
    //     roughness: 0.1,
    //   });
    //   const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    //   ring.rotation.x = Math.PI / 3 + i * 0.15;
    //   ring.rotation.y = i * 0.2;
    //   rings.push(ring);
    //   scene.add(ring);
    // }

    // Lighting
    const spotLight1 = new THREE.SpotLight(darkMode ? 0x6366f1 : 0x6366f1, 3, 50, Math.PI / 8, 0.5, 1);
    spotLight1.position.set(10, 10, 10);
    scene.add(spotLight1);

    const spotLight2 = new THREE.SpotLight(darkMode ? 0x8b5cf6 : 0x06b6d4, 3, 50, Math.PI / 8, 0.5, 1);
    spotLight2.position.set(-10, -10, 10);
    scene.add(spotLight2);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
    scene.add(ambientLight);

    // Animation
    let time = 0;

    const animate = () => {
      requestAnimationFrame(animate);
      time += 0.01;

      // sphereMaterial.uniforms.time.value = time;
      // centralSphere.rotation.x = Math.sin(time * 0.3) * 0.2;
      // centralSphere.rotation.y = time * 0.2;
      // centralSphere.rotation.z = Math.cos(time * 0.2) * 0.2;
      // centralSphere.scale.setScalar(1 + Math.sin(time * 0.4) * 0.15);

      // helixParticles.forEach((helix, index) => {
      //   helix.rotation.y = time * 0.1 * (index === 0 ? 1 : -1);
      //   helix.position.y = Math.sin(time * 0.5) * 2;
      // });

      const constellationPos = constellation.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < constellationPos.length; i += 3) {
        constellationPos[i + 1] += Math.sin(time + i) * 0.01;
      }
      constellation.geometry.attributes.position.needsUpdate = true;
      constellation.rotation.y = time * 0.05;

      // beams.forEach((beam, index) => {
      //   const positions = beam.geometry.attributes.position.array as Float32Array;
      //   const angle = time * 0.5 + index * (Math.PI * 2 / beams.length);
      //   const radius = 10;
      //   const speed = (time * 2 + index) % 4;
        
      //   positions[0] = Math.cos(angle) * radius;
      //   positions[1] = Math.sin(angle) * radius;
      //   positions[2] = -10 + speed * 5;
      //   positions[3] = Math.cos(angle + 0.5) * radius * 1.5;
      //   positions[4] = Math.sin(angle + 0.5) * radius * 1.5;
      //   positions[5] = -10 + speed * 5 + 2;
        
      //   beam.geometry.attributes.position.needsUpdate = true;
      //   (beam.material as THREE.LineBasicMaterial).opacity = 0.6 - (speed / 4) * 0.5;
      // });

      // rings.forEach((ring, i) => {
      //   ring.rotation.y = time * (0.05 + i * 0.02);
      //   ring.rotation.z = Math.sin(time * 0.3 + i) * 0.3;
      //   ring.position.y = Math.sin(time * 0.4 + i * 0.5) * 2;
      //   ring.scale.setScalar(1 + Math.sin(time * 0.3 + i) * 0.05);
      // });

      // spotLight1.position.x = Math.cos(time * 0.7) * 15;
      // spotLight1.position.z = Math.sin(time * 0.7) * 15;
      // spotLight1.intensity = 3 + Math.sin(time * 2) * 1;

      // spotLight2.position.x = Math.cos(time * 0.7 + Math.PI) * 15;
      // spotLight2.position.z = Math.sin(time * 0.7 + Math.PI) * 15;
      // spotLight2.intensity = 3 + Math.cos(time * 2) * 1;

      // camera.position.x = Math.sin(time * 0.2) * 2;
      // camera.position.y = Math.cos(time * 0.15) * 1.5;
      // camera.position.z = 15 + Math.sin(time * 0.1) * 2;
      // camera.lookAt(scene.position);

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [darkMode]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed top-0 left-0 w-full h-full pointer-events-none z-0"
      style={{ opacity: darkMode ? 0.5 : 0.35 }}
    />
  );
}
