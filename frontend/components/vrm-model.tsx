"use client";

import { useEffect, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRM } from "@pixiv/three-vrm";
import * as THREE from "three";
import { VrmBlendShapeController } from "@/utils/vrm-blendshape-controller";
import { VrmAnimationController } from "@/utils/vrm-animation-controller";

interface VrmModelProps {
  url: string;
  onError?: () => void;
  onLoad?: () => void;
}

/**
 * VrmModel Component
 * Loads and renders a VRM 3D character model with animations and facial expressions.
 * Manages character setup, animation mixer, blinking, and body animations.
 */
export function VrmModel({ url, onError, onLoad }: VrmModelProps) {
  const [vrm, setVrm] = useState<VRM | null>(null);
  const [error, setError] = useState(false);
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);
  const blendShapeControllerRef = useRef<VrmBlendShapeController | null>(null);
  const animationControllerRef = useRef<VrmAnimationController | null>(null);

  // Initialize VRM loader and load model
  useEffect(() => {
    const loader = new GLTFLoader();
    loader.register((parser) => new VRMLoaderPlugin(parser));

    loader.load(
      url,
      (gltf) => {
        if (gltf.userData.vrm) {
          const vrmData = gltf.userData.vrm as VRM;
          setVrm(vrmData);
          vrmData.scene.rotation.y = 0;

          // Initialize animation mixer
          const mixer = new THREE.AnimationMixer(vrmData.scene);
          mixerRef.current = mixer;

          // Register and start animations
          if (gltf.animations.length > 0) {
            const animationController = new VrmAnimationController(mixer);
            animationController.registerAnimations(gltf.animations);
            animationControllerRef.current = animationController;
            animationController.transitionToState("idle", 0);
          }

          // Initialize blendshape controller for blinking
          const blendShapeController = new VrmBlendShapeController(vrmData);
          blendShapeControllerRef.current = blendShapeController;

          onLoad?.();
        }
      },
      undefined,
      (err) => {
        setError(true);
        onError?.();
      }
    );

    // Cleanup: dispose resources on unmount
    return () => {
      if (vrm) {
        vrm.scene.traverse((obj) => {
          if (obj instanceof THREE.Mesh) {
            obj.geometry?.dispose();
            if (Array.isArray(obj.material)) {
              obj.material.forEach((m) => m.dispose());
            } else {
              obj.material?.dispose();
            }
          }
        });
      }
      if (mixerRef.current) {
        mixerRef.current.stopAllAction();
      }
    };
  }, [url, onError, onLoad]);

  // Animation frame update: handle all animation and expression updates
  useFrame((state, delta) => {
    if (!vrm) return;

    // STEP 1: Calculate all animation states (blinking, breathing)
    // These mutations are applied to VRM bones and expressions in memory
    blendShapeControllerRef.current?.update(Date.now());
    blendShapeControllerRef.current?.updateBreathing(state.clock.getElapsedTime());

    // STEP 2: Update body animations (skeletal mixer animations)
    // This applies idle, walk, and other animation clip transformations
    if (mixerRef.current) {
      mixerRef.current.update(delta);
    }

    // STEP 3: Propagate all accumulated transformations to the Three.js scene graph
    // This MUST be called LAST so that all mutations (expressions + bone rotations + mixer)
    // are applied to the GPU before rendering. Calling this earlier breaks the update chain.
    vrm.update(delta);
  });

  if (error || !vrm) return null;

  return (
    <primitive
      object={vrm.scene}
      scale={1}
      position={[0, 0, 0]}
    />
  );
}